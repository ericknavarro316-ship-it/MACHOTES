import sys
import os
import unittest
import sqlite3
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Mock missing dependencies BEFORE importing db_manager
for mod in ['pdfplumber', 'fitz', 'openpyxl', 'openpyxl.styles', 'plyer', 'numpy']:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

try:
    import pandas as pd
except ImportError:
    class MockPandas:
        @staticmethod
        def isna(val):
            import math
            if val is None: return True
            if isinstance(val, float) and math.isnan(val): return True
            return False

        DataFrame = MagicMock()
        read_excel = MagicMock()
        read_sql_query = MagicMock()
        concat = MagicMock()
        to_numeric = MagicMock()

    sys.modules['pandas'] = MockPandas
    import pandas as pd

# Add Mis_Machotes to path if needed, though PYTHONPATH should handle it
sys.path.append(os.path.join(os.getcwd(), 'Mis_Machotes'))

import database.db_manager as db_manager

class TestDBManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for the test database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_inventory.db")

        # Patch DB_PATH in db_manager
        self.path_patcher = patch('database.db_manager.DB_PATH', self.db_path)
        self.path_patcher.start()

        # Ensure we start with a fresh DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        self.path_patcher.stop()
        shutil.rmtree(self.test_dir)

    def test_init_db(self):
        """Test that init_db creates the table and indices."""
        db_manager.init_db()
        self.assertTrue(os.path.exists(self.db_path))

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='inventario'")
        self.assertIsNotNone(cursor.fetchone())

        # Check indices
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = [row[0] for row in cursor.fetchall()]
        self.assertIn('idx_estado', indices)
        self.assertIn('idx_sucursal', indices)
        self.assertIn('idx_modelo_base', indices)
        self.assertIn('idx_no_serie', indices)

        conn.close()

    def test_is_db_initialized(self):
        """Test is_db_initialized correctly reports state."""
        # Not initialized yet
        self.assertFalse(db_manager.is_db_initialized())

        # Initialize but empty
        db_manager.init_db()
        self.assertFalse(db_manager.is_db_initialized())

        # Add one item
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO inventario (estado, no_serie) VALUES (?, ?)", ('DISPONIBLE', 'TEST-001'))
        conn.commit()
        conn.close()

        self.assertTrue(db_manager.is_db_initialized())

    def test_insert_new_items(self):
        """Test insert_new_items adds records to DB."""
        db_manager.init_db()
        articulos = [
            {
                'SUCURSAL': 'SUR',
                'MODELO BASE': 'M1',
                'COLOR': 'RED',
                'No de SERIE:': 'SERIE-1',
                'TOTAL': 100.0
            },
            {
                'SUCURSAL': 'NORTE',
                'MODELO BASE': 'M2',
                'COLOR': 'BLUE',
                'No de SERIE:': 'SERIE-2',
                'TOTAL': 200.0
            }
        ]

        db_manager.insert_new_items(articulos)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT sucursal, no_serie, total FROM inventario ORDER BY no_serie")
        rows = cursor.fetchall()
        conn.close()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ('SUR', 'SERIE-1', 100.0))
        self.assertEqual(rows[1], ('NORTE', 'SERIE-2', 200.0))

    def test_mark_items_as_used(self):
        """Test moving items from DISPONIBLE to USADO."""
        db_manager.init_db()
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO inventario (estado, no_serie) VALUES (?, ?)", ('DISPONIBLE', 'S1'))
        conn.execute("INSERT INTO inventario (estado, no_serie) VALUES (?, ?)", ('DISPONIBLE', 'S2'))
        conn.commit()
        conn.close()

        updated = db_manager.mark_items_as_used(['S1'], 'MACHOTE-A')
        self.assertEqual(updated, 1)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT estado, machote FROM inventario WHERE no_serie = 'S1'")
        row = cursor.fetchone()
        self.assertEqual(row, ('USADO', 'MACHOTE-A'))

        cursor.execute("SELECT estado FROM inventario WHERE no_serie = 'S2'")
        row = cursor.fetchone()
        self.assertEqual(row[0], 'DISPONIBLE')
        conn.close()

    def test_undo_last_import(self):
        """Test deleting specific available items."""
        db_manager.init_db()
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO inventario (estado, no_serie) VALUES (?, ?)", ('DISPONIBLE', 'S1'))
        conn.execute("INSERT INTO inventario (estado, no_serie) VALUES (?, ?)", ('USADO', 'S2'))
        conn.commit()
        conn.close()

        deleted = db_manager.undo_last_import(['S1', 'S2'])
        # S2 should not be deleted because its state is USADO
        self.assertEqual(deleted, 1)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM inventario")
        self.assertEqual(cursor.fetchone()[0], 1)
        cursor.execute("SELECT no_serie FROM inventario")
        self.assertEqual(cursor.fetchone()[0], 'S2')
        conn.close()

    def test_mark_items_as_xml(self):
        """Test moving items to XML state."""
        db_manager.init_db()
        conn = sqlite3.connect(self.db_path)
        conn.execute("INSERT INTO inventario (estado, no_serie) VALUES (?, ?)", ('USADO', 'S1'))
        conn.execute("INSERT INTO inventario (estado, no_serie) VALUES (?, ?)", ('DISPONIBLE', 'S2'))
        conn.commit()
        conn.close()

        updated = db_manager.mark_items_as_xml({'S1': 'UUID-1', 'S2': 'UUID-2'})
        self.assertEqual(updated, 2)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT estado, uuid FROM inventario WHERE no_serie = 'S1'")
        self.assertEqual(cursor.fetchone(), ('XML', 'UUID-1'))
        cursor.execute("SELECT estado, uuid FROM inventario WHERE no_serie = 'S2'")
        self.assertEqual(cursor.fetchone(), ('XML', 'UUID-2'))
        conn.close()

    def test_undo_xml_import(self):
        """Test reverting items from XML state."""
        db_manager.init_db()
        conn = sqlite3.connect(self.db_path)
        # S1 was USADO (has machote)
        conn.execute("INSERT INTO inventario (estado, no_serie, machote, uuid) VALUES (?, ?, ?, ?)",
                     ('XML', 'S1', 'M1', 'U1'))
        # S2 was DISPONIBLE (no machote)
        conn.execute("INSERT INTO inventario (estado, no_serie, machote, uuid) VALUES (?, ?, ?, ?)",
                     ('XML', 'S2', None, 'U2'))
        conn.commit()
        conn.close()

        reverted = db_manager.undo_xml_import(['S1', 'S2'])
        self.assertEqual(reverted, 2)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT estado, uuid FROM inventario WHERE no_serie = 'S1'")
        self.assertEqual(cursor.fetchone(), ('USADO', None))
        cursor.execute("SELECT estado, uuid FROM inventario WHERE no_serie = 'S2'")
        self.assertEqual(cursor.fetchone(), ('DISPONIBLE', None))
        conn.close()

if __name__ == '__main__':
    unittest.main()
