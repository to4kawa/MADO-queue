-- MADO hub sample data schema draft
--
-- This is NOT a production schema.
-- This is NOT a Juki Net connection specification.
-- This is NOT the official MADO hub schema.
--
-- Purpose:
--   Provide a fully fictional, reviewable data shape for OSS discussion.
--   The schema is intentionally small and limited to fields likely needed by
--   window-counter support flows: lookup, household selection, address display,
--   movement history checks, and form/care/move test scenarios.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sample_addresses (
    address_id        TEXT PRIMARY KEY,
    municipality_code TEXT NOT NULL,
    municipality_name TEXT NOT NULL,
    town_name         TEXT NOT NULL,
    block_name        TEXT,
    lot_number        TEXT,
    building_name     TEXT,
    room_number       TEXT,
    display_address   TEXT NOT NULL,
    is_fictional      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS sample_residents (
    resident_id       TEXT PRIMARY KEY,
    local_person_code TEXT NOT NULL UNIQUE,
    family_name       TEXT NOT NULL,
    given_name        TEXT NOT NULL,
    family_name_kana  TEXT NOT NULL,
    given_name_kana   TEXT NOT NULL,
    birth_date        TEXT NOT NULL,
    sex_code          TEXT NOT NULL,
    resident_status   TEXT NOT NULL,
    current_address_id TEXT,
    note              TEXT,
    is_fictional      INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (current_address_id) REFERENCES sample_addresses(address_id)
);

CREATE TABLE IF NOT EXISTS sample_households (
    household_id      TEXT PRIMARY KEY,
    local_household_code TEXT NOT NULL UNIQUE,
    head_resident_id  TEXT NOT NULL,
    address_id        TEXT NOT NULL,
    household_status  TEXT NOT NULL,
    start_date        TEXT NOT NULL,
    end_date          TEXT,
    is_fictional      INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (head_resident_id) REFERENCES sample_residents(resident_id),
    FOREIGN KEY (address_id) REFERENCES sample_addresses(address_id)
);

CREATE TABLE IF NOT EXISTS sample_household_members (
    household_member_id TEXT PRIMARY KEY,
    household_id        TEXT NOT NULL,
    resident_id         TEXT NOT NULL,
    relationship_to_head TEXT NOT NULL,
    member_start_date   TEXT NOT NULL,
    member_end_date     TEXT,
    is_current          INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (household_id) REFERENCES sample_households(household_id),
    FOREIGN KEY (resident_id) REFERENCES sample_residents(resident_id)
);

CREATE TABLE IF NOT EXISTS sample_resident_movements (
    movement_id       TEXT PRIMARY KEY,
    resident_id       TEXT NOT NULL,
    movement_type     TEXT NOT NULL,
    movement_date     TEXT NOT NULL,
    previous_address_id TEXT,
    new_address_id    TEXT,
    description       TEXT,
    is_fictional      INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (resident_id) REFERENCES sample_residents(resident_id),
    FOREIGN KEY (previous_address_id) REFERENCES sample_addresses(address_id),
    FOREIGN KEY (new_address_id) REFERENCES sample_addresses(address_id)
);

CREATE TABLE IF NOT EXISTS sample_procedure_cases (
    case_id           TEXT PRIMARY KEY,
    case_type         TEXT NOT NULL,
    resident_id       TEXT,
    household_id      TEXT,
    scenario_title    TEXT NOT NULL,
    expected_use      TEXT NOT NULL,
    is_fictional      INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (resident_id) REFERENCES sample_residents(resident_id),
    FOREIGN KEY (household_id) REFERENCES sample_households(household_id)
);

CREATE INDEX IF NOT EXISTS idx_sample_residents_kana
    ON sample_residents(family_name_kana, given_name_kana);

CREATE INDEX IF NOT EXISTS idx_sample_household_members_household
    ON sample_household_members(household_id);

CREATE INDEX IF NOT EXISTS idx_sample_movements_resident
    ON sample_resident_movements(resident_id, movement_date);
