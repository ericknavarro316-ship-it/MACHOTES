import sys
import os
import unittest
import sqlite3
import tempfile
from unittest.mock import MagicMock, patch

# Mock pandas before importing db_manager
sys.modules['pandas'] = MagicMock()

# Now we can import db_manager
import database.db_manager as db_manager

class TestDBManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary file for the database
        self.db_fd, self.db_path = tempfile.mkstemp()

        # Patch the DB_PATH in db_manager
        self.patcher = patch('database.db_manager.DB_PATH', self.db_path)
        self.patcher.start()

        # Initialize the database schema
        db_manager.init_db()

        # Insert some initial data for testing
        self.conn = sqlite3.connect(self.db_path)
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO inventario (estado, no_serie, modelo)
            VALUES (?, ?, ?)
        ''', ('DISPONIBLE', 'SERIE1', 'MODELO1'))
        cursor.execute('''
            INSERT INTO inventario (estado, no_serie, modelo)
            VALUES (?, ?, ?)
        ''', ('DISPONIBLE', 'SERIE2', 'MODELO2'))
        cursor.execute('''
            INSERT INTO inventario (estado, no_serie, modelo)
            VALUES (?, ?, ?)
        ''', ('XML', 'SERIE3', 'MODELO3'))
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self.patcher.stop()
        os.close(self.db_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_mark_items_as_used_happy_path(self):
        """Test marking available items as used with a machote name."""
        series_to_mark = ['SERIE1', 'SERIE2']
        machote_name = 'TEST_MACHOTE'

        updated_count = db_manager.mark_items_as_used(series_to_mark, machote_name)

        self.assertEqual(updated_count, 2)

        # Verify changes in DB
        cursor = self.conn.cursor()
        for serie in series_to_mark:
            cursor.execute("SELECT estado, machote FROM inventario WHERE no_serie = ?", (serie,))
            row = cursor.fetchone()
            self.assertEqual(row[0], 'USADO')
            self.assertEqual(row[1], 'TEST_MACHOTE')

    def test_mark_items_as_used_empty_list(self):
        """Test calling with an empty list does nothing."""
        updated_count = db_manager.mark_items_as_used([], 'SOME_MACHOTE')
        self.assertIsNone(updated_count)

    def test_mark_items_as_used_non_existent_items(self):
        """Test with series that don't exist in the database."""
        updated_count = db_manager.mark_items_as_used(['NON_EXISTENT'], 'MACHOTE')
        self.assertEqual(updated_count, 0)

    def test_mark_items_as_used_items_in_other_states(self):
        """Test that only DISPONIBLE items are marked as USADO."""
        # SERIE3 is 'XML'
        series_to_mark = ['SERIE3']
        machote_name = 'TEST_MACHOTE'

        updated_count = db_manager.mark_items_as_used(series_to_mark, machote_name)

        self.assertEqual(updated_count, 0)

        # Verify SERIE3 state hasn't changed
        cursor = self.conn.cursor()
        cursor.execute("SELECT estado, machote FROM inventario WHERE no_serie = 'SERIE3'")
        row = cursor.fetchone()
        self.assertEqual(row[0], 'XML')
        self.assertIsNone(row[1])

if __name__ == '__main__':
    unittest.main()
