from importlib.util import find_spec
from pathlib import Path
import argparse
import os
import re
import runpy
import shutil
import sys
import traceback
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
APP_DATA_DIR = BASE_DIR / "app_data"
INVENTORY_DB_PATH = APP_DATA_DIR / "inventory.db"
BACKUPS_DIR = APP_DATA_DIR / "backups"
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
    "plyer": "plyer",
    "defusedxml": "defusedxml",
    "reportlab": "reportlab",
    "PIL": "Pillow"
}
REQUIRED_FILES = [
    BASE_DIR / "dashboard_app.py",
    BASE_DIR / "machote_generator.py",
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
    height = 240
    screen_width = splash.winfo_screenwidth()
    screen_height = splash.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    splash.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

    # Try to load custom theme colors if they exist
    bg_color = "#0F1A12"
    gold_color = "#D7B56D"
    text_color = "#F3ECD2"
    app_name = "MACHOTES OF TIME"

    try:
        import json
        config_path = APP_DATA_DIR / "config.json"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                theme_mode = config_data.get("theme_mode", "Dark")
                if theme_mode == "Custom":
                    bg_color = config_data.get("custom_color_bg", bg_color)
                    gold_color = config_data.get("custom_color_gold", gold_color)
                    text_color = config_data.get("custom_color_text", text_color)
                elif theme_mode == "HoneyWhale":
                    bg_color = "#121212"
                    gold_color = "#FF3B30"
                    text_color = "#FFFFFF"
                app_name = config_data.get("logo_text", app_name)
    except Exception:
        pass

    splash.configure(bg=bg_color, highlightbackground=gold_color, highlightthickness=2)

    # Try to load the custom logo or triforce image
    try:
        from PIL import Image, ImageTk
        custom_logo_path = APP_DATA_DIR / "custom_logo.png"
        if custom_logo_path.exists():
            img = Image.open(custom_logo_path)
            # Calculate height to keep aspect ratio based on max width 120
            w, h = img.size
            new_h = int(120 * h / w)
            img = img.resize((120, new_h), Image.Resampling.LANCZOS)
        else:
            img = Image.open(BASE_DIR / "triforce.png")
            img = img.resize((80, 80), Image.Resampling.LANCZOS)

        splash.photo = ImageTk.PhotoImage(img)
        img_label = tk.Label(splash, image=splash.photo, bg=bg_color)
        img_label.pack(pady=(20, 0))
    except Exception:
        pass

    title_label = tk.Label(splash, text=app_name, font=("Segoe UI", 24, "bold"), bg=bg_color, fg=gold_color)
    title_label.pack(expand=True, pady=(10, 0))

    loading_label = tk.Label(splash, text="Cargando el Reino...", font=("Segoe UI", 12), bg=bg_color, fg=text_color)
    loading_label.pack(pady=20)

    return splash


def collect_check_results():
    missing = [package for module, package in REQUIRED_MODULES.items() if find_spec(module) is None]
    missing_files = [path for path in REQUIRED_FILES if not path.exists()]

    try:
        DASHBOARD_TEXT = (BASE_DIR / "dashboard_app.py").read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        raise RuntimeError(f"No se pudo leer dashboard_app.py: {e}") from e

    required_checks = [
        ("bloque __main__", r'if\s+__name__\s*==\s*["\']__main__["\']'),
        ("llamada a mainloop", r'\.mainloop\s*\('),
        ("uso de customtkinter", r'ctk\.CTk'),
    ]
    missing_snippets = [label for label, pattern in required_checks if not re.search(pattern, DASHBOARD_TEXT)]
    return missing, missing_files, missing_snippets


def perform_checks(splash):
    if getattr(sys, 'frozen', False):
        # Skip raw file text parsing and dependency checking if we are already compiled as an executable
        splash.after(1500, lambda: launch_app(splash))
        return

    try:
        missing, missing_files, missing_snippets = collect_check_results()
    except Exception as e:
        splash.destroy()
        show_error_and_exit("Error", str(e))
        return

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
        if getattr(sys, 'frozen', False):
            import dashboard_app
            app = dashboard_app.ZeldaApp()
            app.mainloop()
        else:
            runpy.run_path(str(BASE_DIR / "dashboard_app.py"), run_name="__main__")
    except Exception as e:
        show_error_and_exit("Error Crítico", f"La app se cerró por un error:\n\n{traceback.format_exc()}")


def run_cli_checks():
    try:
        missing, missing_files, missing_snippets = collect_check_results()
    except Exception as e:
        print(f"❌ Error al validar dashboard_app.py: {e}")
        return 1

    has_errors = False

    if missing:
        has_errors = True
        print("❌ Dependencias faltantes:")
        for pkg in missing:
            print(f"  - {pkg}")

    if missing_files:
        has_errors = True
        print("❌ Archivos base faltantes:")
        for path in missing_files:
            print(f"  - {path}")

    if missing_snippets:
        has_errors = True
        print("❌ dashboard_app.py parece incompleto; faltan snippets:")
        for snippet in missing_snippets:
            print(f"  - {snippet}")

    if has_errors:
        print(f"\nInstala dependencias con:\n{sys.executable} -m pip install -r \"{REQUIREMENTS_PATH}\"")
        return 1

    print("✅ Validación completada: entorno y archivos listos para abrir MACHOTES OF TIME.")
    return 0


def create_db_backup():
    if not INVENTORY_DB_PATH.exists():
        print(f"❌ No existe la base de datos para respaldar: {INVENTORY_DB_PATH}")
        return 1

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUPS_DIR / f"inventory_{timestamp}.db"
    shutil.copy2(INVENTORY_DB_PATH, backup_path)
    print(f"✅ Respaldo creado: {backup_path}")
    return 0


def list_db_backups():
    if not BACKUPS_DIR.exists():
        print(f"No hay carpeta de respaldos todavía: {BACKUPS_DIR}")
        return 0

    backups = sorted(BACKUPS_DIR.glob("inventory_*.db"), reverse=True)
    if not backups:
        print("No hay respaldos de base de datos disponibles.")
        return 0

    print("Respaldos disponibles:")
    for path in backups:
        size_kb = path.stat().st_size / 1024
        print(f"  - {path.name} ({size_kb:.1f} KB)")
    return 0


def get_sorted_backups():
    if not BACKUPS_DIR.exists():
        return []
    return sorted(BACKUPS_DIR.glob("inventory_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)


def prune_db_backups(keep):
    if keep < 1:
        print("❌ El valor de --prune-backups debe ser mayor o igual a 1.")
        return 1

    backups = get_sorted_backups()
    if not backups and not BACKUPS_DIR.exists():
        print(f"No existe la carpeta de respaldos: {BACKUPS_DIR}")
        return 0
    if len(backups) <= keep:
        print(f"No se eliminó nada. Respaldos actuales: {len(backups)} (límite: {keep}).")
        return 0

    to_delete = backups[keep:]
    for path in to_delete:
        path.unlink(missing_ok=True)

    print(f"✅ Limpieza completada. Eliminados: {len(to_delete)}. Conservados: {keep}.")
    return 0


def restore_db_backup(backup_name):
    if not backup_name:
        print("❌ Debes indicar el nombre del respaldo con --restore-backup <archivo.db>.")
        return 1

    backup_path = BACKUPS_DIR / backup_name
    if not backup_path.exists():
        print(f"❌ No existe el respaldo indicado: {backup_path}")
        return 1

    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    if INVENTORY_DB_PATH.exists():
        pre_restore_name = f"inventory_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        pre_restore_path = BACKUPS_DIR / pre_restore_name
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(INVENTORY_DB_PATH, pre_restore_path)
        print(f"ℹ️ Respaldo previo a restauración: {pre_restore_path}")

    shutil.copy2(backup_path, INVENTORY_DB_PATH)
    print(f"✅ Base de datos restaurada desde: {backup_path}")
    return 0


def restore_latest_backup():
    backups = get_sorted_backups()
    if not backups:
        print("❌ No hay respaldos disponibles para restaurar.")
        return 1
    return restore_db_backup(backups[0].name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Lanzador y validador de MACHOTES OF TIME.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Solo valida dependencias/archivos y termina sin abrir la interfaz gráfica.",
    )
    parser.add_argument(
        "--backup-db",
        action="store_true",
        help="Crea un respaldo de app_data/inventory.db y termina.",
    )
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="Lista los respaldos de app_data/backups y termina.",
    )
    parser.add_argument(
        "--restore-backup",
        type=str,
        default="",
        metavar="ARCHIVO",
        help="Restaura app_data/inventory.db desde app_data/backups/ARCHIVO.",
    )
    parser.add_argument(
        "--prune-backups",
        type=int,
        default=0,
        metavar="N",
        help="Conserva solo los N respaldos más recientes y elimina el resto.",
    )
    parser.add_argument(
        "--restore-latest",
        action="store_true",
        help="Restaura automáticamente el respaldo más reciente.",
    )
    args = parser.parse_args()

    if args.check_only:
        raise SystemExit(run_cli_checks())
    if args.backup_db:
        raise SystemExit(create_db_backup())
    if args.list_backups:
        raise SystemExit(list_db_backups())
    if args.restore_backup:
        raise SystemExit(restore_db_backup(args.restore_backup))
    if args.restore_latest:
        raise SystemExit(restore_latest_backup())
    if args.prune_backups:
        raise SystemExit(prune_db_backups(args.prune_backups))

    splash = create_splash_screen()

    # Run checks after a short delay so the window can draw
    splash.after(100, lambda: perform_checks(splash))

    splash.mainloop()
