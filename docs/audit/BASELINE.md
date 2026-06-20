# MADO-queue baseline audit

Date: 2026-06-21 (JST)

Branch: `audit/mado-queue-baseline`

## Scope

This record captures a static codebase audit of the current `MADO-queue` repository. No production code was changed.

Reviewed files:

- `README.md`
- `app.py`
- `config.py`
- `init_db.py`
- `test_app.py`
- `static/script.js`
- `templates/syori.html`
- `templates/display.html`

Not yet verified in this pass:

- Runtime behavior under Docker Compose
- Actual USB or Windows printer behavior
- Existing production database contents and legacy migration behavior
- Full contents of every documentation and template file

## Current architecture

The application is a small Flask monolith centered on `app.py`.

### UI and route map

| UI | Route | Main behavior |
|---|---|---|
| Ticket issue screen | `/` | Issues a ticket through `/get_next_number` |
| Staff processing screen | `/processing` | Starts, completes, cancels, or deletes tickets |
| Lobby display | `/display` | Polls `/display_data` every 3 seconds |

API routes observed:

- `POST /get_next_number`
- `POST /start_processing`
- `POST /end_processing`
- `POST /cancel_processing`
- `POST /delete_ticket`
- `GET /display_data`

### Main request flow

1. `static/script.js` sends category, button text, client-generated JST timestamp, and optional staff count to `/get_next_number`.
2. `app.py` acquires an SQLite write lock with `BEGIN IMMEDIATE` before allocating the next number.
3. The number state is updated in `numbers` and the issuance event is inserted into `event_logs`.
4. After the database transaction succeeds, the server attempts to print two tickets.
5. Printer failure is logged but does not roll back or invalidate the issued ticket.
6. The staff UI starts processing by inserting a row into `processing_logs`.
7. Completion updates matching processing rows; cancellation deletes matching processing rows; deletion creates a `deleted` processing row.
8. The lobby display shows processing rows started less than 60 seconds ago and separately shows the waiting count.

## Database model

### `numbers`

Stores the current number per category.

### `event_logs`

Stores issued tickets and their issuance metadata.

### `processing_logs`

Stores processing lifecycle events and status.

The design currently uses both legacy matching by `ticket_number + category` and newer matching through `event_log_id`.

## Confirmed findings

### F-001: Processing identity is not consistently carried through the lifecycle

Classification: data integrity / concurrency

Evidence:

- `/start_processing` accepts and stores `event_log_id`.
- `/end_processing` identifies rows only by `ticket_number`, `status`, and current date.
- `/cancel_processing` also identifies rows only by `ticket_number`, `status`, and current date.

Actual behavior:

Completion or cancellation can affect more than one matching row when duplicate active processing rows exist for the same ticket number on the same day.

Operational impact:

A duplicate start or inconsistent row state could cause multiple processing records to be completed or deleted together.

Municipal workflow confirmation required: no for the technical defect; yes before choosing the desired duplicate-operation behavior.

Recommended follow-up:

Use one stable identifier throughout the lifecycle, preferably `processing_logs.id` for processing operations and `event_log_id` for issuance linkage.

### F-002: Duplicate processing starts are not prevented by a database constraint

Classification: state integrity

Evidence:

`/start_processing` performs an unconditional insert into `processing_logs`; no unique constraint prevents two active rows for the same issued ticket.

Actual behavior:

Repeated or concurrent start requests can create duplicate `processing` rows.

Operational impact:

The processing screen and lobby display may show duplicated entries. Completion and cancellation may then affect all matching rows because of F-001.

Municipal workflow confirmation required: yes, to determine whether multiple simultaneous handlers are ever valid.

### F-003: Error responses are not consistently represented by HTTP status

Classification: API contract / observability

Evidence:

Several exception branches return JSON containing `success: false` or `error` without an explicit HTTP 5xx status.

Actual behavior:

A server-side database failure can be returned as HTTP 200 with a failure JSON body.

Operational impact:

Monitoring, reverse proxies, and clients relying on HTTP status may treat failed operations as successful requests.

Municipal workflow confirmation required: no.

### F-004: Test coverage is concentrated on issuance and basic validation

Classification: test gap

Evidence:

The existing `test_app.py` covers basic issuance, incrementing, missing category, and selected validation cases for `/start_processing`.

Missing baseline coverage includes:

- Issue → start → complete
- Issue → start → cancel → restart
- Delete lifecycle
- Duplicate start
- Multiple matching processing rows
- Daily reset and date-boundary behavior
- Number band limits
- Concurrent issuance
- Printer exception behavior
- Category D no-print behavior
- Display data behavior
- Migration idempotence and legacy schema handling

Operational impact:

Regressions in the ticket lifecycle, daily reset, concurrency, and migration behavior can reach production without detection.

Municipal workflow confirmation required: no for adding characterization tests.

### F-005: Application responsibilities are concentrated in `app.py`

Classification: maintainability

Evidence:

`app.py` contains Flask routes, SQL, transaction handling, time calculations, input validation, ESC/POS generation, and platform-specific printer access.

Operational impact:

Changes to one concern can have a broad review surface and are difficult to test in isolation.

Municipal workflow confirmation required: no, provided refactoring preserves behavior.

### F-006: The waiting-list query contains explicit legacy compatibility logic

Classification: schema evolution / maintainability

Evidence:

The waiting-list SQL considers both rows linked by `event_log_id` and older rows identified by `ticket_number + category`.

Operational impact:

The compatibility condition increases query complexity and makes identity semantics harder to reason about. It also prevents treating `event_log_id` as universally available without a migration plan.

Municipal workflow confirmation required: no for inventory; yes before removing legacy support.

## Existing positive controls

- Ticket allocation uses `BEGIN IMMEDIATE`, reducing duplicate number allocation under concurrent issuance.
- SQL parameters are used instead of string interpolation for user-supplied values.
- Ticket number and category validation exists for processing operations.
- The display template escapes values before inserting generated HTML.
- Printer execution occurs after the database transaction, so hardware failure does not erase the issuance record.
- Category start values are centralized in `config.py`.

## Priority order

1. Add characterization tests for duplicate start, multiple matching processing rows, completion, and cancellation.
2. Establish a stable processing identifier in all mutation requests.
3. Make failure HTTP status codes consistent.
4. Add lifecycle, concurrency, reset, display, printer-failure, and migration tests.
5. Only after behavior is locked by tests, split database, printer, and route responsibilities out of `app.py`.

## Audit constraint

This branch records current behavior and findings only. Confirmed findings must not be fixed in this branch. Proposed fixes belong in separate branches after review.