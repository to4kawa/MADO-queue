# MADO-queue baseline audit

Date: 2026-06-20 (UTC)
Branch: `audit/mado-queue-baseline`
Scope: evidence gathering only. Production behavior was not changed.

## Environment and commands used

- Working directory: `/workspace/MADO-queue`
- Python: `python -m unittest ...` under the container's default Python 3.14.4 runtime.
- Commands run:
  - `git checkout -b audit/mado-queue-baseline`
  - `python -m unittest test_app -v`
  - `python -m unittest test_audit_baseline -v`
  - `python -m unittest discover -v`
  - `docker compose build && docker compose up -d && sleep 3 && curl -i http://localhost:8000/ ...`

## Existing test results

`python -m unittest test_app -v` passed: 6 tests, OK.

The existing tests use a temporary SQLite database and monkeypatch `print_ticket`, so no real `numbers.db` or printer hardware was used.

## Added audit tests

Added `test_audit_baseline.py`, which imports an isolated copy of `app.py`, creates a fresh temporary SQLite database per test, and stubs or patches printer access. Covered cases:

- HTML route and `/display_data` response smoke checks.
- POST endpoints with no body and malformed JSON.
- Unknown category and invalid/missing identifiers.
- Issue → start → complete.
- Issue → start → cancel → start again.
- Issue → delete.
- Start processing for a never-issued ticket.
- Start the same issued ticket twice.
- Complete/cancel behavior when duplicate processing rows exist.
- First and consecutive number issuance for A/B/C/D.
- A and B upper-bound behavior at 499 and 799.
- Concurrent issuance uniqueness.
- Printer failure after DB commit, and category D print skip at the wrapper level.
- Timestamp omission plus naive/aware ISO processing timestamps.
- Fresh schema vs representative legacy schema migrated by `safe_migrate_db.py`, including idempotent migration.

`python -m unittest discover -v` passed: 19 tests, OK.

## Docker startup result

Docker verification could not be completed in this environment because the `docker` executable is unavailable:

```text
/bin/bash: line 1: docker: command not found
```

Classification: `operational-risk` for this audit environment only. Docker build/start and live HTTP verification must be rerun on a host with Docker Compose available.

## Actual UI/API contract notes

### UI payloads observed

- `/` renders `templates/index.html` and `static/script.js` drives ticket issuance with `POST /get_next_number` JSON fields: `category`, `buttonText`, `staffCount`, and `timestamp`.
- `/processing` renders `templates/syori.html`; actions use JSON fields including `ticket_number`, `category`, `button_text`, `timestamp`, and `event_log_id` for `/start_processing`, while complete/cancel use only `ticket_number`.
- `/display` renders `templates/display.html` and polls `/display_data`.

### API behavior characterized by tests

- `/get_next_number` returns `{'category': category, 'next_number': new_number}` on success.
- `/start_processing`, `/end_processing`, `/cancel_processing`, and `/delete_ticket` return `{'success': True}` on success.
- Missing or malformed request bodies are handled by Flask's default request parsing, not by route-specific JSON validation.

## Confirmed findings

### 1. Category A/B upper bounds are not enforced

- Classification: `requirements-mismatch`
- Evidence: `config.py` documents category bands as A=1-499 and B=500-799, and `app.py` comments repeat the same ranges. The implementation increments without checking an upper bound.
- Reproduction command/test: `python -m unittest test_audit_baseline.AuditBaselineTest.test_number_allocation_resets_and_does_not_enforce_upper_bounds -v`
- Expected behavior source: documented category bands in requirements/architecture/config comments.
- Actual behavior: when A is at 499, the next A ticket is 500; when B is at 799, the next B ticket is 800.
- Operational impact: category bands can overlap, making visual/category distinction unreliable.
- Municipal workflow confirmation required: yes, to decide whether overflow should fail, wrap, or use a different escalation process.

### 2. `/start_processing` accepts tickets that were never issued

- Classification: `confirmed-defect`
- Evidence: `start_processing` looks up `event_logs` only to copy `staff_count`; absence of a matching ticket does not block insertion into `processing_logs`.
- Reproduction command/test: `python -m unittest test_audit_baseline.AuditBaselineTest.test_start_nonexistent_and_duplicate_ticket_processing_are_accepted -v`
- Expected behavior source: queue lifecycle implied by requirements and processing screen behavior: processing starts should target waiting issued tickets.
- Actual behavior: `POST /start_processing` with `ticket_number=999`, `category=A` returns 200 and inserts a processing row.
- Operational impact: staff can display/call numbers that do not exist in the issued queue.
- Municipal workflow confirmation required: no for basic nonexistence validation; yes for the exact error response desired.

### 3. Duplicate starts for the same ticket are accepted

- Classification: `confirmed-defect`
- Evidence: no uniqueness or active-status guard is present before inserting `processing_logs` rows.
- Reproduction command/test: `python -m unittest test_audit_baseline.AuditBaselineTest.test_start_nonexistent_and_duplicate_ticket_processing_are_accepted -v`
- Expected behavior source: one waiting ticket should move to one active processing state.
- Actual behavior: starting the same issued ticket twice returns 200 twice and creates two active rows.
- Operational impact: duplicate active calls can appear and later complete/cancel operations affect more than one row.
- Municipal workflow confirmation required: no for duplicate-active prevention; yes for how to resolve existing duplicates.

### 4. Complete and cancel target all matching processing rows for the same ticket number

- Classification: `confirmed-defect`
- Evidence: `end_processing` and `cancel_processing` filter by `ticket_number`, status, and date, but not by category, event log id, or a single processing row id.
- Reproduction command/test: `python -m unittest test_audit_baseline.AuditBaselineTest.test_complete_and_cancel_affect_all_matching_processing_rows -v`
- Expected behavior source: actions in the UI are per displayed row/ticket, and duplicate rows should not all be mutated by one row action.
- Actual behavior: if duplicate active rows exist, one complete updates both to `completed`; one cancel deletes both.
- Operational impact: audit/history accuracy can be lost and multiple staff actions can be collapsed into one.
- Municipal workflow confirmation required: yes, to define the correct targeting key and duplicate remediation.

### 5. Migrated legacy schema differs from fresh schema

- Classification: `operational-risk`
- Evidence: `init_db.py` creates `processing_logs.status TEXT NOT NULL`, but `safe_migrate_db.py` adds missing `status` as nullable `TEXT` and does not recreate constraints.
- Reproduction command/test: `python -m unittest test_audit_baseline.AuditBaselineTest.test_fresh_and_migrated_legacy_schema_differ -v`
- Expected behavior source: fresh and upgraded databases should be operationally equivalent unless differences are documented.
- Actual behavior: migrated `processing_logs.status` has different nullability from a fresh database. Migration is idempotent for the representative legacy schema.
- Operational impact: upgraded installations may permit states impossible in fresh installs, complicating support and future migrations.
- Municipal workflow confirmation required: no; this is a schema management risk.

## Documentation mismatches

### API response envelope differs from docs

- Classification: `documentation-mismatch`
- Evidence: implementation returns `next_number` for `/get_next_number`; requirements/architecture should be reviewed for the documented response schema and synchronized with tests.
- Reproduction command/test: `python -m unittest test_audit_baseline.AuditBaselineTest.test_issue_start_complete_lifecycle -v`
- Expected behavior source: `docs/ARCHITECTURE.md` API section.
- Actual behavior: current route returns `category` and `next_number`; processing routes use `success` envelopes.
- Operational impact: external callers built from docs may not parse the live API correctly.
- Municipal workflow confirmation required: no.

### Timezone assumptions are not consistently enforced

- Classification: `documentation-mismatch`
- Evidence: docs/task refer to a JST assumption, while SQL date filters use SQLite `localtime` and issuance reset uses `datetime.now().date()` from the process timezone. The display route constructs a JST time for template rendering only.
- Reproduction command/test: `python -m unittest test_audit_baseline.AuditBaselineTest.test_timestamp_omission_and_timezone_inputs -v`
- Expected behavior source: documented JST assumption in audit task and operational deployment expectations.
- Actual behavior: reset/date filtering follows host/container local timezone unless the environment is configured to JST.
- Operational impact: daily reset boundaries can differ between deployment environments.
- Municipal workflow confirmation required: yes, to confirm official business-day boundary and timezone.

## Other characterized behavior

- Successful DB commit followed by a printer exception still returns success and persists the ticket, because `print_ticket` catches printer exceptions internally.
- Category D skips hardware printing in `print_ticket`, although the route still invokes the `print_ticket` wrapper.
- Concurrent issuance test with 8 threads produced unique A numbers, consistent with the `BEGIN IMMEDIATE` lock.
- Missing JSON bodies and malformed JSON rely on Flask default 415/400 handling instead of endpoint-specific JSON error envelopes.

## Unconfirmed risks

- Docker image build/start and live route checks remain unconfirmed because Docker is unavailable in this environment.
- Full browser rendering screenshots were not taken because this audit did not change UI behavior and Docker/local server startup was unavailable.
- Hardware printing behavior beyond the software exception path remains unconfirmed by design; all printer access was stubbed or patched.
- Category overflow resolution needs domain confirmation before a production fix is proposed.
- Exact JST business-day boundary behavior needs domain/deployment confirmation before a production fix is proposed.

## Reproduction summary

Run:

```bash
python -m unittest test_app -v
python -m unittest test_audit_baseline -v
python -m unittest discover -v
```

Docker follow-up on a Docker-enabled host:

```bash
docker compose build
docker compose up -d
curl -i http://localhost:8000/
curl -i http://localhost:8000/processing
curl -i http://localhost:8000/display
curl -i http://localhost:8000/display_data
docker compose down
```

## Recommended next action

1. Rerun Docker verification on a Docker-enabled host and append the result.
2. Review confirmed findings with maintainers and municipal workflow owners.
3. Split any production fixes into separate, focused branches after review.
4. Add contract documentation updates once accepted behavior is decided.
