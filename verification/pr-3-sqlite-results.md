# PR #3 SQLite concurrency verification

Date: 2026-06-20 (UTC)

## Scope and constraints

- Branch: `verify/pr-3-concurrency`.
- Baseline branch `audit/mado-queue-baseline` was not touched.
- No upstream PR comments were made.
- No GitHub PR was created.
- Docker and Flask server were not used.
- Verification used Python standard library `sqlite3`, threads, and processes only.
- Production code was not modified; verification code and this result file are the only intended branch contents.

## Upstream PR #3 behavior reproduced

The verification script reproduces the relevant PR #3 schema and `start_processing` SQL order:

1. Build `processing_logs` with `event_log_id INTEGER NOT NULL REFERENCES event_logs(id)` and `status` CHECK.
2. Create non-unique indexes `idx_pl_event_log_id` and `idx_pl_status`.
3. For `start_processing`, read the `event_logs` row by `event_log_id`.
4. Execute `SELECT 1 FROM processing_logs WHERE event_log_id = ? AND status = 'processing'`.
5. If no row exists, execute `INSERT INTO processing_logs (...) VALUES (..., 'processing', ...)`.

## Commands executed

```bash
git branch main 2>/dev/null || true
git switch -C verify/pr-3-concurrency main
mkdir -p verification
python3 verification/pr_3_sqlite_verify.py | tee /tmp/pr3-results.json
```

Network `git fetch` from GitHub was attempted but failed in this environment with `CONNECT tunnel failed, response 403`; PR #3 details were read from GitHub's web-rendered PR/raw-file views instead.

## Test code

Test code is in [`verification/pr_3_sqlite_verify.py`](pr_3_sqlite_verify.py). It creates temporary SQLite databases, uses two independent SQLite connections per case, and records per-connection `SELECT` results, insert outcome, lock errors, final row counts, duplicate active processing rows, schema uniqueness, processing-id update/delete behavior, and migration idempotency behavior.

## Observed results

### Case 1: sequential two calls

- First connection:
  - `SELECT` result: `null`
  - `INSERT`: `success`
  - `database is locked`: `false`
- Second connection:
  - `SELECT` result: `[1]`
  - `INSERT`: `skipped_already_processing`
  - `database is locked`: `false`
- Final `processing_logs` count: `1`
- Multiple `status='processing'` rows for the same `event_log_id`: no

Conclusion: the application-level SELECT-then-INSERT guard works for sequential execution.

### Case 2: two threads at nearly the same time

- Thread 1:
  - `SELECT` result: `null`
  - `INSERT`: `success`
  - `database is locked`: `false`
- Thread 2:
  - `SELECT` result: `null`
  - `INSERT`: `success`
  - `database is locked`: `false`
- Final `processing_logs` count: `2`
- Multiple `status='processing'` rows for the same `event_log_id`: yes, `event_log_id=1` had count `2`

Conclusion: both independent connections can observe no active processing row and both can insert. This demonstrates the race remains under threaded concurrency.

### Case 3: two processes at nearly the same time

- Process 1:
  - `SELECT` result: `null`
  - `INSERT`: `success`
  - `database is locked`: `false`
- Process 2:
  - `SELECT` result: `null`
  - `INSERT`: `success`
  - `database is locked`: `false`
- Final `processing_logs` count: `2`
- Multiple `status='processing'` rows for the same `event_log_id`: yes, `event_log_id=1` had count `2`

Conclusion: both independent processes can observe no active processing row and both can insert. This demonstrates the race remains under process concurrency.

### Schema uniqueness check

`PRAGMA index_list(processing_logs)` showed only these indexes:

- `idx_pl_status`, non-unique, column `status`
- `idx_pl_event_log_id`, non-unique, column `event_log_id`

The `processing_logs` table SQL contained `PRIMARY KEY`, `NOT NULL`, `REFERENCES`, and `CHECK`, but no `UNIQUE` constraint and no partial unique index such as `UNIQUE(event_log_id) WHERE status='processing'`.

Conclusion: PR #3's schema does **not** prevent duplicate active processing rows at the database level.

### `processing_id` UPDATE and DELETE checks

- `UPDATE processing_logs ... WHERE id = ? AND status = 'processing'` changed exactly `1` row.
- `DELETE FROM processing_logs WHERE id = ? AND status = 'processing'` changed exactly `1` row.
- Remaining row after the update/delete check: only row `id=1`, `status='completed'`.

Conclusion: using `processing_logs.id` for completion/cancel targets one row in SQLite as expected.

### `safe_migrate_db.py` idempotency and FK check

The verification database was already built with the PR #3 migrated schema. The PR #3 migration's initial FK check therefore takes the idempotent no-op path:

- Run 1: `Already migrated (FK to event_logs present). Nothing to do.`
- Run 2: `Already migrated (FK to event_logs present). Nothing to do.`
- `PRAGMA foreign_key_check` returned no violations.

Conclusion: the already-migrated-schema path is idempotent, and FK integrity was clean in the SQLite-only verification DB.

## Overall conclusion for Issue #1

**Issue #1 is only partially resolved by upstream PR #3.**

What PR #3 improves:

- It moves operations to stable IDs (`event_log_id` and `processing_id`) instead of daily-reset ticket numbers.
- Sequential duplicate `start_processing` calls become idempotent because the second call sees the existing active processing row.
- `end_processing` and `cancel_processing` by `processing_id` affect only the intended row.

What remains unresolved:

- The `start_processing` duplicate guard is still an application-level `SELECT` followed by `INSERT` without a database uniqueness constraint or explicit write transaction around the read/write pair.
- Under true concurrency, two independent SQLite connections can both read "no active processing row" and then both insert `status='processing'` for the same `event_log_id`.
- No `database is locked` error occurred in the observed thread/process runs; therefore the duplicate rows are not merely hidden by incidental SQLite locking.
- Even if a future run happened to produce `database is locked`, that would be lock timing, not a correctness guarantee equivalent to a UNIQUE constraint.

A complete DB-level fix would require preventing duplicate active processing rows with a UNIQUE constraint or partial UNIQUE INDEX, or otherwise making the read/write sequence atomic. Per the task constraints, no production fix was made here.
