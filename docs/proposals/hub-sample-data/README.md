# MADO hub sample data proposal

This directory contains fictional sample data for discussing a draft MADO hub data shape.

## Review format

CSV is the primary review format. The files in `csv/` provide one file per sample table so reviewers can inspect columns and values without reading SQL `INSERT` statements:

- `csv/sample_addresses.csv`
- `csv/sample_residents.csv`
- `csv/sample_households.csv`
- `csv/sample_household_members.csv`
- `csv/sample_resident_movements.csv`
- `csv/sample_procedure_cases.csv`

`schema.sql` remains the table definition source for the draft structure. `seed.sql` is secondary/reference only; prefer the CSV files as the canonical sample data.

## Local SQLite testing

Run the loader to create or reset a local SQLite database from `schema.sql` and the CSV files:

```bash
python docs/proposals/hub-sample-data/scripts/load_csv_to_sqlite.py
```

The default output is `docs/proposals/hub-sample-data/sample_hub.sqlite3`. Use `--output` to write elsewhere:

```bash
python docs/proposals/hub-sample-data/scripts/load_csv_to_sqlite.py --output /tmp/sample_hub.sqlite3
```

The loader enables SQLite foreign keys, validates that every required CSV exists, and fails if CSV columns do not match the target table.

## Explicit scope limits

- This is not a production schema.
- This is not a Juki Net connection specification.
- This is not the official MADO hub schema.
- This contains no real resident data.
- All data is fictional, including municipality values such as `雪見町` and `019999`.
