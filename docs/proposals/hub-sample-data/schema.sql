PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS sample_procedure_cases;
DROP TABLE IF EXISTS sample_resident_movements;
DROP TABLE IF EXISTS sample_household_members;
DROP TABLE IF EXISTS sample_households;
DROP TABLE IF EXISTS sample_residents;
DROP TABLE IF EXISTS sample_addresses;

CREATE TABLE sample_addresses (
  address_id TEXT PRIMARY KEY,
  municipality_code TEXT NOT NULL,
  municipality_name TEXT NOT NULL,
  town_name TEXT NOT NULL,
  block_name TEXT NOT NULL,
  building_name TEXT,
  room_number TEXT,
  postal_code TEXT NOT NULL
);

CREATE TABLE sample_residents (
  resident_id TEXT PRIMARY KEY,
  municipality_code TEXT NOT NULL,
  municipality_name TEXT NOT NULL,
  display_name TEXT NOT NULL,
  kana_name TEXT NOT NULL,
  birth_date TEXT NOT NULL,
  sex TEXT NOT NULL,
  address_id TEXT NOT NULL,
  resident_status TEXT NOT NULL,
  FOREIGN KEY (address_id) REFERENCES sample_addresses(address_id)
);

CREATE TABLE sample_households (
  household_id TEXT PRIMARY KEY,
  municipality_code TEXT NOT NULL,
  municipality_name TEXT NOT NULL,
  address_id TEXT NOT NULL,
  household_head_resident_id TEXT NOT NULL,
  household_status TEXT NOT NULL,
  FOREIGN KEY (address_id) REFERENCES sample_addresses(address_id),
  FOREIGN KEY (household_head_resident_id) REFERENCES sample_residents(resident_id)
);

CREATE TABLE sample_household_members (
  household_member_id TEXT PRIMARY KEY,
  household_id TEXT NOT NULL,
  resident_id TEXT NOT NULL,
  relationship_to_head TEXT NOT NULL,
  joined_on TEXT NOT NULL,
  left_on TEXT,
  FOREIGN KEY (household_id) REFERENCES sample_households(household_id),
  FOREIGN KEY (resident_id) REFERENCES sample_residents(resident_id)
);

CREATE TABLE sample_resident_movements (
  movement_id TEXT PRIMARY KEY,
  resident_id TEXT NOT NULL,
  movement_type TEXT NOT NULL,
  effective_date TEXT NOT NULL,
  previous_address_id TEXT,
  new_address_id TEXT,
  reason_note TEXT NOT NULL,
  FOREIGN KEY (resident_id) REFERENCES sample_residents(resident_id),
  FOREIGN KEY (previous_address_id) REFERENCES sample_addresses(address_id),
  FOREIGN KEY (new_address_id) REFERENCES sample_addresses(address_id)
);

CREATE TABLE sample_procedure_cases (
  procedure_case_id TEXT PRIMARY KEY,
  resident_id TEXT NOT NULL,
  household_id TEXT,
  procedure_type TEXT NOT NULL,
  channel TEXT NOT NULL,
  status TEXT NOT NULL,
  submitted_on TEXT NOT NULL,
  completed_on TEXT,
  memo TEXT NOT NULL,
  FOREIGN KEY (resident_id) REFERENCES sample_residents(resident_id),
  FOREIGN KEY (household_id) REFERENCES sample_households(household_id)
);
