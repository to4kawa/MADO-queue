# HTTP error status verification

Date: 2026-06-21 (JST)

Fork issue: https://github.com/to4kawa/MADO-queue/issues/4

Verification PR: https://github.com/to4kawa/MADO-queue/pull/5

Target commit: `fb7198230f2a10cf28c43fba45b79147dd7ec74e`

## Purpose

Verify whether API routes return an HTTP success status while the JSON body reports an internal database failure.

This record contains observations only. No production code is changed in the audit branch.

## Method

The verification used:

- Flask test client
- A temporary SQLite database initialized with `init_db.py`
- Runtime replacement of `app.get_db` to inject database connection, SQL execution, and commit failures
- Runtime replacement of `app.print_ticket` to avoid printer access

Commands reported by the verification PR:

```text
python3 verification/http_error_status_verify.py
python3 -m py_compile verification/http_error_status_verify.py
python3 -m unittest test_app -v
```

The existing six unit tests passed in the verification environment.

## Confirmed results

### H-001: Four mutation APIs return HTTP 200 for internal DB failures

Status: reproduced.

Affected routes:

- `POST /start_processing`
- `POST /end_processing`
- `POST /cancel_processing`
- `POST /delete_ticket`

For each route, the following injected failures were tested:

- Database connection failure
- SQL execution failure
- Commit failure

Observed response in all tested cases:

- HTTP status: `200`
- Content-Type: `application/json`
- JSON includes `success: false`
- JSON includes `error: "Internal server error"`

Conclusion:

The response body reports failure while the HTTP status reports success. Clients that inspect the JSON body can detect the error, but HTTP-level monitoring, proxies, logs, and generic API clients may classify the request as successful.

### H-002: `/get_next_number` returns HTTP 500 for the same classes of failure

Status: reproduced.

For database connection, SQL execution, and commit failures, the route returned:

- HTTP status: `500`
- Content-Type: `application/json`
- JSON: `{"error": "Internal server error"}`

Conclusion:

Internal-error status handling is inconsistent between `/get_next_number` and the four mutation APIs listed in H-001.

### H-003: `/display_data` converts DB failures into a normal empty response

Status: reproduced; classification requires specification review.

For database connection and SQL execution failures, the route returned:

- HTTP status: `200`
- Content-Type: `application/json`
- JSON: `{"calling": [], "waiting_count": 0}`

The verification script classified this as appropriate because the JSON did not contain `success: false` or `error`. That classification is incomplete.

Observed technical behavior:

- A real database failure is indistinguishable at the API boundary from a valid state where nobody is being called and nobody is waiting.
- The lobby display can therefore show an empty queue during a DB failure.
- HTTP-level monitoring cannot detect the failure from the response.

Possible interpretations:

- Intentional availability fallback: keep the display operating with empty values.
- Silent failure: mask a system fault as valid operational data.

No conclusion is made here about which behavior is intended. Upstream specification or maintainer confirmation is required.

## Scope and limitations

Verified:

- Flask test-client responses for the listed routes
- SQLite-related exception handling
- JSON body and HTTP status consistency

Not verified:

- Docker or Waitress behavior
- Reverse-proxy behavior
- Real printer behavior
- Production database behavior
- Browser-visible handling
- Non-SQLite failures
- Routes outside the tested set

The failure objects used for injection are test doubles, not every possible SQLite exception form. This does not weaken the central observation because the tested route exception handlers were reached and their actual HTTP responses were recorded.

## Upstream issue decision

### Mutation API inconsistency

Recommended for upstream issue reporting.

Reasons:

- Reproducible on four routes
- Independent of Issue #1 and Issue #2
- Concrete API-contract and observability impact
- Different behavior already exists in `/get_next_number`, demonstrating an internal inconsistency

### `/display_data` fallback

Do not present as a confirmed defect without separating it from the mutation API issue.

Options:

1. Include it in the same upstream issue as a secondary specification question.
2. Create a separate issue asking whether empty-data fallback during DB failure is intentional.
3. Record only in the audit if maintainers confirm that the fallback is intentional.

## Current conclusion

1. A confirmed HTTP status inconsistency exists in four mutation APIs.
2. `/get_next_number` already returns HTTP 500 for equivalent internal failures.
3. `/display_data` masks tested DB failures as valid empty queue data; whether that is a defect or an intentional fallback remains unresolved.
4. The verification PR should not be merged into `main`; it is evidence only.

## AI assistance disclosure

- Tool: OpenAI Codex
- Scope: code reading, exception-injection test creation, execution, and result organization
- Human review: verification code and reported results were reviewed
