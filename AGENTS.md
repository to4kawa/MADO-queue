# AGENTS.md

## Purpose

This fork is used to audit MADO-queue before proposing any behavioral change.
The first phase is evidence gathering and reproducible testing, not refactoring.

## Source of truth

Read these files before changing code:

1. `docs/REQUIREMENTS.md` — business requirements
2. `docs/ARCHITECTURE.md` — implementation reference
3. `docs/DEVELOPMENT.md` — supported setup and test procedure
4. `app.py`, `init_db.py`, `safe_migrate_db.py`, templates and static files — actual behavior

When documentation and implementation disagree, record the discrepancy. Do not silently choose one as correct.

## Phase 1 scope

Allowed:

- Run the existing unit tests.
- Build and start the Docker configuration.
- Inspect all routes, templates, JavaScript, database initialization and migration code.
- Add tests that reproduce current behavior or demonstrate a suspected defect.
- Add audit notes under `docs/audit/`.
- Make test-only changes needed for isolation, deterministic execution, or hardware stubbing.

Not allowed without a separate task:

- Change production behavior.
- Redesign the UI or database.
- Add authentication or external services.
- Replace Flask, SQLite, Waitress, Bootstrap, or the printing stack.
- Perform broad formatting or unrelated refactoring.
- Assume undocumented municipal workflow requirements.

## Audit priorities

Validate these points with tests or direct evidence:

1. Existing tests pass in a clean environment.
2. Every documented API matches the actual request and response schema.
3. Category ranges A=1–499 and B=500–799 are enforced or explicitly not enforced.
4. `/start_processing` behavior for nonexistent tickets.
5. Duplicate or concurrent processing starts for the same ticket.
6. Correct targeting of `/end_processing` and `/cancel_processing` when multiple records exist.
7. Malformed JSON, missing JSON bodies, invalid categories and invalid IDs.
8. Daily reset behavior and timezone assumptions.
9. Printer failure behavior, including what the client receives and what remains in the database.
10. Schema differences between a fresh database and a database upgraded by `safe_migrate_db.py`.
11. SQLite concurrency behavior for simultaneous ticket issuance.
12. Consistency among `REQUIREMENTS.md`, `ARCHITECTURE.md`, code and tests.

## Testing rules

- Never use or modify a real `numbers.db`.
- Use temporary database files for every test case or test class.
- Stub all printer access. Do not require USB hardware.
- Prefer black-box Flask client tests for API behavior.
- Add direct SQLite assertions when verifying persistence or schema.
- A test demonstrating a suspected bug may initially fail; mark and document it clearly rather than changing production code in the same commit.
- Keep each commit focused and explain what evidence it adds.

## Reporting

Create `docs/audit/BASELINE.md` containing:

- Environment and commands used
- Existing test results
- Docker startup result
- Confirmed findings
- Unconfirmed risks
- Documentation mismatches
- Reproduction steps for each confirmed finding
- Recommended next action, without implementing it

Classify findings as:

- `confirmed-defect`
- `requirements-mismatch`
- `documentation-mismatch`
- `operational-risk`
- `needs-domain-confirmation`

Do not describe a concern as a defect unless it is reproducible or directly contradicted by the written requirements.
