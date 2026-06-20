"""Baseline audit characterization tests for current MADO-queue behavior.

These tests intentionally avoid changing production behavior.  They use a fresh
SQLite database per test and stub printer access.
"""

import importlib.util
import json
import os
import runpy
import sqlite3
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from unittest import mock

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Import after setting a harmless temporary DB so module import cannot touch a
# real numbers.db. Individual tests replace app_module.DB_PATH in setUp.
_import_fd, _import_db = tempfile.mkstemp(suffix='.db')
os.close(_import_fd)
os.environ['DB_PATH'] = _import_db
runpy.run_path(os.path.join(BASE_DIR, 'init_db.py'))
_spec = importlib.util.spec_from_file_location('app_audit_baseline', os.path.join(BASE_DIR, 'app.py'))
app_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(app_module)
ORIGINAL_PRINT_TICKET = app_module.print_ticket


def tearDownModule():
    try:
        os.remove(_import_db)
    except OSError:
        pass


class AuditBaselineTest(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        os.environ['DB_PATH'] = self.db_path
        runpy.run_path(os.path.join(BASE_DIR, 'init_db.py'))
        app_module.DB_PATH = self.db_path
        self.original_print_ticket = ORIGINAL_PRINT_TICKET
        app_module.print_ticket = mock.Mock(name='print_ticket')
        self.client = app_module.app.test_client()

    def tearDown(self):
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def rows(self, sql, params=()):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute(sql, params).fetchall()

    def post_json(self, path, payload):
        return self.client.post(path, data=json.dumps(payload), content_type='application/json')

    def issue(self, category='A', **extra):
        payload = {'category': category, 'buttonText': f'button-{category}', **extra}
        response = self.post_json('/get_next_number', payload)
        self.assertEqual(response.status_code, 200, response.get_data(as_text=True))
        return response.get_json()

    def start(self, ticket_number, category='A', **extra):
        payload = {'ticket_number': ticket_number, 'category': category, **extra}
        return self.post_json('/start_processing', payload)

    def test_html_routes_and_display_data_respond(self):
        for path in ['/', '/processing', '/display']:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn('text/html', response.content_type)
        response = self.client.get('/display_data')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {'calling': [], 'waiting_count': 0})

    def test_post_endpoints_with_no_body_and_malformed_json_are_unsupported_media_or_bad_request(self):
        for path in ['/get_next_number', '/start_processing', '/end_processing', '/cancel_processing', '/delete_ticket']:
            no_body = self.client.post(path)
            malformed = self.client.post(path, data='{bad json', content_type='application/json')
            self.assertIn(no_body.status_code, (400, 415), path)
            self.assertEqual(malformed.status_code, 400, path)

    def test_unknown_category_and_invalid_identifiers(self):
        self.assertEqual(self.post_json('/get_next_number', {'category': 'Z'}).status_code, 404)
        cases = [
            ('/start_processing', {'ticket_number': 'abc', 'category': 'A'}, 400),
            ('/start_processing', {'ticket_number': 1, 'category': 'Z'}, 400),
            ('/start_processing', {'ticket_number': 1, 'category': 'A', 'event_log_id': 'abc'}, 400),
            ('/end_processing', {'ticket_number': 'abc'}, 400),
            ('/cancel_processing', {'ticket_number': 'abc'}, 400),
            ('/delete_ticket', {'ticket_number': 1, 'category': 'Z'}, 400),
            ('/delete_ticket', {'ticket_number': 1, 'category': 'A', 'event_log_id': 'abc'}, 400),
        ]
        for path, payload, expected in cases:
            self.assertEqual(self.post_json(path, payload).status_code, expected, (path, payload))

    def test_issue_start_complete_lifecycle(self):
        ticket = self.issue('A')
        self.assertEqual(self.start(ticket['next_number'], 'A').status_code, 200)
        end = self.post_json('/end_processing', {'ticket_number': ticket['next_number']})
        self.assertEqual(end.status_code, 200)
        rows = self.rows('SELECT status, end_time, processing_time FROM processing_logs')
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 'completed')
        self.assertIsNotNone(rows[0][1])
        self.assertIsNotNone(rows[0][2])

    def test_cancel_returns_ticket_to_queue_and_allows_start_again(self):
        ticket = self.issue('A')
        self.assertEqual(self.start(ticket['next_number'], 'A').status_code, 200)
        self.assertEqual(self.post_json('/cancel_processing', {'ticket_number': ticket['next_number']}).status_code, 200)
        self.assertEqual(self.start(ticket['next_number'], 'A').status_code, 200)
        self.assertEqual(self.rows('SELECT COUNT(*) FROM processing_logs')[0][0], 1)

    def test_delete_ticket_marks_deleted(self):
        ticket = self.issue('A')
        response = self.post_json('/delete_ticket', {'ticket_number': ticket['next_number'], 'category': 'A'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.rows('SELECT status FROM processing_logs'), [('deleted',)])

    def test_start_nonexistent_and_duplicate_ticket_processing_are_accepted(self):
        self.assertEqual(self.start(999, 'A').status_code, 200)
        issued = self.issue('A')
        self.assertEqual(self.start(issued['next_number'], 'A').status_code, 200)
        self.assertEqual(self.start(issued['next_number'], 'A').status_code, 200)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM processing_logs WHERE ticket_number = ?", (issued['next_number'],))[0][0], 2)

    def test_complete_and_cancel_affect_all_matching_processing_rows(self):
        ticket = self.issue('A')
        self.start(ticket['next_number'], 'A')
        self.start(ticket['next_number'], 'A')
        self.assertEqual(self.post_json('/end_processing', {'ticket_number': ticket['next_number']}).status_code, 200)
        self.assertEqual(self.rows('SELECT status, COUNT(*) FROM processing_logs GROUP BY status'), [('completed', 2)])

        ticket_b = self.issue('B')
        self.start(ticket_b['next_number'], 'B')
        self.start(ticket_b['next_number'], 'B')
        self.assertEqual(self.post_json('/cancel_processing', {'ticket_number': ticket_b['next_number']}).status_code, 200)
        self.assertEqual(self.rows("SELECT COUNT(*) FROM processing_logs WHERE ticket_number = ?", (ticket_b['next_number'],))[0][0], 0)

    def test_number_allocation_resets_and_does_not_enforce_upper_bounds(self):
        starts = {'A': 1, 'B': 500, 'C': 800, 'D': 0}
        for category, first_number in starts.items():
            self.assertEqual(self.issue(category)['next_number'], first_number)
            self.assertEqual(self.issue(category)['next_number'], first_number + 1)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("UPDATE numbers SET current_number = 499, timestamp = DATE('now') WHERE category = 'A'")
            conn.execute("UPDATE numbers SET current_number = 799, timestamp = DATE('now') WHERE category = 'B'")
        self.assertEqual(self.issue('A')['next_number'], 500)
        self.assertEqual(self.issue('B')['next_number'], 800)

    def test_concurrent_issues_do_not_duplicate_numbers(self):
        results = []
        errors = []
        lock = threading.Lock()

        def worker():
            try:
                client = app_module.app.test_client()
                response = client.post('/get_next_number', json={'category': 'A'})
                with lock:
                    results.append(response.get_json()['next_number'])
            except Exception as exc:  # pragma: no cover - captured for assertion
                with lock:
                    errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertEqual(len(results), 8)
        self.assertEqual(len(set(results)), 8)

    def test_printer_exception_is_swallowed_and_category_d_skips_printing(self):
        app_module.print_ticket = self.original_print_ticket
        with mock.patch.object(app_module, '_print_linux', side_effect=RuntimeError('printer failed')) as linux_print:
            response = self.post_json('/get_next_number', {'category': 'A'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.rows('SELECT category, current_number FROM event_logs'), [('A', 1)])
        linux_print.assert_called_once()

        with mock.patch.object(app_module, '_print_linux', side_effect=RuntimeError('should not print')) as linux_print:
            response = self.post_json('/get_next_number', {'category': 'D'})
        self.assertEqual(response.status_code, 200)
        linux_print.assert_not_called()

    def test_timestamp_omission_and_timezone_inputs(self):
        response = self.post_json('/get_next_number', {'category': 'A'})
        self.assertEqual(response.status_code, 200)
        stored_timestamp = self.rows('SELECT timestamp FROM event_logs')[0][0]
        self.assertTrue(stored_timestamp)

        naive = (datetime.now() - timedelta(minutes=3)).isoformat()
        aware = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        self.assertEqual(self.start(1, 'A', timestamp=naive).status_code, 200)
        self.assertEqual(self.start(2, 'A', timestamp=aware).status_code, 200)
        waits = [row[0] for row in self.rows('SELECT wait_time FROM processing_logs ORDER BY id')]
        self.assertGreaterEqual(waits[0], 2)
        self.assertGreaterEqual(waits[1], 4)

    def test_fresh_and_migrated_legacy_schema_differ(self):
        fresh_info = self.rows('PRAGMA table_info(processing_logs)')
        fresh_notnull = {row[1]: row[3] for row in fresh_info}

        fd, legacy_db = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        try:
            with sqlite3.connect(legacy_db) as conn:
                conn.execute('CREATE TABLE event_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, category CHAR(1) NOT NULL, button_text TEXT, timestamp TEXT NOT NULL, current_number INTEGER NOT NULL)')
                conn.execute('CREATE TABLE processing_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, ticket_number INTEGER NOT NULL, wait_time INTEGER, processing_time INTEGER, created_at TEXT NOT NULL)')
            os.environ['DB_PATH'] = legacy_db
            migration_globals = runpy.run_path(os.path.join(BASE_DIR, 'safe_migrate_db.py'))
            migration_globals['safe_migrate']()
            migration_globals['safe_migrate']()
            with sqlite3.connect(legacy_db) as conn:
                migrated = conn.execute('PRAGMA table_info(processing_logs)').fetchall()
                migrated_event = conn.execute('PRAGMA table_info(event_logs)').fetchall()
            migrated_notnull = {row[1]: row[3] for row in migrated}
            self.assertEqual(migrated_notnull['created_at'], fresh_notnull['created_at'])
            self.assertNotEqual(migrated_notnull['status'], fresh_notnull['status'])
            self.assertIn('staff_count', {row[1] for row in migrated_event})
        finally:
            os.environ['DB_PATH'] = self.db_path
            try:
                os.remove(legacy_db)
            except OSError:
                pass


if __name__ == '__main__':
    unittest.main()
