# Upstream PR #3 verification

Date: 2026-06-21 (JST)

Target: https://github.com/Memuro-Town/MADO-queue/pull/3

Related upstream issue: https://github.com/Memuro-Town/MADO-queue/issues/1

Verification artifacts:

- https://github.com/to4kawa/MADO-queue/pull/2
- https://github.com/to4kawa/MADO-queue/pull/3

Purpose: verify which parts of upstream PR #3 resolve Issue #1, and test the proposed database-side protection against duplicate active processing rows. The upstream PR code is not merged into this audit branch.

## Audit constraints

- This branch records evidence only.
- No production code is changed here.
- The verification branches and PRs in the fork are observation artifacts, not merge targets.
- No conclusion about municipal workflow is inferred from the technical tests alone.

## Upstream PR #3 scope

PR #3 changes the lifecycle to use stable identifiers:

- `/start_processing` requires `event_log_id`.
- `/end_processing` and `/cancel_processing` operate by `processing_id`.
- `/delete_ticket` operates by `event_log_id`.
- `/get_next_number` returns `event_log_id`.
- The waiting-list query uses `event_log_id`.
- The schema adds foreign-key and status constraints, but no uniqueness constraint for one active row per `event_log_id`.

The PR author explicitly stated in Issue #1 that database-side prevention of duplicate active rows is outside PR #3's current scope and remains a design question.

## Verified results

### V-001: Completion and cancellation target one processing row

Status: verified by static review and SQLite-level operation checks.

Using `processing_logs.id` through `processing_id` causes completion and cancellation to affect only the selected row. Rows sharing the same displayed ticket number are not selected merely because their number matches.

Conclusion: this part of Issue #1 is addressed by PR #3.

### V-002: Sequential repeated starts are suppressed by the application guard

Status: verified in the first SQLite reproduction.

The PR #3 sequence checks for an existing row with the same `event_log_id` and `status='processing'` before inserting.

Observed sequential result:

- First request found no active row and inserted one.
- Second request found the existing row and skipped insertion.
- Final active-row count: 1.

Conclusion: ordinary double-clicks and repeated requests after the first transaction commits are handled idempotently.

### V-003: True concurrent starts can still create duplicate active rows

Status: reproduced.

The first verification recreated the relevant PR #3 sequence with two independent SQLite connections:

1. Check for an active row by `event_log_id`.
2. If absent, insert a `processing` row.

Observed results:

- Two-thread case: both connections observed no active row; both inserts succeeded.
- Two-process case: both connections observed no active row; both inserts succeeded.
- No `database is locked` error occurred.
- Final state contained two `status='processing'` rows for the same `event_log_id`.

Conclusion: PR #3 partially resolves Issue #1, but does not provide a database invariant preventing concurrent duplicate active rows.

## Partial UNIQUE INDEX comparison

A second verification tested the database-side candidate discussed in Issue #1:

```sql
CREATE UNIQUE INDEX uq_processing_active_event
ON processing_logs(event_log_id)
WHERE status = 'processing';
```

This comparison intentionally tests the database constraint itself. It is not a second reproduction of the full PR #3 application guard.

### Without the partial UNIQUE INDEX

When multiple `processing` inserts were attempted for the same `event_log_id`, SQLite accepted them and duplicate active rows remained.

### With the partial UNIQUE INDEX

Observed in both thread and process tests:

- One insert succeeded.
- The other failed with `UNIQUE constraint failed: processing_logs.event_log_id`.
- No `database is locked` error occurred.
- Final active-row count remained 1.

Conclusion: the partial UNIQUE INDEX prevents concurrent duplicate active rows at the SQLite constraint layer.

## State-transition compatibility

The partial index only covers rows where `status='processing'`.

Verified behavior:

- After an active row was changed to `completed`, a new `processing` row for the same `event_log_id` could be inserted.
- A `deleted` history row did not block a new `processing` row.
- Historical `completed` and `deleted` rows remained present.

Therefore the index preserves history and allows a later restart after completion or deletion.

## Migration precondition

If duplicate active rows already exist for the same `event_log_id`, creating the partial UNIQUE INDEX fails with a uniqueness violation.

Therefore a migration adding this index must first detect and resolve existing duplicate active rows.

## Remaining workflow decision

The technical constraint permits a ticket to be started again after its previous active row has become `completed` or `deleted`.

The municipality must decide which behavior matches actual counter operations. Examples:

- A staff member accidentally marked the ticket complete and needs to resume it.
- Missing documents are discovered after completion and work on the same visitor must resume.
- A completed ticket must never be reused; a new number must always be issued.

The answer changes the final remediation design:

- If restart is allowed, the partial UNIQUE INDEX is compatible.
- If restart is forbidden, a broader uniqueness rule or a separate explicit reopen/correction workflow is required.

## Overall conclusion

1. PR #3 improves identity handling and fixes non-unique completion and cancellation targeting.
2. PR #3 suppresses sequential duplicate starts through an application-level guard.
3. PR #3 does not fully resolve simultaneous starts; concurrent duplicate active rows were reproduced.
4. The tested partial UNIQUE INDEX prevents those duplicate active rows at the database layer.
5. Final adoption depends on the municipality's decision about whether a completed ticket may be started again.

## AI assistance disclosure

- Tool: OpenAI Codex
- Scope: verification script generation, concurrency testing, and result organization
- Human review: verification code and observed results were reviewed
