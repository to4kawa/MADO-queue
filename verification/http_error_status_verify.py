"""Verify API HTTP status behavior when internal DB errors occur.

This script is intentionally read-only for production code. It uses Flask's test
client, a temporary SQLite database, and monkeypatches app.get_db / print_ticket
at runtime to inject reachable DB failures without Docker, printers, or the
production DB.
"""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
import importlib
import importlib.metadata
import json
import os
import platform
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "verification" / "http-error-status-results.md"
MAIN_SHA = "fb7198230f2a10cf28c43fba45b79147dd7ec74e"


@dataclass
class Case:
    route: str
    method: str
    payload: dict[str, Any] | None
    exception_label: str
    injection: str
    normal_setup: Callable[[Any], None] | None = None


class ExecuteFailCursor:
    def execute(self, *args: Any, **kwargs: Any) -> None:
        raise sqlite3.OperationalError("injected SQL execution failure")

    def fetchone(self) -> Any:
        return None

    def fetchall(self) -> list[Any]:
        return []

    @property
    def rowcount(self) -> int:
        return 0


class ExecuteFailConnection:
    def cursor(self) -> ExecuteFailCursor:
        return ExecuteFailCursor()

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def close(self) -> None:
        pass


@contextmanager
def connect_failure_db():
    raise sqlite3.OperationalError("injected DB connection failure")
    yield  # pragma: no cover


@contextmanager
def execute_failure_db():
    yield ExecuteFailConnection()


@contextmanager
def commit_failure_db():
    conn = sqlite3.connect(os.environ["DB_PATH"])
    try:
        yield conn
        raise sqlite3.OperationalError("injected commit failure")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def command_output(args: list[str]) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()


def init_temp_db() -> str:
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    fd, path = tempfile.mkstemp(prefix="mado-http-status-", suffix=".db")
    os.close(fd)
    os.environ["DB_PATH"] = path
    runpy.run_path(str(ROOT / "init_db.py"))
    return path


def seed_processing(app_module: Any, ticket_number: int = 1, category: str = "A") -> None:
    now = datetime.now().isoformat()
    with sqlite3.connect(os.environ["DB_PATH"]) as conn:
        conn.execute(
            "INSERT INTO processing_logs "
            "(ticket_number, category, button_text, start_time, wait_time, status, created_at) "
            "VALUES (?, ?, ?, ?, 0, 'processing', ?)",
            (ticket_number, category, "seed", now, now),
        )


def request(client: Any, method: str, route: str, payload: dict[str, Any] | None) -> Any:
    if method == "GET":
        return client.get(route)
    return client.post(route, data=json.dumps(payload or {}), content_type="application/json")


def classify(status: int, body: Any, content_type: str, unhandled: bool) -> tuple[str, bool]:
    if unhandled or not content_type.startswith("application/json"):
        return "未処理例外", False
    failure_json = isinstance(body, dict) and (body.get("success") is False or "error" in body)
    if failure_json and status == 200:
        return "不整合", False
    if failure_json and status >= 400:
        return "適切", True
    return "適切", True


def run_case(app_module: Any, case: Case, injection_map: dict[str, Callable[[], Any]]) -> dict[str, Any]:
    original_get_db = app_module.get_db
    app_module.get_db = injection_map[case.injection]
    client = app_module.app.test_client()
    app_module.app.testing = False
    unhandled = False
    try:
        response = request(client, case.method, case.route, case.payload)
        body = response.get_json(silent=True)
        if body is None:
            body = response.get_data(as_text=True)[:120].replace("\n", " ")
        status = response.status_code
        content_type = response.content_type
    except Exception as exc:  # Flask propagated rather than returning a response.
        unhandled = True
        status = "propagated"
        content_type = "n/a"
        body = f"{type(exc).__name__}: {exc}"
    finally:
        app_module.get_db = original_get_db
    classification, consistent = classify(status if isinstance(status, int) else 500, body, content_type, unhandled)
    field = ""
    if isinstance(body, dict):
        if "success" in body:
            field = f"success={body['success']}"
        elif "error" in body:
            field = f"error={body['error']}"
    return {
        "route": case.route,
        "method": case.method,
        "exception": case.exception_label,
        "status": status,
        "content_type": content_type,
        "json": body,
        "field": field,
        "unhandled": unhandled,
        "consistent": consistent,
        "classification": classification,
    }


def normal_status(app_module: Any, case: Case) -> int:
    if case.normal_setup:
        case.normal_setup(app_module)
    client = app_module.app.test_client()
    response = request(client, case.method, case.route, case.payload)
    return response.status_code


def md_table(rows: list[dict[str, Any]], include_normal: bool = False) -> str:
    cols = ["route", "method"] + (["normal_status"] if include_normal else []) + ["exception", "status", "content_type", "field", "unhandled", "consistent", "classification", "json"]
    out = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for row in rows:
        vals = []
        for col in cols:
            val = row.get(col, "")
            if col == "json":
                val = json.dumps(val, ensure_ascii=False) if not isinstance(val, str) else val
            vals.append(str(val).replace("|", "\\|").replace("\n", " "))
        out.append("| " + " | ".join(vals) + " |")
    return "\n".join(out)


def main() -> int:
    db_path = init_temp_db()
    try:
        sys.path.insert(0, str(ROOT))
        app_module = importlib.import_module("app")
        app_module.print_ticket = lambda *args, **kwargs: None

        cases = [
            Case("/get_next_number", "POST", {"category": "A", "buttonText": "verify"}, "DB接続失敗", "connect"),
            Case("/get_next_number", "POST", {"category": "A", "buttonText": "verify"}, "SQL実行失敗", "execute"),
            Case("/get_next_number", "POST", {"category": "A", "buttonText": "verify"}, "commit失敗", "commit"),
            Case("/start_processing", "POST", {"ticket_number": 1, "category": "A"}, "DB接続失敗", "connect"),
            Case("/start_processing", "POST", {"ticket_number": 1, "category": "A"}, "SQL実行失敗", "execute"),
            Case("/start_processing", "POST", {"ticket_number": 1, "category": "A"}, "commit失敗", "commit"),
            Case("/end_processing", "POST", {"ticket_number": 1}, "DB接続失敗", "connect", seed_processing),
            Case("/end_processing", "POST", {"ticket_number": 1}, "SQL実行失敗", "execute", seed_processing),
            Case("/end_processing", "POST", {"ticket_number": 1}, "commit失敗", "commit", seed_processing),
            Case("/cancel_processing", "POST", {"ticket_number": 1}, "DB接続失敗", "connect", seed_processing),
            Case("/cancel_processing", "POST", {"ticket_number": 1}, "SQL実行失敗", "execute", seed_processing),
            Case("/cancel_processing", "POST", {"ticket_number": 1}, "commit失敗", "commit", seed_processing),
            Case("/delete_ticket", "POST", {"ticket_number": 1, "category": "A"}, "DB接続失敗", "connect"),
            Case("/delete_ticket", "POST", {"ticket_number": 1, "category": "A"}, "SQL実行失敗", "execute"),
            Case("/delete_ticket", "POST", {"ticket_number": 1, "category": "A"}, "commit失敗", "commit"),
            Case("/display_data", "GET", None, "DB接続失敗", "connect"),
            Case("/display_data", "GET", None, "SQL実行失敗", "execute"),
        ]
        injection_map = {"connect": connect_failure_db, "execute": execute_failure_db, "commit": commit_failure_db}
        rows = []
        normal_cache: dict[tuple[str, str, str], int] = {}
        for case in cases:
            key = (case.route, case.method, json.dumps(case.payload, sort_keys=True))
            if key not in normal_cache:
                normal_cache[key] = normal_status(app_module, case)
            row = run_case(app_module, case, injection_map)
            row["normal_status"] = normal_cache[key]
            rows.append(row)

        version_rows = [
            f"- Python: {platform.python_version()}",
            f"- Flask: {importlib.metadata.version('Flask')}",
            f"- SQLite module: {getattr(sqlite3, 'version', 'n/a')}; SQLite library: {sqlite3.sqlite_version}",
        ]
        inconsistent = [r for r in rows if r["classification"] == "不整合"]
        text = f"""# HTTP error status verification results\n\n## 対象commit SHA\n\n`{MAIN_SHA}`\n\n## 実行環境\n\n{chr(10).join(version_rows)}\n\n## 実行コマンド\n\n```sh\npython3 verification/http_error_status_verify.py\npython3 -m py_compile verification/http_error_status_verify.py\npython3 -m unittest test_app -v\n```\n\n## 対象ルート一覧\n\n- POST /get_next_number\n- POST /start_processing\n- POST /end_processing\n- POST /cancel_processing\n- POST /delete_ticket\n- GET /display_data\n\n## 正常系と異常系の結果表\n\n{md_table(rows, include_normal=True)}\n\n## HTTP 200で失敗JSONを返した具体例\n\n{md_table(inconsistent, include_normal=True) if inconsistent else '該当なし。'}\n\n## 本家Issue候補にするべきか\n\n本家Issue候補にするべき事実が確認された。`/start_processing`, `/end_processing`, `/cancel_processing`, `/delete_ticket` はDB内部エラー時に `success: false` と `error` を含むJSONを返す一方、HTTPステータスは200だった。\n\n## 修正案ではなく、確認された事実だけ\n\n- `/get_next_number` は確認したDB接続失敗、SQL実行失敗、commit失敗でHTTP 500のJSONを返した。\n- `/start_processing`, `/end_processing`, `/cancel_processing`, `/delete_ticket` は確認したDB接続失敗、SQL実行失敗、commit失敗でHTTP 200の失敗JSONを返した。\n- `/display_data` は確認したDB接続失敗、SQL実行失敗でHTTP 200の正常形JSON（空配列と0件）を返した。\n- Flask test client上で未処理例外としてHTML 500へ到達したケースはなかった。\n\n## 未検証事項\n\n- 実プリンター、Docker、本番DB、実ブラウザからの挙動。\n- SQLite以外のDBエラー。\n- `/processing` HTMLルートおよび対象外API。\n- 外部GitHub Issue #4へのコメント投稿。\n\n## AI Assistance\n\n- 使用ツール: OpenAI Codex\n- 利用範囲: コード読解、例外注入テスト作成、実行、結果整理\n- 人間による確認: 後で実施予定\n"""
        RESULTS_PATH.write_text(text, encoding="utf-8")
        print(text)
        return 0
    except Exception:
        traceback.print_exc()
        return 1
    finally:
        try:
            os.remove(db_path)
        except OSError:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
