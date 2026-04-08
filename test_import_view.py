import sys
sys.path.append("Mis_Machotes")
import unittest
from unittest.mock import MagicMock
import pandas as pd
import import_view

class TestImportViewDeps(unittest.TestCase):
    def test_mg_available(self):
        self.assertTrue(hasattr(import_view.mg, 'aplicar_mapeo'))

if __name__ == '__main__':
    unittest.main()
