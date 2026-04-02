import sys
import os
import unittest
import math
from unittest.mock import patch, MagicMock

# The memory mentions: "In restricted network environments, verifying module imports for 'Mis_Machotes' requires mocking 'customtkinter', 'pandas', 'matplotlib' (and its backends), 'pdfplumber', 'fitz', and 'openpyxl' (and its styles) in 'sys.modules'."
# To satisfy this requirement and allow the tests to run without failing imports,
# we mock only the required unavailable libraries globally, but NOT core functionalities like pandas entirely.
# Wait, if `pandas` is not available at all, `import pandas` inside `machote_generator` will fail.
# Let's mock the ones that are causing ModuleNotFoundError gently.

for mod in ['pdfplumber', 'fitz', 'openpyxl', 'openpyxl.styles', 'plyer', 'numpy', 'defusedxml', 'defusedxml.ElementTree']:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

try:
    import pandas as pd
except ImportError:
    # If pandas is missing, we must mock it so `machote_generator` can import it.
    class MockPandas:
        @staticmethod
        def isna(val):
            if val is None:
                return True
            if isinstance(val, float) and math.isnan(val):
                return True
            return False

        DataFrame = MagicMock()
        read_excel = MagicMock()
        notna = MagicMock()
        to_numeric = MagicMock()

    sys.modules['pandas'] = MockPandas
    import pandas as pd

# Ensure we can import modules from the main app
# The tests are run with PYTHONPATH=Mis_Machotes or similar.
import core.config as config
from machote_generator import aplicar_mapeo

# A mock for pd.isna just in case `pandas` was real but we want to be safe,
# though we already mocked it if it was unavailable.
def mock_pd_isna(val):
    if val is None:
        return True
    if isinstance(val, float) and math.isnan(val):
        return True
    return False

class TestAplicarMapeo(unittest.TestCase):

    def setUp(self):
        # We ensure config.MAPEOS_MODELOS is set to known values for testing
        self.test_mapeos = {
            "S2 AIR V2": "S2",
            "HN-C80": "HN-C80 PRO",
            "M2MAX": "M2MAX 8.5",
            "M2MAXB": "M2MAXB10"
        }
        # Patch the dict in config module
        self.patcher = patch.dict('core.config.MAPEOS_MODELOS', self.test_mapeos, clear=True)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @patch('machote_generator.pd.isna', side_effect=mock_pd_isna)
    def test_aplicar_mapeo_existing_mapping(self, mock_isna):
        """Test that models present in the mapping dictionary return their mapped value."""
        self.assertEqual(aplicar_mapeo("S2 AIR V2"), "S2")
        self.assertEqual(aplicar_mapeo("HN-C80"), "HN-C80 PRO")

    @patch('machote_generator.pd.isna', side_effect=mock_pd_isna)
    def test_aplicar_mapeo_case_insensitivity(self, mock_isna):
        """Test that mapping is case-insensitive."""
        self.assertEqual(aplicar_mapeo("s2 air v2"), "S2")
        self.assertEqual(aplicar_mapeo("hn-c80"), "HN-C80 PRO")

    @patch('machote_generator.pd.isna', side_effect=mock_pd_isna)
    def test_aplicar_mapeo_whitespace_stripping(self, mock_isna):
        """Test that leading and trailing whitespaces are stripped."""
        self.assertEqual(aplicar_mapeo("  S2 AIR V2  "), "S2")
        self.assertEqual(aplicar_mapeo("\tHN-C80\n"), "HN-C80 PRO")

    @patch('machote_generator.pd.isna', side_effect=mock_pd_isna)
    def test_aplicar_mapeo_no_mapping(self, mock_isna):
        """Test that models not in the mapping dictionary return the uppercase stripped string."""
        self.assertEqual(aplicar_mapeo("UNKNOWN MODEL"), "UNKNOWN MODEL")
        self.assertEqual(aplicar_mapeo("  unknown model  "), "UNKNOWN MODEL")

    @patch('machote_generator.pd.isna', side_effect=mock_pd_isna)
    def test_aplicar_mapeo_nan_values(self, mock_isna):
        """Test that NaN/None values are handled correctly and returned as is."""
        self.assertIsNone(aplicar_mapeo(None))

        nan_val = float('nan')
        result = aplicar_mapeo(nan_val)
        self.assertTrue(math.isnan(result))

    @patch('machote_generator.pd.isna', side_effect=mock_pd_isna)
    def test_aplicar_mapeo_numeric_values(self, mock_isna):
        """Test that numeric models are correctly cast to strings."""
        self.assertEqual(aplicar_mapeo(12345), "12345")
        self.assertEqual(aplicar_mapeo(3.14), "3.14")

if __name__ == '__main__':
    unittest.main()
