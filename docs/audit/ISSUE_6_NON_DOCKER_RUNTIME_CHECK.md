# Issue #6 Non-Docker Runtime Check

## Scope

- Target branch: `audit/issue-6-non-docker-runtime-check`
- Purpose: Verify the non-Docker startup path documented in `docs/DEVELOPMENT.md` for Issue #6.
- Runtime timezone: `TZ=Asia/Tokyo`
- Docker was not used for this check.
- Files intentionally changed: this audit memo only.

## Environment

| Item | Result |
| --- | --- |
| Working directory | `/workspace/MADO-queue` |
| Python | `Python 3.14.4` |
| SQLite CLI | `3.45.1 2024-01-30 16:01:20 ... (64-bit)` |
| Python `sqlite3` module | `3.45.1` |
| Waitress bind used for local smoke test | `127.0.0.1:8000` |

## Commands and Results

### Dependency installation

Command:

```bash
pip install -r requirements.txt
```

Result: passed. All dependencies were already installed, including Flask, Flask-Cors, Waitress, and pyusb.

### Database initialization with `TZ=Asia/Tokyo`

Command:

```bash
TZ=Asia/Tokyo python init_db.py
```

Result: passed.

Observed output:

```text
DB initialized: /workspace/MADO-queue/numbers.db
```

### Waitress startup with `TZ=Asia/Tokyo`

Command:

```bash
TZ=Asia/Tokyo waitress-serve --host=127.0.0.1 --port=8000 app:app
```

Result: passed.

Observed output:

```text
INFO:waitress:Serving on http://127.0.0.1:8000
```

Note: `127.0.0.1` was used instead of `0.0.0.0` to keep the smoke test bound to localhost in this environment.

### HTTP smoke test

Commands:

```bash
curl -s -o /tmp/root.html -w '%{http_code}\n' http://127.0.0.1:8000/
curl -s -o /tmp/get_next_number.json -w '%{http_code}\n' \
  -X POST http://127.0.0.1:8000/get_next_number \
  -H 'Content-Type: application/json' \
  -d '{"category":"A","buttonText":"住民票","timestamp":"2026-06-21T09:00:00+09:00"}'
curl -s -o /tmp/display_data.json -w '%{http_code}\n' http://127.0.0.1:8000/display_data
curl -s -o /tmp/processing.html -w '%{http_code}\n' http://127.0.0.1:8000/processing
curl -s -o /tmp/display.html -w '%{http_code}\n' http://127.0.0.1:8000/display
```

Results:

| Endpoint | Method | HTTP status | Response / note |
| --- | --- | --- | --- |
| `/` | GET | `200` | HTML saved to `/tmp/root.html` |
| `/get_next_number` | POST | `200` | `{"category":"A","next_number":1}` |
| `/display_data` | GET | `200` | `{"calling":[],"waiting_count":1}` |
| `/processing` | GET | `200` | HTML saved to `/tmp/processing.html` |
| `/display` | GET | `200` | HTML saved to `/tmp/display.html` |

During the `/get_next_number` request, the environment printed the expected printer-backend warning because no printer backend is available:

```text
[print_ticket] error: No backend available
```

This did not prevent issuing the queue number or returning HTTP 200.

### Python localtime check with `TZ=Asia/Tokyo`

Command:

```bash
TZ=Asia/Tokyo python - <<'PY'
import os, time, datetime
print('TZ=', os.environ.get('TZ'))
print('time.tzname=', time.tzname)
print('datetime.now().isoformat=', datetime.datetime.now().isoformat(timespec='seconds'))
print('datetime.now().astimezone().isoformat=', datetime.datetime.now().astimezone().isoformat(timespec='seconds'))
PY
```

Result: passed.

Observed output:

```text
TZ= Asia/Tokyo
time.tzname= ('JST', 'JST')
datetime.now().isoformat= 2026-06-21T16:06:49
datetime.now().astimezone().isoformat= 2026-06-21T16:06:49+09:00
```

Interpretation: Python respected `TZ=Asia/Tokyo`; `astimezone()` reported the local offset as `+09:00`.

### SQLite localtime check with `TZ=Asia/Tokyo`

Command:

```bash
TZ=Asia/Tokyo sqlite3 :memory: "select datetime('now') as utc_now, datetime('now','localtime') as localtime_now, time('now','localtime') as localtime_time;"
```

Result: passed.

Observed output:

```text
2026-06-21 07:06:49|2026-06-21 16:06:49|16:06:49
```

Interpretation: SQLite `datetime('now','localtime')` was 9 hours ahead of UTC, matching JST (`Asia/Tokyo`).

## Final Verification

Commands requested to confirm the patch scope:

```bash
git diff --stat
git status --short
```

At the time this memo was first written, the only intended repository change was this file: `docs/audit/ISSUE_6_NON_DOCKER_RUNTIME_CHECK.md`.

## Conclusion

The documented non-Docker runtime path was verified successfully with `TZ=Asia/Tokyo` for database initialization, Waitress startup, HTTP smoke tests, and Python/SQLite localtime behavior. No application source files, Docker files, or compose files were changed.

## Follow-up: JST Midnight Boundary Check

### Follow-up metadata

- Follow-up check date/time: 2026-06-21 16:11 JST (`Asia/Tokyo`) / 2026-06-21 07:11 UTC
- Branch: `audit/issue-6-non-docker-runtime-check`
- Docker usage: Docker was not used.
- Application source changes: none.
- Test timestamp: `2026-06-21T00:30:00+09:00`
- Isolated database files:
  - UTC case: `/tmp/mado-issue6-utc.db`
  - JST case: `/tmp/mado-issue6-jst.db`
- Waitress ports:
  - UTC case: `18001`
  - JST case: `18002`

### UTC case result

Runtime settings:

```bash
TZ=UTC DB_PATH=/tmp/mado-issue6-utc.db waitress-serve --host=127.0.0.1 --port=18001 app:app
```

Result summary:

- DB initialization passed with `TZ=UTC DB_PATH=/tmp/mado-issue6-utc.db python init_db.py`.
- Waitress started successfully on `http://127.0.0.1:18001`.
- `/` responded successfully before the ticket request.
- `/get_next_number` response: `{"category":"A","next_number":1}`
- `/display_data` response: `{"calling":[],"waiting_count":0}`
- Database row summary:
  - `event_logs` rows: 1
  - `processing_logs` rows: 0
  - inserted row: `category='A'`, `button_text='住民票'`, `timestamp='2026-06-21T00:30:00+09:00'`, `current_number=1`
- Python timezone output summary:
  - `TZ= UTC`
  - `time.tzname= ('UTC', 'UTC')`
  - `datetime.now.astimezone= 2026-06-21T07:10:56+00:00`
- SQLite time output summary:
  - `datetime('now') = 2026-06-21 07:10:56`
  - `datetime('now','localtime') = 2026-06-21 07:10:56`
  - `date('now','localtime') = 2026-06-21`
- Additional row date comparison under `TZ=UTC`:
  - `DATE(timestamp) = 2026-06-20`
  - `DATE(timestamp, 'localtime') = 2026-06-20`
  - `DATE('now', 'localtime') = 2026-06-21`

The attempted scripted row comparison using `ticket_number` failed because the table column is named `current_number`; the row was then inspected with the correct column name.

### JST case result

Runtime settings:

```bash
TZ=Asia/Tokyo DB_PATH=/tmp/mado-issue6-jst.db waitress-serve --host=127.0.0.1 --port=18002 app:app
```

Result summary:

- DB initialization passed with `TZ=Asia/Tokyo DB_PATH=/tmp/mado-issue6-jst.db python init_db.py`.
- Waitress started successfully on `http://127.0.0.1:18002`.
- `/` responded successfully before the ticket request.
- `/get_next_number` response: `{"category":"A","next_number":1}`
- `/display_data` response: `{"calling":[],"waiting_count":1}`
- Database row summary:
  - `event_logs` rows: 1
  - `processing_logs` rows: 0
  - inserted row: `category='A'`, `button_text='住民票'`, `timestamp='2026-06-21T00:30:00+09:00'`, `current_number=1`
- Python timezone output summary:
  - `TZ= Asia/Tokyo`
  - `time.tzname= ('JST', 'JST')`
  - `datetime.now.astimezone= 2026-06-21T16:11:01+09:00`
- SQLite time output summary:
  - `datetime('now') = 2026-06-21 07:11:01`
  - `datetime('now','localtime') = 2026-06-21 16:11:01`
  - `date('now','localtime') = 2026-06-21`
- Additional row date comparison under `TZ=Asia/Tokyo`:
  - `DATE(timestamp) = 2026-06-20`
  - `DATE(timestamp, 'localtime') = 2026-06-21`
  - `DATE('now', 'localtime') = 2026-06-21`

The attempted scripted row comparison using `ticket_number` failed because the table column is named `current_number`; the row was then inspected with the correct column name.

### Interpretation

This follow-up checks the documented non-Docker runtime path only.

It compares `TZ=UTC` and `TZ=Asia/Tokyo` using a ticket timestamp near the JST midnight boundary: `2026-06-21T00:30:00+09:00`.

Under `TZ=UTC`, the ticket row was inserted, but `/display_data` returned `waiting_count: 0`. The row date comparison showed `DATE(timestamp, 'localtime') = 2026-06-20` while `DATE('now', 'localtime') = 2026-06-21`.

Under `TZ=Asia/Tokyo`, the same ticket timestamp was visible in `/display_data` with `waiting_count: 1`. The row date comparison showed `DATE(timestamp, 'localtime') = 2026-06-21` and `DATE('now', 'localtime') = 2026-06-21`.

This supports the concern in Issue #6 that runtime timezone can affect the app's “today” filtering near the JST midnight boundary. This is an audit observation only; it does not claim the issue is fixed or fully characterized.

### Limitations

- This is a non-Docker runtime check.
- It does not test `docker compose up`.
- It does not modify the application code.
- It uses the current runtime date for `DATE('now','localtime')`, so results may depend on the actual execution date/time.
- A deterministic unit test with controlled “now” would be needed for a complete regression test.
- The scripted database inspection initially referenced `ticket_number`, but this schema uses `current_number`; the follow-up row comparison was rerun with the correct column.

### Final verification for follow-up

Commands:

```bash
git diff --stat
git status --short
```

Observed final `git diff --stat` after appending this follow-up section:

```text
docs/audit/ISSUE_6_NON_DOCKER_RUNTIME_CHECK.md | 127 +++++++++++++++++++++++++
 1 file changed, 127 insertions(+)
```

Observed final `git status --short` after appending this follow-up section:

```text
 M docs/audit/ISSUE_6_NON_DOCKER_RUNTIME_CHECK.md
```
