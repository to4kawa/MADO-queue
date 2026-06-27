-- Secondary/reference only.
-- CSV files under csv/ are the canonical sample data for review.
-- This file is intentionally kept as a convenience mirror for SQL readers.

.mode csv
.import --skip 1 csv/sample_addresses.csv sample_addresses
.import --skip 1 csv/sample_residents.csv sample_residents
.import --skip 1 csv/sample_households.csv sample_households
.import --skip 1 csv/sample_household_members.csv sample_household_members
.import --skip 1 csv/sample_resident_movements.csv sample_resident_movements
.import --skip 1 csv/sample_procedure_cases.csv sample_procedure_cases
