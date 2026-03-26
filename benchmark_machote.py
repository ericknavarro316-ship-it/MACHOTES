import time
import re
from unittest.mock import patch, MagicMock

# Import the module to test
import machote_generator as mg

def run_benchmark(num_items=1000):
    print(f"Running benchmark with {num_items} items...")

    # We will simulate the behavior of the `extraer_nuevos_articulos` function.
    # To do this without a real PDF, we can mock the `pdfplumber.open` and the `fitz` interactions,
    # or just copy the logic we want to test into a small isolated function.

    # Let's create a simulated text block that `extraer_nuevos_articulos` parses
    lines = []

    # We will generate `num_items` blocks
    for i in range(num_items):
        # A main item line
        # Format: nombre_completo \s+ \d+ \s+ \(\d+\) \s+ [A-Z0-9, ]+ \s+ \$[\d,]+\.\d{2}
        series = f"SERIE{i}A, SERIE{i}B, SERIE{i}C"
        line = f"Item {i}  3 (3)  {series}  $100.00"
        lines.append(line)

        # A few extra series lines
        lines.append(f"EXTRASERIE{i}D, EXTRASERIE{i}E")
        lines.append(f"EXTRASERIE{i}F, EXTRASERIE{i}G")

    # We can mock `pdfplumber.open` to return this text
    class MockPage:
        def __init__(self, text):
            self.text = text
            self.page_number = 1
        def extract_text(self, layout=True):
            return self.text

    class MockPdf:
        def __init__(self, text):
            self.pages = [MockPage(text)]
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    full_text = "\n".join(lines)

    with patch('pdfplumber.open', return_value=MockPdf(full_text)), \
         patch('machote_generator._guardar_warnings_pdf'):

        start_time = time.time()
        # Call the function
        result = mg.extraer_nuevos_articulos("reporte-productos test.pdf", with_report=False)
        end_time = time.time()

    execution_time = end_time - start_time
    print(f"Extracted {len(result)} items in {execution_time:.4f} seconds.")
    return execution_time

if __name__ == "__main__":
    run_benchmark(100)
    run_benchmark(500)
    run_benchmark(1000)
    run_benchmark(2000)
