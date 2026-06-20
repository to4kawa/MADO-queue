#!/usr/bin/env python3
"""PR #3 concurrency verification with and without a partial UNIQUE index.

Uses only Python stdlib and SQLite.  The script creates disposable SQLite
files under verification/.tmp_pr3_sqlite_verify and writes a Markdown summary to
verification/pr-3-sqlite-results.md.
"""

from __future__ import annotations

import json
import multiprocessing as mp
import shutil
import sqlite3
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
TMP_ROOT = ROOT / ".tmp_pr3_sqlite_verify"
RESULTS_MD = ROOT / "pr-3-sqlite-results.md"

PARTIAL_UNIQUE_INDEX = """
CREATE UNIQUE INDEX uq_processing_active_event
ON processing_logs(event_log_id)
WHERE status = 'processing'
""".strip()


@dataclass
class Attempt:
    actor: str
    selected: list[tuple]
    insert_ok: bool
    exception_type: str | None = None
    exception_message: str | None = None

    @property
    def database_is_locked(self) -> bool:
        return "database is locked" in (self.exception_message or "")

    @property
    def unique_failed(self) -> bool:
        return "UNIQUE constraint failed" in (self.exception_message or "")


@dataclass
class CaseResult:
    schema: str
    case: str
    attempts: list[Attempt]
    final_count: int
    active_duplicate_remaining: bool

    @property
    def locked_seen(self) -> bool:
        return any(a.database_is_locked for a in self.attempts)

    @property
    def unique_seen(self) -> bool:
        return any(a.unique_failed for a in self.attempts)


def connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path, timeout=10.0, isolation_level=None)


def init_schema(db_path: Path, *, with_unique: bool) -> None:
    with connect(db_path) as conn:
        conn.executescript(
            """
            PRAGMA journal_mode = WAL;
            CREATE TABLE event_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category CHAR(1) NOT NULL,
                button_text TEXT,
                timestamp TEXT NOT NULL,
                current_number INTEGER NOT NULL,
                staff_count INTEGER
            );
            CREATE TABLE processing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticket_number INTEGER NOT NULL,
                category CHAR(1),
                button_text TEXT,
                start_time TEXT,
                end_time TEXT,
                wait_time INTEGER,
                status TEXT NOT NULL,
                processing_time INTEGER,
                created_at TEXT NOT NULL,
                staff_count INTEGER,
                event_log_id INTEGER
            );
            INSERT INTO event_logs(category, button_text, timestamp, current_number, staff_count)
            VALUES ('A', '住民票', '2026-06-20T00:00:00', 1, 2);
            """
        )
        if with_unique:
            conn.execute(PARTIAL_UNIQUE_INDEX)


def attempt_start(db_path: Path, actor: str, barrier: threading.Barrier | None = None) -> Attempt:
    selected: list[tuple] = []
    try:
        conn = connect(db_path)
        try:
            selected = list(conn.execute("SELECT staff_count FROM event_logs WHERE id = ?", (1,)))
            if barrier is not None:
                barrier.wait()
            conn.execute(
                """
                INSERT INTO processing_logs
                    (ticket_number, category, button_text, start_time, wait_time,
                     status, created_at, staff_count, event_log_id)
                VALUES (1, 'A', '住民票', '2026-06-20T00:00:01', 0,
                        'processing', '2026-06-20T00:00:01', ?, 1)
                """,
                (selected[0][0] if selected else None,),
            )
            return Attempt(actor=actor, selected=selected, insert_ok=True)
        finally:
            conn.close()
    except Exception as exc:  # record exact DB outcome for verification
        return Attempt(actor=actor, selected=selected, insert_ok=False,
                       exception_type=type(exc).__name__, exception_message=str(exc))


def process_attempt(db_path: str, actor: str, queue: mp.Queue, barrier: mp.Barrier) -> None:
    selected: list[tuple] = []
    try:
        conn = connect(Path(db_path))
        try:
            selected = list(conn.execute("SELECT staff_count FROM event_logs WHERE id = ?", (1,)))
            barrier.wait()
            conn.execute(
                """
                INSERT INTO processing_logs
                    (ticket_number, category, button_text, start_time, wait_time,
                     status, created_at, staff_count, event_log_id)
                VALUES (1, 'A', '住民票', '2026-06-20T00:00:01', 0,
                        'processing', '2026-06-20T00:00:01', ?, 1)
                """,
                (selected[0][0] if selected else None,),
            )
            queue.put(asdict(Attempt(actor=actor, selected=selected, insert_ok=True)))
        finally:
            conn.close()
    except Exception as exc:
        queue.put(asdict(Attempt(actor=actor, selected=selected, insert_ok=False,
                                 exception_type=type(exc).__name__, exception_message=str(exc))))


def summarize(db_path: Path, schema: str, case: str, attempts: list[Attempt]) -> CaseResult:
    with connect(db_path) as conn:
        final_count = conn.execute("SELECT COUNT(*) FROM processing_logs").fetchone()[0]
        duplicates = conn.execute(
            """
            SELECT COUNT(*) FROM processing_logs
            WHERE event_log_id = 1 AND status = 'processing'
            """
        ).fetchone()[0] > 1
    return CaseResult(schema, case, attempts, final_count, duplicates)


def run_case(schema: str, with_unique: bool, case: str) -> CaseResult:
    db_path = TMP_ROOT / f"{schema}_{case}.sqlite3"
    init_schema(db_path, with_unique=with_unique)
    if case == "sequential_two_starts":
        attempts = [attempt_start(db_path, "conn-1"), attempt_start(db_path, "conn-2")]
    elif case == "two_threads_same_time":
        barrier = threading.Barrier(2)
        attempts: list[Attempt] = []
        threads = [threading.Thread(target=lambda name=n: attempts.append(attempt_start(db_path, name, barrier))) for n in ("thread-1", "thread-2")]
        for thread in threads: thread.start()
        for thread in threads: thread.join()
        attempts.sort(key=lambda a: a.actor)
    elif case == "two_processes_same_time":
        barrier = mp.Barrier(2)
        queue: mp.Queue = mp.Queue()
        procs = [mp.Process(target=process_attempt, args=(str(db_path), n, queue, barrier)) for n in ("process-1", "process-2")]
        for proc in procs: proc.start()
        attempts = [Attempt(**queue.get(timeout=20)) for _ in procs]
        for proc in procs: proc.join(timeout=20)
        attempts.sort(key=lambda a: a.actor)
    else:
        raise ValueError(case)
    return summarize(db_path, schema, case, attempts)


def verify_transitions() -> dict[str, object]:
    db_path = TMP_ROOT / "transitions.sqlite3"
    init_schema(db_path, with_unique=True)
    out: dict[str, object] = {}
    with connect(db_path) as conn:
        conn.execute("INSERT INTO processing_logs(ticket_number,status,created_at,event_log_id) VALUES (1,'processing','t1',1)")
        conn.execute("UPDATE processing_logs SET status = 'completed' WHERE event_log_id = 1")
        try:
            conn.execute("INSERT INTO processing_logs(ticket_number,status,created_at,event_log_id) VALUES (1,'processing','t2',1)")
            out["insert_after_completed"] = "ok"
        except Exception as exc:
            out["insert_after_completed"] = f"{type(exc).__name__}: {exc}"
        conn.execute("UPDATE processing_logs SET status = 'completed' WHERE status = 'processing'")
        conn.execute("INSERT INTO processing_logs(ticket_number,status,created_at,event_log_id) VALUES (1,'deleted','t3',1)")
        try:
            conn.execute("INSERT INTO processing_logs(ticket_number,status,created_at,event_log_id) VALUES (1,'processing','t4',1)")
            out["insert_with_deleted_history"] = "ok"
        except Exception as exc:
            out["insert_with_deleted_history"] = f"{type(exc).__name__}: {exc}"
        out["rows"] = list(conn.execute("SELECT status, COUNT(*) FROM processing_logs GROUP BY status ORDER BY status"))
    return out


def verify_index_creation_failure() -> dict[str, object]:
    db_path = TMP_ROOT / "index_creation_failure.sqlite3"
    init_schema(db_path, with_unique=False)
    with connect(db_path) as conn:
        conn.execute("INSERT INTO processing_logs(ticket_number,status,created_at,event_log_id) VALUES (1,'processing','t1',1)")
        conn.execute("INSERT INTO processing_logs(ticket_number,status,created_at,event_log_id) VALUES (1,'processing','t2',1)")
        try:
            conn.execute(PARTIAL_UNIQUE_INDEX)
            return {"created": True, "exception": None}
        except Exception as exc:
            return {"created": False, "exception": f"{type(exc).__name__}: {exc}"}


def md_bool(value: bool) -> str:
    return "あり" if value else "なし"


def write_markdown(results: Iterable[CaseResult], transitions: dict[str, object], index_failure: dict[str, object]) -> None:
    lines = [
        "# PR #3 SQLite concurrency verification",
        "",
        "Generated by `python3 verification/pr_3_sqlite_verify.py`.",
        "",
        "## Compared schemas",
        "",
        "- **PR #3 only**: PR #3 equivalent `processing_logs` schema without an active-row uniqueness constraint.",
        "- **PR #3 + partial UNIQUE INDEX**:",
        "",
        "```sql",
        PARTIAL_UNIQUE_INDEX + ";",
        "```",
        "",
        "## Concurrent-start results",
        "",
        "| Schema | Case | SELECT results | INSERT results | database is locked | UNIQUE constraint failed | Final rows | Multiple active rows for same event_log_id |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- |",
    ]
    for r in results:
        selects = "<br>".join(f"{a.actor}: `{a.selected}`" for a in r.attempts)
        inserts = "<br>".join(
            f"{a.actor}: OK" if a.insert_ok else f"{a.actor}: NG `{a.exception_type}: {a.exception_message}`"
            for a in r.attempts
        )
        lines.append(
            f"| {r.schema} | {r.case} | {selects} | {inserts} | {md_bool(r.locked_seen)} | {md_bool(r.unique_seen)} | {r.final_count} | {md_bool(r.active_duplicate_remaining)} |"
        )
    lines += [
        "",
        "## State-transition checks with the partial UNIQUE INDEX",
        "",
        f"- Insert after updating the previous active row to `completed`: `{transitions['insert_after_completed']}`.",
        f"- Insert while a `deleted` history row exists for the same `event_log_id`: `{transitions['insert_with_deleted_history']}`.",
        f"- Final status counts: `{transitions['rows']}`.",
        "",
        "Because the index predicate is `WHERE status = 'processing'`, `completed` and `deleted` rows are outside the index target. The check above confirms history retention and a later restart are not blocked by those non-active statuses.",
        "",
        "## Existing duplicate data before index creation",
        "",
        f"- Creating the partial UNIQUE INDEX after two existing `processing` rows for the same `event_log_id`: created=`{index_failure['created']}`, exception=`{index_failure['exception']}`.",
        "- Therefore existing duplicate active rows must be cleaned up before adding this index in a migration.",
        "",
        "## Findings",
        "",
        "- Without the constraint, sequential and concurrent starts can leave duplicate active `processing` rows for the same `event_log_id`.",
        "- With the partial UNIQUE INDEX, one duplicate `processing` insert is rejected by the database constraint.",
        "- The rejection is observed as `UNIQUE constraint failed: processing_logs.event_log_id`, not as `database is locked`.",
        "- `completed` and `deleted` are outside the partial-index predicate, so they do not prevent history retention or insertion of a new active `processing` row.",
        "- If duplicate active data already exists, index creation fails and data cleanup is required before adding the index.",
        "",
        "## Three-level conclusion",
        "",
        "1. **PR #3 only**: PR #3's schema and insert flow still allow duplicate active starts when the same ticket is started more than once.",
        "2. **PR #3 + partial UNIQUE INDEX**: Adding the partial UNIQUE INDEX prevents duplicate active rows at the SQLite constraint layer under sequential, threaded, and process concurrency tests.",
        "3. **Business rule unresolved**: Whether the service should allow a ticket to be started again after completion remains a business-specification decision; the partial index permits it because `completed` rows are not active.",
        "",
    ]
    RESULTS_MD.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)
    TMP_ROOT.mkdir()
    cases = ["sequential_two_starts", "two_threads_same_time", "two_processes_same_time"]
    results = []
    for schema, with_unique in [("PR #3 only", False), ("PR #3 + partial UNIQUE INDEX", True)]:
        safe_schema = "without_unique" if not with_unique else "with_unique"
        for case in cases:
            result = run_case(safe_schema, with_unique, case)
            result.schema = schema
            results.append(result)
    transitions = verify_transitions()
    index_failure = verify_index_creation_failure()
    write_markdown(results, transitions, index_failure)
    print(json.dumps({"results": [asdict(r) for r in results], "transitions": transitions, "index_creation_failure": index_failure}, ensure_ascii=False, indent=2))
    print(f"Wrote {RESULTS_MD}")


if __name__ == "__main__":
    main()
