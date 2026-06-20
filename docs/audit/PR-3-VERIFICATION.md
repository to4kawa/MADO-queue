# Upstream PR #3 verification

Date: 2026-06-21 (JST)

Target: https://github.com/Memuro-Town/MADO-queue/pull/3

Purpose: verify whether upstream PR #3 actually resolves Issue #1 without merging the PR into this audit branch.

## Audit constraints

- This branch records evidence only.
- The upstream PR code is not merged here.
- No production behavior is changed.
- The goal is verification, not preparing this branch for merge.

## PR metadata

- State: open
- Draft: yes
- Mergeable according to GitHub: yes
- Base: `main` at `fb7198230f2a10cf28c43fba45b79147dd7ec74e`
- Head: `refactor/2-stable-keys` at `3fe467d0bc6f083590a9858686f6082d4f914aa6`
- Changed files: 5
- Additions: 546
- Deletions: 263

Changed files:

- `app.py`
- `init_db.py`
- `safe_migrate_db.py`
- `templates/syori.html`
- `test_app.py`

## Claimed behavior relevant to Issue #1

PR #3 changes the ticket lifecycle to use stable identifiers:

- `/start_processing` requires `event_log_id`.
- `/end_processing` and `/cancel_processing` require `processing_id`.
- `/delete_ticket` requires `event_log_id`.
- `/get_next_number` returns `event_log_id`.
- The waiting-list query uses `event_log_id` only.
- The schema adds foreign-key and status constraints.

These changes remove the previous behavior where completion and cancellation used only `ticket_number` and the current date.

## Static verification findings

### V-001: Completion and cancellation no longer target all rows with the same ticket number

Status: supported by the diff

The PR changes `/end_processing` and `/cancel_processing` to operate on `processing_logs.id` through `processing_id`.

Expected effect:

- A completion request updates one processing row.
- A cancellation request deletes one processing row.
- Old or duplicate rows with the same displayed ticket number are not selected merely because their number matches.

This directly addresses the second half of Issue #1.

### V-002: Repeated sequential start requests are treated as idempotent

Status: supported by the diff

Before inserting a new processing row, `/start_processing` checks whether a row already exists with the same `event_log_id` and `status = 'processing'`.

If found, it returns success with `already_processing: true` and does not insert another row.

Expected effect:

- Double-clicks and repeated requests that arrive after the first transaction commits should not create duplicate active rows.

### V-003: True concurrent start requests may still race

Status: unresolved risk identified by static review

The duplicate-start guard is implemented as:

1. `SELECT` for an existing active row.
2. If no row exists, `INSERT` a new row.

The reviewed diff does not show a database-side unique constraint that guarantees only one active `processing` row per `event_log_id`.

Therefore two requests that overlap closely enough may both observe no existing row before either insert is visible, then both insert.

Operational meaning:

- PR #3 appears to fix ordinary repeated requests.
- It may not fully resolve the exact near-simultaneous multi-terminal race described in Issue #1.
- A runtime concurrency test is required before concluding that Issue #1 is fully resolved.

### V-004: The PR changes the external API contract

Status: confirmed

- End and cancel requests change from `ticket_number` to `processing_id`.
- The bundled staff template is updated in the same PR.
- Any external client that calls these endpoints directly must be updated separately.

## Runtime verification status

Attempted command:

```text
git clone https://github.com/Memuro-Town/MADO-queue.git
```

Result:

```text
Could not resolve host: github.com
```

The current execution environment could not clone GitHub directly. PR metadata and patches were obtained through the GitHub connector, but the test suite has not yet been independently executed in this pass.

## Required runtime tests

1. Run the PR author's full test suite and confirm all 30 tests pass.
2. Issue one ticket and call `/start_processing` twice sequentially; verify one active row.
3. Issue one ticket and call `/start_processing` concurrently from two connections; verify whether one or two active rows are created.
4. Create representative duplicate rows, then complete one by `processing_id`; verify only the selected row changes.
5. Cancel one by `processing_id`; verify only the selected row is removed.
6. Run the legacy migration twice and verify idempotence and foreign-key integrity.

## Interim conclusion

PR #3 clearly fixes non-unique completion and cancellation targeting and improves sequential duplicate-start handling.

It is not yet proven to fully resolve Issue #1 because the near-simultaneous start race appears to rely on an application-level check rather than an enforced database invariant. The final judgment remains pending runtime concurrency verification.
