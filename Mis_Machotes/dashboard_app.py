import os
import sys
import threading
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox, ttk

import machote_generator as mg
from core.state import AppState
import core.config as config
from ui.components import TreeBundle, CURRENT_THEME
from ui.views.dashboard_view import DashboardView
from ui.views.inventory_view import InventoryView
from ui.views.generator_view import GeneratorView
from ui.views.import_view import ImportView
from ui.views.xml_view import XMLView
from ui.views.history_view import HistoryView
from ui.views.machote_hist_view import MachoteHistoryView
from ui.views.settings_view import SettingsView

BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class RedirectText:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, string):
        self.textbox.insert("end", string)
        self.textbox.see("end")

    def flush(self):
        return None

class ZeldaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.app_state = AppState()
        self.title("MACHOTES OF TIME · Hero's Admin Panel")
        self.geometry("1480x900")
        self.minsize(1280, 760)
        self.configure(fg_color=CURRENT_THEME["bg"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.style_treeview()
        self.create_sidebar()
        self.create_log_panel()
        self.create_main_area()

        sys.stdout = RedirectText(self.log_text)
        sys.stderr = RedirectText(self.log_text)

        self.apply_runtime_config()
        self.refresh_data(force=True)
        self.show_view("dashboard")


    def apply_runtime_config(self):
        # Apply configurations to core/config.py
        config.PATH_INVENTARIO = self.app_state.config.get("inventario_path", config.PATH_INVENTARIO)
        config.PATH_MACHOTE = self.app_state.config.get("machote_path", config.PATH_MACHOTE)
        config.PATH_PRECIOS = self.app_state.config.get("precios_path", config.PATH_PRECIOS)
        config.OUTPUT_DIR = self.app_state.config.get("output_dir", config.OUTPUT_DIR)

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#162318",
            foreground=CURRENT_THEME["text"],
            fieldbackground="#162318",
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=CURRENT_THEME["gold"],
            foreground="#241B0B",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", CURRENT_THEME["forest"])])

    def create_sidebar(self):
        self.sidebar_collapsed = False
        self.sidebar = ctk.CTkFrame(self, width=270, fg_color=CURRENT_THEME["panel"], corner_radius=0, border_width=1, border_color=CURRENT_THEME["gold"])
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1)

        self.sidebar_header = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.sidebar_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 6))
        self.sidebar_header.grid_columnconfigure(0, weight=1)
        self.logo_label = ctk.CTkLabel(self.sidebar_header, text=self.app_state.config.get("logo_text", "MACHOTES OF TIME"), text_color=CURRENT_THEME["gold"], justify="left", font=ctk.CTkFont(size=28, weight="bold"))
        self.logo_label.grid(row=0, column=0, sticky="w")
        self.sidebar_toggle_btn = ctk.CTkButton(
            self.sidebar_header,
            text="▲",
            width=42,
            fg_color=CURRENT_THEME["panel_alt"],
            hover_color=CURRENT_THEME["gold_hover"],
            command=self.toggle_sidebar,
        )
        self.sidebar_toggle_btn.grid(row=0, column=1, sticky="e", padx=(8, 0))
        self.sidebar_subtitle = ctk.CTkLabel(self.sidebar, text="Panel inspirado en Ocarina of Time", text_color=CURRENT_THEME["text"], font=ctk.CTkFont(size=12))
        self.sidebar_subtitle.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        self.nav_buttons = {}
        self.nav_labels_full = {}
        nav_items = [
            ("dashboard", "🗺 Dashboard"),
            ("inventario", "📦 Inventario"),
            ("machotes", "⚔ Generador"),
            ("carga", "🚢 Carga PDF"),
            ("xml", "🧾 Validar XML"),
            ("history", "📜 Historial"),
            ("machote_hist", "🗂 Machotes"),
            ("settings", "🔮 Ajustes"),
        ]
        for idx, (key, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(self.sidebar, text=label, anchor="w", fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["forest_hover"], text_color=CURRENT_THEME["text"], height=42, command=lambda k=key: self.show_view(k))
            btn.grid(row=idx, column=0, sticky="ew", padx=18, pady=6)
            self.nav_buttons[key] = btn
            self.nav_labels_full[key] = label

        self.quick = ctk.CTkFrame(self.sidebar, fg_color=CURRENT_THEME["panel_alt"], corner_radius=16, border_width=1, border_color=CURRENT_THEME["gold"])
        self.quick.grid(row=10, column=0, sticky="ew", padx=18, pady=18)
        ctk.CTkLabel(self.quick, text="Atajos del Héroe", text_color=CURRENT_THEME["gold"], font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkButton(self.quick, text="Recargar datos", fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", command=lambda: self.refresh_data(force=True)).pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(self.quick, text="Abrir carpeta salida", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], text_color=CURRENT_THEME["text"], command=self.open_output_folder).pack(fill="x", padx=12, pady=(0, 12))

    def toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed
        if self.sidebar_collapsed:
            self.sidebar.configure(width=82)
            self.logo_label.configure(text="△")
            self.sidebar_subtitle.grid_remove()
            self.quick.grid_remove()
            self.sidebar_toggle_btn.configure(text="👁")
            for key, btn in self.nav_buttons.items():
                icon = self.nav_labels_full[key].split(" ")[0]
                btn.configure(text=icon, anchor="center")
        else:
            self.sidebar.configure(width=270)
            self.logo_label.configure(text=self.app_state.config.get("logo_text", "MACHOTES OF TIME"))
            self.sidebar_subtitle.grid()
            self.quick.grid()
            self.sidebar_toggle_btn.configure(text="▲")
            for key, btn in self.nav_buttons.items():
                btn.configure(text=self.nav_labels_full[key], anchor="w")

    def create_main_area(self):
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.views = {
            "dashboard": DashboardView(self.main_area, self),
            "inventario": InventoryView(self.main_area, self),
            "machotes": GeneratorView(self.main_area, self),
            "carga": ImportView(self.main_area, self),
            "xml": XMLView(self.main_area, self),
            "history": HistoryView(self.main_area, self),
            "machote_hist": MachoteHistoryView(self.main_area, self),
            "settings": SettingsView(self.main_area, self),
        }
        self.history_view = self.views["history"]

    def create_log_panel(self):
        self.log_collapsed = False
        self.log_frame = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=0, border_width=1, border_color=CURRENT_THEME["gold"])
        self.log_frame.grid(row=1, column=1, sticky="nsew")
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self.log_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text="Sheikah Log", text_color=CURRENT_THEME["gold"], font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=4, pady=2)
        self.log_toggle_btn = ctk.CTkButton(
            header,
            text="◣",
            width=40,
            height=28,
            fg_color=CURRENT_THEME["panel_alt"],
            hover_color=CURRENT_THEME["forest_hover"],
            command=self.toggle_log_panel,
        )
        self.log_toggle_btn.grid(row=0, column=1, sticky="e", padx=(6, 0))

        self.log_text = ctk.CTkTextbox(self.log_frame, height=150, fg_color="#101712", text_color=CURRENT_THEME["text"], border_width=1, border_color=CURRENT_THEME["gold"], font=("Consolas", 11))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.log("Santuario inicializado. Bienvenido al reino de los machotes.")

    def toggle_log_panel(self):
        self.log_collapsed = not self.log_collapsed
        if self.log_collapsed:
            self.log_text.grid_remove()
            self.grid_rowconfigure(1, weight=0, minsize=44)
            self.log_toggle_btn.configure(text="◢")
        else:
            self.log_text.grid()
            self.grid_rowconfigure(1, weight=0, minsize=0)
            self.log_toggle_btn.configure(text="◣")

    def create_treeview(self, parent, columns):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show="headings")
        for column_id, label, width in columns:
            tree.heading(column_id, text=label)
            tree.column(column_id, width=width, anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        y_scroll = ctk.CTkScrollbar(frame, command=tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ctk.CTkScrollbar(frame, orientation="horizontal", command=tree.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        return TreeBundle(frame, tree)

    def money(self, value):
        import math
        try:
            val = float(value)
            if math.isnan(val):
                return "$0.00"
            return f"${val:,.2f}"
        except Exception:
            return "$0.00"

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{timestamp}] {message}\n")
        self.log_text.see("end")

    def run_in_thread(self, callback):
        thread = threading.Thread(target=callback, daemon=True)
        thread.start()

    def get_inventory_data(self, refresh=False):
        if self.app_state.inventory_cache is None or refresh:
            try:
                df_reporte, df_usados, df_xml, df_precios = mg.load_data()
                self.app_state.inventory_cache = {
                    "reporte": df_reporte,
                    "usados": df_usados,
                    "xml": df_xml,
                    "precios": df_precios,
                }
            except Exception as exc:
                self.log(f"Error cargando datos base: {exc}")
                messagebox.showerror("Datos no disponibles", f"No se pudieron leer los archivos base.\n\n{exc}")
                return None
        return self.app_state.inventory_cache

    def refresh_data(self, force=False):
        self.app_state.inventory_cache = None if force else self.app_state.inventory_cache
        inventory = self.get_inventory_data(refresh=force)
        if not inventory:
            return
        self.views["dashboard"].refresh()
        self.views["inventario"].refresh()
        self.views["history"].refresh()
        self.log("Datos del reino actualizados.")

    def show_view(self, key):
        for view in self.views.values():
            view.grid_forget()
        self.views[key].grid(row=0, column=0, sticky="nsew")
        for btn_key, btn in self.nav_buttons.items():
            active = btn_key == key
            btn.configure(fg_color=CURRENT_THEME["gold"] if active else CURRENT_THEME["panel_alt"], text_color="#241B0B" if active else CURRENT_THEME["text"])
        if hasattr(self.views[key], "refresh"):
            self.views[key].refresh()

    def open_output_folder(self):
        output_dir = Path(self.app_state.config.get("output_dir", config.OUTPUT_DIR))
        output_dir.mkdir(exist_ok=True)
        self.log(f"Carpeta de salida lista en {output_dir}")
        messagebox.showinfo("Carpeta de salida", f"Ubicación actual:\n\n{output_dir.resolve()}")

    def on_close(self):
        self.app_state.save_config()
        self.app_state.save_history()
        self.destroy()


if __name__ == "__main__":
    app = ZeldaApp()
    app.mainloop()
