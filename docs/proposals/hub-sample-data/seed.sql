-- MADO hub fictional seed data draft
--
-- All rows are fictional.
-- Do not use real resident data in this file.
-- Names, addresses, household structures, and movement histories are synthetic.

PRAGMA foreign_keys = ON;

INSERT INTO sample_addresses
(address_id, municipality_code, municipality_name, town_name, block_name, lot_number, building_name, room_number, display_address, is_fictional)
VALUES
('ADDR-0001', '019999', '雪見町', '中央一条', '1番', '1号', NULL, NULL, '雪見町中央一条1番1号', 1),
('ADDR-0002', '019999', '雪見町', '東町二条', '3番', '5号', 'サンプルハイツ', '201', '雪見町東町二条3番5号 サンプルハイツ201', 1),
('ADDR-0003', '019999', '雪見町', '西町三条', '7番', '2号', NULL, NULL, '雪見町西町三条7番2号', 1),
('ADDR-9001', '019998', '前住所町', '仮町一丁目', '9番', '9号', NULL, NULL, '前住所町仮町一丁目9番9号', 1);

INSERT INTO sample_residents
(resident_id, local_person_code, family_name, given_name, family_name_kana, given_name_kana, birth_date, sex_code, resident_status, current_address_id, note, is_fictional)
VALUES
('RES-0001', 'P000000001', '北原', '陽一', 'キタハラ', 'ヨウイチ', '1982-04-12', 'M', 'active', 'ADDR-0001', '世帯主サンプル', 1),
('RES-0002', 'P000000002', '北原', '美咲', 'キタハラ', 'ミサキ', '1985-09-03', 'F', 'active', 'ADDR-0001', '同一世帯配偶者サンプル', 1),
('RES-0003', 'P000000003', '北原', '航', 'キタハラ', 'ワタル', '2014-06-21', 'M', 'active', 'ADDR-0001', '同一世帯子サンプル', 1),
('RES-0004', 'P000000004', '森野', '灯', 'モリノ', 'アカリ', '1997-12-08', 'F', 'active', 'ADDR-0002', '単身世帯サンプル', 1),
('RES-0005', 'P000000005', '白石', '玄', 'シライシ', 'ゲン', '1944-02-17', 'M', 'active', 'ADDR-0003', '高齢者世帯サンプル', 1),
('RES-0006', 'P000000006', '白石', '千代', 'シライシ', 'チヨ', '1948-11-29', 'F', 'active', 'ADDR-0003', '高齢者世帯サンプル', 1),
('RES-0007', 'P000000007', '夏川', '透', 'ナツカワ', 'トオル', '1976-07-01', 'M', 'moved_out', NULL, '転出済みサンプル', 1);

INSERT INTO sample_households
(household_id, local_household_code, head_resident_id, address_id, household_status, start_date, end_date, is_fictional)
VALUES
('HH-0001', 'H000000001', 'RES-0001', 'ADDR-0001', 'active', '2020-04-01', NULL, 1),
('HH-0002', 'H000000002', 'RES-0004', 'ADDR-0002', 'active', '2024-10-15', NULL, 1),
('HH-0003', 'H000000003', 'RES-0005', 'ADDR-0003', 'active', '1998-05-20', NULL, 1);

INSERT INTO sample_household_members
(household_member_id, household_id, resident_id, relationship_to_head, member_start_date, member_end_date, is_current)
VALUES
('HHM-0001', 'HH-0001', 'RES-0001', '世帯主', '2020-04-01', NULL, 1),
('HHM-0002', 'HH-0001', 'RES-0002', '妻', '2020-04-01', NULL, 1),
('HHM-0003', 'HH-0001', 'RES-0003', '子', '2020-04-01', NULL, 1),
('HHM-0004', 'HH-0002', 'RES-0004', '世帯主', '2024-10-15', NULL, 1),
('HHM-0005', 'HH-0003', 'RES-0005', '世帯主', '1998-05-20', NULL, 1),
('HHM-0006', 'HH-0003', 'RES-0006', '妻', '1998-05-20', NULL, 1);

INSERT INTO sample_resident_movements
(movement_id, resident_id, movement_type, movement_date, previous_address_id, new_address_id, description, is_fictional)
VALUES
('MOV-0001', 'RES-0001', '転入', '2020-04-01', 'ADDR-9001', 'ADDR-0001', '前住所町から雪見町へ転入した架空ケース', 1),
('MOV-0002', 'RES-0002', '転入', '2020-04-01', 'ADDR-9001', 'ADDR-0001', '前住所町から雪見町へ転入した架空ケース', 1),
('MOV-0003', 'RES-0004', '転居', '2024-10-15', 'ADDR-0003', 'ADDR-0002', '町内転居の架空ケース', 1),
('MOV-0004', 'RES-0007', '転出', '2025-03-31', 'ADDR-0002', NULL, '町外転出済みの架空ケース', 1);

INSERT INTO sample_procedure_cases
(case_id, case_type, resident_id, household_id, scenario_title, expected_use, is_fictional)
VALUES
('CASE-0001', 'move', 'RES-0004', 'HH-0002', '町内転居後の住所確認', 'move パッケージで新旧住所と世帯情報を確認する', 1),
('CASE-0002', 'form', 'RES-0001', 'HH-0001', '世帯全員の証明書申請', 'form パッケージで世帯員一覧を転記確認する', 1),
('CASE-0003', 'care', 'RES-0005', 'HH-0003', '高齢者世帯の手続き確認', 'care パッケージで世帯構成と連絡対象を確認する', 1),
('CASE-0004', 'move', 'RES-0007', NULL, '転出済み住民の検索結果確認', '転出済みステータスの表示・除外条件を確認する', 1);
