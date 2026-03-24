import json
import os
from datetime import datetime
from pathlib import Path
import customtkinter as ctk

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "app_data"
CONFIG_PATH = DATA_DIR / "config.json"
HISTORY_PATH = DATA_DIR / "history.json"

DATA_DIR.mkdir(exist_ok=True)

DEFAULT_CONFIG = {
    "empresa_default": "MOVILIDAD ELECTRICA DE JALISCO",
    "cuenta_default": "MP",
    "rfc_default": "MEJ123456789",
    "theme_mode": "Dark",
    "tolerancia_resumen": 50,
    "logo_text": "MACHOTES OF TIME",
    "inventario_path": str(BASE_DIR / "machotes" / "Inventario_Final.xlsx"),
    "machote_path": str(BASE_DIR / "machotes" / "EJEMPLO MACHOTE.xlsx"),
    "precios_path": str(BASE_DIR / "machotes" / "Lista de precios ok.xlsx"),
    "output_dir": str(BASE_DIR / "machotes_generados"),
    "parse_warning_threshold": 3,
}

class AppState:
    def __init__(self):
        self.config = self._load_json(CONFIG_PATH, DEFAULT_CONFIG)
        self.history = self._load_json(HISTORY_PATH, [])
        self.inventory_cache = None
        self.last_preview = None
        self.last_generated_file = None
        self.last_import_backup = None

        mode = self.config.get("theme_mode", "Dark")
        if mode in ["Dark", "Light", "System"]:
            ctk.set_appearance_mode(mode)
        else:
            ctk.set_appearance_mode("Dark")

        from ui.components import update_theme_colors
        update_theme_colors(mode)

    def _load_json(self, path, default):
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception:
                return default.copy() if isinstance(default, dict) else list(default)
        return default.copy() if isinstance(default, dict) else list(default)

    def save_config(self):
        CONFIG_PATH.write_text(json.dumps(self.config, indent=2, ensure_ascii=False), encoding="utf-8")

    def save_history(self):
        HISTORY_PATH.write_text(json.dumps(self.history, indent=2, ensure_ascii=False), encoding="utf-8")

    def record_event(self, event_type, summary, details=None):
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "type": event_type,
            "summary": summary,
            "details": details or {},
        }
        self.history.insert(0, entry)
        self.history = self.history[:300]
        self.save_history()
