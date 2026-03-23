from importlib.util import find_spec
from pathlib import Path
import os
import runpy
import sys
import traceback
import tkinter as tk
from tkinter import messagebox
from threading import Thread
import time

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

def show_error_and_exit(title, message):
    # We create a temporary hidden Tk window to show the messagebox
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(title, message)
    root.destroy()
    sys.exit(1)


def create_splash_screen():
    splash = tk.Tk()
    splash.overrideredirect(True)

    # Calculate position
    width = 400
    height = 200
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    splash.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

    # Zelda OOT theme colors
    bg_color = "#0F1A12"
    gold_color = "#D7B56D"
    text_color = "#F3ECD2"

    splash.configure(bg=bg_color, highlightbackground=gold_color, highlightthickness=2)

    title_label = tk.Label(splash, text="MACHOTES OF TIME", font=("Segoe UI", 24, "bold"), bg=bg_color, fg=gold_color)
    title_label.pack(expand=True)

    loading_label = tk.Label(splash, text="Cargando el Reino...", font=("Segoe UI", 12), bg=bg_color, fg=text_color)
    loading_label.pack(pady=20)

    return splash

def perform_checks(splash):
    missing = [package for module, package in REQUIRED_MODULES.items() if find_spec(module) is None]
    missing_files = [path for path in REQUIRED_FILES if not path.exists()]

    try:
        DASHBOARD_TEXT = (BASE_DIR / "dashboard_app.py").read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        splash.destroy()
        show_error_and_exit("Error", f"No se pudo leer dashboard_app.py:\n{e}")
        return

    REQUIRED_SNIPPETS = [
        "class ZeldaApp(ctk.CTk):",
        'if __name__ == "__main__":',
        "app.mainloop()",
    ]
    missing_snippets = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in DASHBOARD_TEXT]

    if missing:
        splash.destroy()
        missing_str = "\n".join(f"- {pkg}" for pkg in missing)
        msg = f"Faltan dependencias para abrir la aplicación.\n\nInstálalas con este comando:\n{sys.executable} -m pip install -r \"{REQUIREMENTS_PATH}\"\n\nPaquetes faltantes detectados:\n{missing_str}"
        show_error_and_exit("Dependencias Faltantes", msg)

    if missing_files:
        splash.destroy()
        missing_str = "\n".join(f"- {path.name}" for path in missing_files)
        msg = f"Faltan archivos base del proyecto.\n\nAsegúrate de tener esta carpeta completa dentro de Mis_Machotes:\n{missing_str}"
        show_error_and_exit("Archivos Faltantes", msg)

    if missing_snippets:
        splash.destroy()
        missing_str = "\n".join(f"- {snippet}" for snippet in missing_snippets)
        msg = f"El archivo dashboard_app.py parece incompleto o no es la versión correcta.\n\nFaltan estas partes clave dentro del archivo:\n{missing_str}"
        show_error_and_exit("Archivo Incompleto", msg)

    # Give a small delay to actually see the splash screen
    splash.after(1500, lambda: launch_app(splash))

def launch_app(splash):
    splash.destroy()
    os.chdir(BASE_DIR)

    try:
        runpy.run_path(str(BASE_DIR / "dashboard_app.py"), run_name="__main__")
    except Exception as e:
        show_error_and_exit("Error Crítico", f"La app se cerró por un error:\n\n{traceback.format_exc()}")


if __name__ == "__main__":
    splash = create_splash_screen()

    # Run checks after a short delay so the window can draw
    splash.after(100, lambda: perform_checks(splash))

    splash.mainloop()
