from pathlib import Path
import argparse
import csv
import sqlite3

BASE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = BASE_DIR / "schema.sql"
CSV_DIR = BASE_DIR / "csv"
DEFAULT_OUTPUT = BASE_DIR / "sample_hub.sqlite3"

TABLES = [
    "sample_addresses",
    "sample_residents",
    "sample_households",
    "sample_household_members",
    "sample_resident_movements",
    "sample_procedure_cases",
]


def table_columns(connection, table_name):
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    if not rows:
        raise RuntimeError(f"Table is not defined by schema.sql: {table_name}")
    return [row[1] for row in rows]


def load_table(connection, table_name):
    csv_path = CSV_DIR / f"{table_name}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing required CSV file: {csv_path}")

    expected_columns = table_columns(connection, table_name)
    with csv_path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames != expected_columns:
            raise ValueError(
                f"Column mismatch for {table_name}: "
                f"expected {expected_columns}, found {reader.fieldnames}"
            )
        placeholders = ", ".join(["?"] * len(expected_columns))
        column_sql = ", ".join(expected_columns)
        insert_sql = f"INSERT INTO {table_name} ({column_sql}) VALUES ({placeholders})"
        rows = [[row[column] if row[column] != "" else None for column in expected_columns] for row in reader]
        connection.executemany(insert_sql, rows)
        return len(rows)


def create_database(output_path):
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Missing schema file: {SCHEMA_PATH}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    with sqlite3.connect(output_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        counts = {table_name: load_table(connection, table_name) for table_name in TABLES}
        connection.commit()
    return counts


def main():
    parser = argparse.ArgumentParser(description="Load MADO hub proposal CSV sample data into SQLite.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help=f"SQLite output path (default: {DEFAULT_OUTPUT})")
    args = parser.parse_args()

    counts = create_database(args.output)
    print(f"Created SQLite database: {args.output}")
    for table_name in TABLES:
        print(f"{table_name}: {counts[table_name]} rows")


if __name__ == "__main__":
    main()
