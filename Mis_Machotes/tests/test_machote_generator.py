import sys
import math
from unittest.mock import MagicMock

# Mock dependencies
class MockCTk(MagicMock): pass
class MockCTkFrame(MagicMock): pass
class MockCTkLabel(MagicMock): pass

mock_ctk = MagicMock()
mock_ctk.CTk = MockCTk
mock_ctk.CTkFrame = MockCTkFrame
mock_ctk.CTkLabel = MockCTkLabel

sys.modules['customtkinter'] = mock_ctk
sys.modules['pandas'] = MagicMock()
sys.modules['matplotlib'] = MagicMock()
sys.modules['matplotlib.pyplot'] = MagicMock()
sys.modules['pdfplumber'] = MagicMock()
sys.modules['fitz'] = MagicMock()
sys.modules['openpyxl'] = MagicMock()
sys.modules['openpyxl.styles'] = MagicMock()

import pytest
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# We need to mock pd.isna specifically as it's used in aplicar_mapeo
import pandas as pd
def mock_isna(obj):
    if obj is None: return True
    try:
        return math.isnan(obj)
    except:
        return False
pd.isna = mock_isna

from Mis_Machotes.machote_generator import aplicar_mapeo

def test_aplicar_mapeo_nan():
    # Test with NaN input
    assert aplicar_mapeo(None) is None
    res = aplicar_mapeo(float('nan'))
    assert math.isnan(res)

def test_aplicar_mapeo_exact_match():
    # Test with exact matches from MAPEOS_MODELOS
    assert aplicar_mapeo("S2 AIR V2") == "S2"
    assert aplicar_mapeo("HN-C80") == "HN-C80 PRO"
    assert aplicar_mapeo("M2MAX") == "M2MAX 8.5"
    assert aplicar_mapeo("M2MAXB") == "M2MAXB10"

def test_aplicar_mapeo_case_and_whitespace():
    # Test with different casing and whitespace
    assert aplicar_mapeo("  s2 air v2  ") == "S2"
    assert aplicar_mapeo("hn-c80") == "HN-C80 PRO"
    assert aplicar_mapeo("m2max") == "M2MAX 8.5"

def test_aplicar_mapeo_no_match():
    # Test with models not in the mapping
    assert aplicar_mapeo("MODELO DESCONOCIDO") == "MODELO DESCONOCIDO"
    assert aplicar_mapeo("S3") == "S3"

def test_aplicar_mapeo_numeric():
    # Test with numeric inputs (should be converted to string and stripped/uppered)
    assert aplicar_mapeo(123) == "123"
