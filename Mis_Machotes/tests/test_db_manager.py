import unittest
import sqlite3
import os
import sys
from unittest.mock import patch, MagicMock

# Ensure we can import from the project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock things that might fail during imports
for mod in ['pdfplumber', 'fitz', 'openpyxl', 'openpyxl.styles', 'plyer', 'customtkinter', 'pandas']:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

import database.db_manager as db_manager

class TestDBManager(unittest.TestCase):
    def setUp(self):
        # Use an in-memory database for testing
        self.conn = sqlite3.connect(':memory:')
        self.patcher_conn = patch('database.db_manager.get_connection', return_value=self.conn)
        self.patcher_conn.start()

        # Initialize the schema
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estado TEXT NOT NULL,
            no_serie TEXT UNIQUE,
            uuid TEXT,
            machote TEXT
        )
        ''')
        self.conn.commit()

    def tearDown(self):
        self.patcher_conn.stop()
        self.conn.close()

    def test_mark_items_as_xml_success(self):
        # We need to recreate the connection because the function we test closes it.
        # But we mocked get_connection to return self.conn.
        # If mark_items_as_xml calls conn.close(), self.conn becomes unusable.
        # Let's adjust mark_items_as_xml or our mock.

        # A better mock for get_connection: return a new connection to the same in-memory DB or use a file.
        # SQLite in-memory :memory: is unique to the connection.
        # Let's use a temporary file.
        self.test_db_path = 'test_inventory.db'
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

        self.patcher_conn.stop() # stop the previous one
        self.patcher_conn = patch('database.db_manager.get_connection', side_effect=lambda: sqlite3.connect(self.test_db_path))
        self.patcher_conn.start()

        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE inventario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estado TEXT NOT NULL,
            no_serie TEXT UNIQUE,
            uuid TEXT,
            machote TEXT
        )
        ''')
        cursor.execute("INSERT INTO inventario (estado, no_serie) VALUES ('DISPONIBLE', 'SERIE1')")
        cursor.execute("INSERT INTO inventario (estado, no_serie) VALUES ('USADO', 'SERIE2')")
        cursor.execute("INSERT INTO inventario (estado, no_serie) VALUES ('OTRO', 'SERIE3')")
        conn.commit()
        conn.close()

        series_uuid_dict = {
            'SERIE1': 'UUID1',
            'SERIE2': 'UUID2',
            'SERIE3': 'UUID3' # Should not be updated because state is 'OTRO'
        }

        updated_count = db_manager.mark_items_as_xml(series_uuid_dict)

        self.assertEqual(updated_count, 2)

        # Verify results
        conn = sqlite3.connect(self.test_db_path)
        cursor = conn.cursor()
        # Verify SERIE1
        cursor.execute("SELECT estado, uuid FROM inventario WHERE no_serie='SERIE1'")
        row1 = cursor.fetchone()
        self.assertEqual(row1[0], 'XML')
        self.assertEqual(row1[1], 'UUID1')

        # Verify SERIE2
        cursor.execute("SELECT estado, uuid FROM inventario WHERE no_serie='SERIE2'")
        row2 = cursor.fetchone()
        self.assertEqual(row2[0], 'XML')
        self.assertEqual(row2[1], 'UUID2')

        # Verify SERIE3
        cursor.execute("SELECT estado, uuid FROM inventario WHERE no_serie='SERIE3'")
        row3 = cursor.fetchone()
        self.assertEqual(row3[0], 'OTRO')
        self.assertIsNone(row3[1])

    def test_mark_items_as_xml_empty(self):
        updated_count = db_manager.mark_items_as_xml({})
        self.assertIsNone(updated_count)

    def test_mark_items_as_xml_no_match(self):
        updated_count = db_manager.mark_items_as_xml({'NONEXISTENT': 'SOMEUUID'})
        self.assertEqual(updated_count, 0)

if __name__ == '__main__':
    unittest.main()
