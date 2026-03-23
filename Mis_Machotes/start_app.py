from importlib.util import find_spec
from pathlib import Path
import os
import runpy
import sys
import traceback

BASE_DIR = Path(__file__).resolve().parent
REQUIREMENTS_CANDIDATES = [
    BASE_DIR / "requirements.txt",
    BASE_DIR.parent / "requirements.txt",
]
REQUIREMENTS_PATH = next((path for path in REQUIREMENTS_CANDIDATES if path.exists()), REQUIREMENTS_CANDIDATES[0])
REQUIRED_MODULES = {
    "customtkinter": "customtkinter",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "pdfplumber": "pdfplumber",
    "fitz": "pymupdf",
    "openpyxl": "openpyxl",
}
REQUIRED_FILES = [
    BASE_DIR / "dashboard_app.py",
    BASE_DIR / "machote_generator.py",
    BASE_DIR / "machotes" / "Inventario_Final.xlsx",
    BASE_DIR / "machotes" / "EJEMPLO MACHOTE.xlsx",
    BASE_DIR / "machotes" / "Lista de precios ok.xlsx",
]

missing = [package for module, package in REQUIRED_MODULES.items() if find_spec(module) is None]
missing_files = [path for path in REQUIRED_FILES if not path.exists()]

DASHBOARD_TEXT = (BASE_DIR / "dashboard_app.py").read_text(encoding="utf-8", errors="ignore")
REQUIRED_SNIPPETS = [
    "class ZeldaApp(ctk.CTk):",
    'if __name__ == "__main__":',
    "app.mainloop()",
]
missing_snippets = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in DASHBOARD_TEXT]

if missing:
    print("Faltan dependencias para abrir la aplicación.")
    print("Instálalas con este comando:")
    print(f"\n{sys.executable} -m pip install -r \"{REQUIREMENTS_PATH}\"\n")
    print("Paquetes faltantes detectados:")
    for package in missing:
        print(f"- {package}")
    print("\nDespués vuelve a ejecutar:")
    print(f"cd \"{BASE_DIR}\"")
    print("python start_app.py")
    raise SystemExit(1)

if missing_files:
    print("Faltan archivos base del proyecto.")
    print("Asegúrate de tener esta carpeta completa dentro de Mis_Machotes:")
    for path in missing_files:
        print(f"- {path}")
    raise SystemExit(1)

if missing_snippets:
    print("El archivo dashboard_app.py parece incompleto o no es la versión correcta.")
    print("Faltan estas partes clave dentro del archivo:")
    for snippet in missing_snippets:
        print(f"- {snippet}")
    raise SystemExit(1)

print("Abriendo la aplicación...")
os.chdir(BASE_DIR)

try:
    runpy.run_path(str(BASE_DIR / "dashboard_app.py"), run_name="__main__")
    print("La ejecución terminó sin error, pero la ventana no quedó abierta.")
    print("Esto normalmente significa que `dashboard_app.py` no es la versión completa o que se cerró de inmediato.")
    print("Prueba pegar de nuevo el archivo completo `dashboard_app.py` y vuelve a correr `python start_app.py`.")
except Exception:
    print("\nLa app se cerró por un error. Copia y pega este mensaje para revisarlo:")
    traceback.print_exc()
    raise SystemExit(1)