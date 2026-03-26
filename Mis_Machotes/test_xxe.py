import os
import sys
from unittest.mock import MagicMock

# Mock necessary modules
sys.modules['customtkinter'] = MagicMock()
sys.modules['pandas'] = MagicMock()
sys.modules['matplotlib'] = MagicMock()
sys.modules['pdfplumber'] = MagicMock()
sys.modules['fitz'] = MagicMock()
sys.modules['openpyxl'] = MagicMock()
sys.modules['openpyxl.styles'] = MagicMock()
sys.modules['plyer'] = MagicMock()

import machote_generator
from defusedxml.common import EntitiesForbidden

def test_xxe():
    # Create a malicious XML file
    xml_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
<!DOCTYPE foo [
  <!ELEMENT foo ANY >
  <!ENTITY xxe SYSTEM "file:///etc/passwd" >]><foo>&xxe;</foo>"""

    os.makedirs("test_xml_dir", exist_ok=True)
    with open("test_xml_dir/malicious.xml", "w") as f:
        f.write(xml_content)

    try:
        # Expected behavior: defusedxml should raise EntitiesForbidden or DTDForbidden
        machote_generator.procesar_xmls("test_xml_dir")
        print("Success: The script ran, but did it process the XML?")
    except Exception as e:
        print(f"Exception raised as expected: {type(e)}")
        assert isinstance(e, EntitiesForbidden) or type(e).__name__ in ('DTDForbidden', 'EntitiesForbidden')
    finally:
        import shutil
        shutil.rmtree("test_xml_dir")

if __name__ == "__main__":
    test_xxe()
