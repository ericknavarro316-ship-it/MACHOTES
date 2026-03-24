import json
import os
import shutil
import sys
import threading
from datetime import datetime
from pathlib import Path

import customtkinter as ctk
import pandas as pd
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from tkinter import filedialog, messagebox, ttk

import machote_generator as mg

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "app_data"
CONFIG_PATH = DATA_DIR / "config.json"
HISTORY_PATH = DATA_DIR / "history.json"

os.chdir(BASE_DIR)
DATA_DIR.mkdir(exist_ok=True)

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CURRENT_THEME = {
    "bg": "#0F1A12",
    "panel": "#17271B",
    "panel_alt": "#203423",
    "gold": "#D7B56D",
    "gold_hover": "#C59C43",
    "forest": "#3E6B45",
    "forest_hover": "#50895A",
    "emerald": "#4FAF6D",
    "text": "#F3ECD2",
    "muted": "#A8A088",
    "danger": "#A64B3C",
    "danger_hover": "#8B3C31",
    "warning": "#B88A3B",
    "sky": "#6AA7A5",
}

HW_THEME = {
    "bg": "#121212",        # Almost black background
    "panel": "#1E1E1E",     # Dark gray panel
    "panel_alt": "#2C2C2C", # Lighter gray panel
    "gold": "#FF3B30",      # Honey Whale Red/Orange accent
    "gold_hover": "#D32F2F",# Darker Red
    "forest": "#424242",    # Gray instead of forest green
    "forest_hover": "#616161",
    "emerald": "#4CAF50",   # Green for success
    "text": "#FFFFFF",      # White text
    "muted": "#B0BEC5",     # Light gray muted text
    "danger": "#F44336",    # Red danger
    "danger_hover": "#D32F2F",
    "warning": "#FF9800",   # Orange warning
    "sky": "#2196F3",       # Blue
}

CURRENT_THEME = CURRENT_THEME.copy()

def update_theme_colors(theme_name):
    global CURRENT_THEME
    if theme_name == "HoneyWhale":
        CURRENT_THEME.update(HW_THEME)
    else:
        CURRENT_THEME.update(CURRENT_THEME)

DEFAULT_CONFIG = {
    "empresa_default": "MOVILIDAD ELECTRICA DE JALISCO",
    "cuenta_default": "MP",
    "rfc_default": "MEJ123456789",
    "theme_mode": "Dark",
    "tolerancia_resumen": 50,
    "logo_text": "MACHOTES OF TIME",
    "inventario_path": mg.PATH_INVENTARIO,
    "machote_path": mg.PATH_MACHOTE,
    "precios_path": mg.PATH_PRECIOS,
    "output_dir": mg.OUTPUT_DIR,
    "parse_warning_threshold": 3,
}


def format_color_for_display(color_value):
    color = str(color_value or "").strip().upper()
    if not color:
        return ""
    return " / ".join(part.strip() for part in color.replace("-", "/").split("/") if part.strip())


class MultiSelectMenu(ctk.CTkButton):
    def __init__(self, master, title="Seleccionar", values=None, command=None, **kwargs):
        super().__init__(master, text=title, **kwargs)
        self.values = values or []
        self.command = command
        self.variables = {}
        self.dropdown = None
        self._title = title
        self.configure(command=self.toggle_dropdown)
        self.set_values(self.values)

    def set_values(self, values):
        old_vars = self.variables
        self.values = values
        self.variables = {}
        for val in values:
            if val in old_vars:
                self.variables[val] = old_vars[val]
            else:
                self.variables[val] = ctk.IntVar(value=1)
        self.update_text()

    def get(self):
        return [val for val, var in self.variables.items() if var.get() == 1]

    def update_text(self):
        selected = len(self.get())
        total = len(self.values)
        if selected == total:
            self.configure(text=f"{self._title} (Todos)")
        elif selected == 0:
            self.configure(text=f"{self._title} (Ninguno)")
        else:
            self.configure(text=f"{self._title} ({selected})")

    def toggle_dropdown(self):
        if self.dropdown is not None and self.dropdown.winfo_exists():
            self.dropdown.destroy()
            self.dropdown = None
            self.update_text()
            if self.command:
                self.command()
        else:
            self.dropdown = ctk.CTkToplevel(self)
            self.dropdown.overrideredirect(True)
            self.dropdown.attributes('-topmost', True)
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            self.dropdown.geometry(f"+{int(x)}+{int(y)}")

            main_frame = ctk.CTkFrame(self.dropdown, fg_color=CURRENT_THEME["panel"], border_color=CURRENT_THEME["gold"], border_width=1)
            main_frame.pack(fill="both", expand=True)

            # Search entry
            self.search_var = ctk.StringVar()
            self.search_var.trace("w", self._filter_options)
            search_entry = ctk.CTkEntry(main_frame, textvariable=self.search_var, placeholder_text="Buscar...", height=28)
            search_entry.pack(fill="x", padx=10, pady=(10, 5))

            # Scrollable options frame
            self.options_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent", width=200, height=200)
            self.options_frame.pack(fill="both", expand=True)

            # Buttons frame
            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(fill="x", pady=5, padx=5)
            def select_all():
                for cb, val in self.checkboxes:
                    if cb.winfo_ismapped():
                        self.variables[val].set(1)
            def deselect_all():
                for cb, val in self.checkboxes:
                    if cb.winfo_ismapped():
                        self.variables[val].set(0)
            def select_visible_only():
                for cb, val in self.checkboxes:
                    self.variables[val].set(1 if cb.winfo_ismapped() else 0)
            def close_dropdown():
                self.toggle_dropdown()

            ctk.CTkButton(btn_frame, text="Todo", width=50, height=24, command=select_all, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["forest_hover"]).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Nada", width=50, height=24, command=deselect_all, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["danger_hover"]).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Solo visibles", width=90, height=24, command=select_visible_only, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["gold_hover"]).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Cerrar", width=50, height=24, command=close_dropdown, fg_color=CURRENT_THEME["gold"], text_color="#0D0D12", hover_color=CURRENT_THEME["gold_hover"]).pack(side="right", padx=2)

            self.checkboxes = []
            for val in self.values:
                cb = ctk.CTkCheckBox(self.options_frame, text=val, variable=self.variables[val], onvalue=1, offvalue=0, fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], text_color=CURRENT_THEME["text"])
                cb.pack(anchor="w", padx=10, pady=5)
                self.checkboxes.append((cb, val))

    def _filter_options(self, *args):
        query = self.search_var.get().lower()
        for cb, val in self.checkboxes:
            if query in val.lower():
                if not cb.winfo_ismapped():
                    cb.pack(anchor="w", padx=10, pady=5)
            else:
                if cb.winfo_ismapped():
                    cb.pack_forget()

class RedirectText:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, string):
        self.textbox.insert("end", string)
        self.textbox.see("end")

    def flush(self):
        return None


class ZeldaTree(ttk.Treeview):
    pass


class TreeBundle:
    def __init__(self, frame, tree):
        self._frame = frame
        self._tree = tree

    def __getattr__(self, name):
        return getattr(self._tree, name)

    def grid(self, *args, **kwargs):
        return self._frame.grid(*args, **kwargs)

    def pack(self, *args, **kwargs):
        return self._frame.pack(*args, **kwargs)

    def place(self, *args, **kwargs):
        return self._frame.place(*args, **kwargs)


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


class BaseView(ctk.CTkFrame):
    title = ""
    subtitle = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=self.title, font=ctk.CTkFont(size=28, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(header, text=self.subtitle, font=ctk.CTkFont(size=13), text_color=CURRENT_THEME["text"]).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))
        return header


class DashboardView(BaseView):
    title = "Santuario del Reino"
    subtitle = "Vista general del inventario, hallazgos y señales clave del negocio."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(3, weight=1)
        self.metric_labels = {}
        self.chart_canvas = None
        self.summary_tree = None

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        self.filter_var = ctk.StringVar(value="Todos")
        self.segment = ctk.CTkSegmentedButton(controls, values=["Todos", "Disponibles", "Usados", "XML"], variable=self.filter_var, command=lambda _: self.refresh(), selected_color=CURRENT_THEME["gold"], selected_hover_color=CURRENT_THEME["gold_hover"], unselected_color=CURRENT_THEME["panel_alt"], unselected_hover_color=CURRENT_THEME["panel"])
        self.segment.pack(anchor="w")
        ctk.CTkButton(controls, text="Exportar Dashboard", width=150, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["gold_hover"], command=self.export_dashboard_snapshot).pack(anchor="e")
        period_row = ctk.CTkFrame(controls, fg_color="transparent")
        period_row.pack(anchor="w", pady=(8, 0))
        ctk.CTkLabel(period_row, text="Periodo:", text_color=CURRENT_THEME["muted"]).pack(side="left", padx=(0, 8))
        self.period_var = ctk.StringVar(value="Todo")
        self.custom_range = None
        self.period_segment = ctk.CTkSegmentedButton(
            period_row,
            values=["Todo", "Hoy", "7d", "30d", "90d", "Rango"],
            variable=self.period_var,
            command=self.on_period_change,
            selected_color=CURRENT_THEME["gold"],
            selected_hover_color=CURRENT_THEME["gold_hover"],
            unselected_color=CURRENT_THEME["panel_alt"],
            unselected_hover_color=CURRENT_THEME["panel"],
        )
        self.period_segment.pack(side="left")
        ctk.CTkLabel(period_row, text="Desde:", text_color=CURRENT_THEME["muted"]).pack(side="left", padx=(14, 4))
        self.from_date_entry = ctk.CTkEntry(period_row, width=105, placeholder_text="YYYY-MM-DD")
        self.from_date_entry.pack(side="left", padx=(0, 6))
        ctk.CTkLabel(period_row, text="Hasta:", text_color=CURRENT_THEME["muted"]).pack(side="left", padx=(4, 4))
        self.to_date_entry = ctk.CTkEntry(period_row, width=105, placeholder_text="YYYY-MM-DD")
        self.to_date_entry.pack(side="left", padx=(0, 6))
        ctk.CTkButton(period_row, text="Aplicar rango", width=110, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["gold_hover"], command=self.apply_custom_range).pack(side="left", padx=(4, 0))
        ctk.CTkButton(period_row, text="Limpiar", width=80, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"], command=self.clear_custom_range).pack(side="left", padx=(6, 0))

        metrics = ctk.CTkFrame(self, fg_color="transparent")
        metrics.grid(row=2, column=0, sticky="ew", padx=18)
        for idx in range(4):
            metrics.grid_columnconfigure(idx, weight=1)

        self._metric_card(metrics, 0, "Rupias Totales", "$0.00", "total")
        self._metric_card(metrics, 1, "Reliquias Activas", "0", "pieces")
        self._metric_card(metrics, 2, "Participación Rubro", "0%", "share")
        self._metric_card(metrics, 3, "Ticket Promedio", "$0.00", "avg")
        self.compare_label = ctk.CTkLabel(self, text="Comparativo: sin periodo seleccionado.", text_color=CURRENT_THEME["muted"])
        self.compare_label.grid(row=2, column=0, sticky="e", padx=24, pady=(94, 0))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=3, column=0, sticky="nsew", padx=18, pady=(12, 18))
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)

        chart_card = ctk.CTkFrame(content, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        chart_card.grid_rowconfigure(1, weight=1)
        chart_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(chart_card, text="Mapa de Sucursales", font=ctk.CTkFont(size=18, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))
        self.chart_container = ctk.CTkFrame(chart_card, fg_color="transparent")
        self.chart_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        summary_card = ctk.CTkFrame(content, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        summary_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        summary_card.grid_rowconfigure(1, weight=1)
        summary_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(summary_card, text="Resumen por Sucursal", font=ctk.CTkFont(size=18, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))
        self.summary_tree = self.app.create_treeview(summary_card, [
            ("sucursal", "Sucursal", 160),
            ("cantidad", "Cantidad", 100),
            ("porcentaje", "% del total", 110),
            ("total", "Total", 140),
        ])
        self.summary_tree.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def _metric_card(self, parent, column, title, value, key):
        card = ctk.CTkFrame(parent, fg_color=CURRENT_THEME["panel_alt"], corner_radius=16, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=0, column=column, sticky="ew", padx=6)
        ctk.CTkLabel(card, text=title, text_color=CURRENT_THEME["muted"], font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(12, 0))
        label = ctk.CTkLabel(card, text=value, text_color=CURRENT_THEME["text"], font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(anchor="w", padx=16, pady=(2, 14))
        self.metric_labels[key] = label

    def refresh(self):
        inventory = self.app.get_inventory_data(refresh=False)
        if not inventory:
            return

        rep_df = self._filter_by_period(inventory.get("reporte"))
        us_df = self._filter_by_period(inventory.get("usados"))
        xml_df = self._filter_by_period(inventory.get("xml"))

        dfs = []
        filtro = self.filter_var.get()
        if filtro in ["Todos", "Disponibles"]: dfs.append(rep_df)
        if filtro in ["Todos", "Usados"]: dfs.append(us_df)
        if filtro in ["Todos", "XML"]: dfs.append(xml_df)

        total_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True) if any(not df.empty for df in dfs) else pd.DataFrame()
        total_money = pd.to_numeric(total_df.get("TOTAL", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not total_df.empty else 0
        total_pieces = len(total_df)

        global_total = len(rep_df) + len(us_df) + len(xml_df)
        share = (total_pieces / global_total * 100) if global_total else 0
        avg_ticket = (total_money / total_pieces) if total_pieces else 0

        self.metric_labels["total"].configure(text=f"${total_money:,.2f}")
        self.metric_labels["pieces"].configure(text=str(total_pieces))

        self.metric_labels["share"].configure(text=f"{share:.1f}%")
        if share < 25:
            self.metric_labels["share"].configure(text_color=CURRENT_THEME["danger"])
        elif share < 60:
            self.metric_labels["share"].configure(text_color=CURRENT_THEME["warning"])
        else:
            self.metric_labels["share"].configure(text_color=CURRENT_THEME["emerald"])

        self.metric_labels["avg"].configure(text=f"${avg_ticket:,.2f}")
        self._update_period_comparison(inventory, filtro, total_money, total_pieces)

        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        if not total_df.empty and "SUCURSAL" in total_df.columns:
            top = total_df.copy()
            top["TOTAL"] = pd.to_numeric(top.get("TOTAL", 0), errors="coerce").fillna(0)
            top = top.groupby("SUCURSAL", as_index=False).agg(
                CANTIDAD=("SUCURSAL", "size"),
                TOTAL=("TOTAL", "sum")
            ).sort_values("TOTAL", ascending=False)

            total_count = top["CANTIDAD"].sum() if not top.empty else 0
            for _, row in top.iterrows():
                pct = (row["CANTIDAD"] / total_count * 100) if total_count else 0
                self.summary_tree.insert("", "end", values=(row["SUCURSAL"], str(row["CANTIDAD"]), f"{pct:.1f}%", f"${row['TOTAL']:,.2f}"))

        self.draw_chart(total_df)

    def on_period_change(self, selected_period):
        now = pd.Timestamp.now().normalize()
        if selected_period == "Hoy":
            start = now
            end = now
            self.from_date_entry.delete(0, "end")
            self.from_date_entry.insert(0, start.strftime("%Y-%m-%d"))
            self.to_date_entry.delete(0, "end")
            self.to_date_entry.insert(0, end.strftime("%Y-%m-%d"))
        elif selected_period in {"7d", "30d", "90d"}:
            days = int(selected_period.replace("d", ""))
            start = now - pd.Timedelta(days=days)
            end = now
            self.from_date_entry.delete(0, "end")
            self.from_date_entry.insert(0, start.strftime("%Y-%m-%d"))
            self.to_date_entry.delete(0, "end")
            self.to_date_entry.insert(0, end.strftime("%Y-%m-%d"))
        elif selected_period == "Todo":
            self.custom_range = None
            self.from_date_entry.delete(0, "end")
            self.to_date_entry.delete(0, "end")
        self.refresh()

    def apply_custom_range(self):
        start_str = self.from_date_entry.get().strip()
        end_str = self.to_date_entry.get().strip()
        if not start_str or not end_str:
            messagebox.showwarning("Rango incompleto", "Ingresa fecha inicial y final en formato YYYY-MM-DD.")
            return
        try:
            start = pd.to_datetime(start_str, format="%Y-%m-%d")
            end = pd.to_datetime(end_str, format="%Y-%m-%d")
        except Exception:
            messagebox.showwarning("Formato inválido", "Usa formato YYYY-MM-DD. Ejemplo: 2026-03-24")
            return
        if end < start:
            messagebox.showwarning("Rango inválido", "La fecha final no puede ser menor que la inicial.")
            return
        self.custom_range = (start.normalize(), end.normalize() + pd.Timedelta(days=1) - pd.Timedelta(seconds=1))
        self.period_var.set("Rango")
        self.refresh()

    def clear_custom_range(self):
        self.custom_range = None
        self.from_date_entry.delete(0, "end")
        self.to_date_entry.delete(0, "end")
        if self.period_var.get() == "Rango":
            self.period_var.set("Todo")
        self.refresh()

    def _filter_by_period(self, df):
        if df is None or df.empty:
            return pd.DataFrame() if df is None else df
        period = self.period_var.get()
        if period == "Todo":
            return df
        if "FECHA ACTUALIZACION" not in df.columns:
            return df
        now = pd.Timestamp.now()
        if period == "Hoy":
            start = now.normalize()
            end = start + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            fechas = pd.to_datetime(df["FECHA ACTUALIZACION"], errors="coerce")
            return df[(fechas >= start) & (fechas <= end)]
        if period == "Rango":
            if not self.custom_range:
                return df
            start, end = self.custom_range
            fechas = pd.to_datetime(df["FECHA ACTUALIZACION"], errors="coerce")
            return df[(fechas >= start) & (fechas <= end)]

        days_map = {"7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(period)
        if not days:
            return df
        tmp = df.copy()
        fechas = pd.to_datetime(tmp["FECHA ACTUALIZACION"], errors="coerce")
        cutoff = now - pd.Timedelta(days=days)
        return tmp[fechas >= cutoff]

    def _get_period_bounds(self):
        now = pd.Timestamp.now()
        period = self.period_var.get()
        if period == "Todo":
            return None
        if period == "Hoy":
            start = now.normalize()
            end = start + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
            return start, end
        if period in {"7d", "30d", "90d"}:
            days = int(period.replace("d", ""))
            end = now
            start = end - pd.Timedelta(days=days)
            return start, end
        if period == "Rango" and self.custom_range:
            return self.custom_range
        return None

    def _filter_by_bounds(self, df, bounds):
        if df is None or df.empty:
            return pd.DataFrame() if df is None else df
        if "FECHA ACTUALIZACION" not in df.columns:
            return df
        start, end = bounds
        fechas = pd.to_datetime(df["FECHA ACTUALIZACION"], errors="coerce")
        return df[(fechas >= start) & (fechas <= end)]

    def _update_period_comparison(self, inventory, filtro, current_money, current_pieces):
        bounds = self._get_period_bounds()
        if not bounds:
            self.compare_label.configure(text="Comparativo: selecciona Hoy/7d/30d/90d/Rango.", text_color=CURRENT_THEME["muted"])
            return
        start, end = bounds
        duration = end - start
        prev_end = start - pd.Timedelta(seconds=1)
        prev_start = prev_end - duration
        prev_bounds = (prev_start, prev_end)

        rep_prev = self._filter_by_bounds(inventory.get("reporte"), prev_bounds)
        us_prev = self._filter_by_bounds(inventory.get("usados"), prev_bounds)
        xml_prev = self._filter_by_bounds(inventory.get("xml"), prev_bounds)
        dfs_prev = []
        if filtro in ["Todos", "Disponibles"]: dfs_prev.append(rep_prev)
        if filtro in ["Todos", "Usados"]: dfs_prev.append(us_prev)
        if filtro in ["Todos", "XML"]: dfs_prev.append(xml_prev)
        prev_df = pd.concat([df for df in dfs_prev if not df.empty], ignore_index=True) if any(not df.empty for df in dfs_prev) else pd.DataFrame()
        prev_money = pd.to_numeric(prev_df.get("TOTAL", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not prev_df.empty else 0
        prev_pieces = len(prev_df)

        def pct_delta(curr, prev):
            if prev == 0:
                return 100.0 if curr > 0 else 0.0
            return ((curr - prev) / prev) * 100

        delta_money = pct_delta(current_money, prev_money)
        delta_pieces = pct_delta(current_pieces, prev_pieces)
        money_sign = "+" if delta_money >= 0 else ""
        pieces_sign = "+" if delta_pieces >= 0 else ""
        color = CURRENT_THEME["emerald"] if delta_money >= 0 and delta_pieces >= 0 else CURRENT_THEME["warning"]
        self.compare_label.configure(
            text=f"Vs periodo anterior → Piezas: {pieces_sign}{delta_pieces:.1f}% · Total: {money_sign}{delta_money:.1f}%",
            text_color=color,
        )

    def export_dashboard_snapshot(self):
        out_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("PDF", "*.pdf")],
            title="Exportar Dashboard (Excel/PDF)",
            initialfile="Dashboard_Resumen.xlsx",
        )
        if not out_path:
            return
        try:
            kpis = {
                "Rupias Totales": self.metric_labels["total"].cget("text"),
                "Reliquias Activas": self.metric_labels["pieces"].cget("text"),
                "Participación Rubro": self.metric_labels["share"].cget("text"),
                "Ticket Promedio": self.metric_labels["avg"].cget("text"),
                "Comparativo": self.compare_label.cget("text"),
            }
            filters = {
                "Filtro estado": self.filter_var.get(),
                "Periodo": self.period_var.get(),
                "Desde": self.from_date_entry.get() or "-",
                "Hasta": self.to_date_entry.get() or "-",
                "Exportado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            rows = []
            for item_id in self.summary_tree.get_children():
                values = self.summary_tree.item(item_id, "values")
                rows.append(values)
            summary_df = pd.DataFrame(rows, columns=["Sucursal", "Cantidad", "% del total", "Total"])
            kpi_df = pd.DataFrame([kpis])
            filters_df = pd.DataFrame([filters])

            if out_path.lower().endswith(".pdf"):
                self._export_dashboard_pdf(out_path, kpi_df, summary_df, filters_df)
            else:
                with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                    kpi_df.to_excel(writer, sheet_name="KPIs", index=False)
                    summary_df.to_excel(writer, sheet_name="Sucursales", index=False)
                    filters_df.to_excel(writer, sheet_name="Filtros", index=False)
            self.app.log(f"Dashboard exportado: {out_path}")
            messagebox.showinfo("Exportación completada", f"Dashboard exportado en:\n{out_path}")
        except Exception as exc:
            self.app.log(f"Error exportando dashboard: {exc}")
            import traceback
            self.app.log(traceback.format_exc())
            messagebox.showerror("Error exportando", f"No se pudo exportar dashboard.\n\n{exc}")

    def _export_dashboard_pdf(self, out_path, kpi_df, summary_df, filters_df):
        with PdfPages(out_path) as pdf:
            fig1 = Figure(figsize=(8.27, 11.69), dpi=120, facecolor="white")
            ax1 = fig1.add_subplot(111)
            ax1.axis("off")
            ax1.text(0.03, 0.97, "Dashboard - Resumen", fontsize=16, fontweight="bold", va="top")

            y = 0.90
            for col in filters_df.columns:
                val = str(filters_df.iloc[0][col])
                ax1.text(0.03, y, f"{col}: {val}", fontsize=10, va="top")
                y -= 0.04

            y -= 0.02
            ax1.text(0.03, y, "KPIs", fontsize=12, fontweight="bold", va="top")
            y -= 0.03
            for col in kpi_df.columns:
                val = str(kpi_df.iloc[0][col])
                ax1.text(0.03, y, f"{col}: {val}", fontsize=10, va="top")
                y -= 0.04
            pdf.savefig(fig1, bbox_inches="tight")

            fig2 = Figure(figsize=(11.69, 8.27), dpi=120, facecolor="white")
            ax2 = fig2.add_subplot(111)
            ax2.axis("off")
            ax2.text(0.01, 0.98, "Dashboard - Resumen por sucursal", fontsize=14, fontweight="bold", va="top")
            if summary_df.empty:
                ax2.text(0.01, 0.90, "No hay datos visibles para exportar con los filtros/rango actuales.", fontsize=10, va="top")
            else:
                table = ax2.table(
                    cellText=summary_df.values.tolist(),
                    colLabels=summary_df.columns.tolist(),
                    loc="upper left",
                    cellLoc="left",
                    colLoc="left",
                    bbox=[0.01, 0.05, 0.98, 0.88],
                )
                table.auto_set_font_size(False)
                table.set_fontsize(9)
            pdf.savefig(fig2, bbox_inches="tight")

    def draw_chart(self, total_df):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(5.4, 4.2), dpi=100, facecolor=CURRENT_THEME["panel"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(CURRENT_THEME["panel"])

        if not total_df.empty and "SUCURSAL" in total_df.columns:
            counts_all = total_df["SUCURSAL"].fillna("SIN SUCURSAL").value_counts()
            counts = counts_all.head(5)
            if len(counts_all) > 5:
                counts.loc["OTROS"] = counts_all.iloc[5:].sum()
            colors = [CURRENT_THEME["gold"], CURRENT_THEME["forest"], CURRENT_THEME["emerald"], CURRENT_THEME["sky"], CURRENT_THEME["warning"], CURRENT_THEME["danger"]]
            ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=90, colors=colors[: len(counts)], textprops={"color": CURRENT_THEME["text"], "fontsize": 10})
            ax.set_title("Distribución por Sucursal (Top 5 + Otros)", color=CURRENT_THEME["gold"], fontsize=14)
        else:
            ax.text(0.5, 0.5, "No hay datos aún", color=CURRENT_THEME["text"], ha="center", va="center")
            ax.axis("off")

        fig.tight_layout()
        self.chart_canvas = FigureCanvasTkAgg(fig, master=self.chart_container)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True)


class InventoryView(BaseView):
    title = "Salón del Inventario"
    subtitle = "Explora, filtra y exporta las piezas disponibles, usadas y facturadas."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(3, weight=1)
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        controls.grid_columnconfigure(3, weight=1)

        self.sucursal_opt = MultiSelectMenu(controls, title="Sucursal", values=[], command=self.refresh, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"])
        self.sucursal_opt.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.modelo_opt = MultiSelectMenu(controls, title="Modelo", values=[], command=self.refresh, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"])
        self.modelo_opt.grid(row=0, column=1, padx=(0, 10), sticky="w")

        ctk.CTkLabel(controls, text="Buscar:", text_color=CURRENT_THEME["text"]).grid(row=0, column=2, padx=(0, 10), sticky="w")
        self.search_entry = ctk.CTkEntry(controls, placeholder_text="serie, color...")
        self.search_entry.grid(row=0, column=3, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda _e: self.refresh())
        ctk.CTkButton(controls, text="X Filtros", fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], command=self.clear_filters).grid(row=0, column=4, padx=(10, 0))
        self.active_filters_label = ctk.CTkLabel(controls, text="Filtros activos: 0", text_color=CURRENT_THEME["muted"])
        self.active_filters_label.grid(row=0, column=8, padx=(12, 0), sticky="e")

        ctk.CTkButton(controls, text="Exportar Excel Completo", fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", command=self.export_full_excel).grid(row=0, column=5, padx=(10, 0))
        ctk.CTkButton(controls, text="Exportar Vista", fg_color=CURRENT_THEME["emerald"], hover_color=CURRENT_THEME["forest_hover"], command=self.export_view).grid(row=0, column=6, padx=10)
        ctk.CTkButton(controls, text="Recargar", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=lambda: self.app.refresh_data(force=True)).grid(row=0, column=7)

        totals_frame = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel_alt"], corner_radius=8)
        totals_frame.grid(row=2, column=0, sticky="ew", padx=18)
        self.lbl_totals = ctk.CTkLabel(totals_frame, text="0 piezas visibles · Total: $0.00", text_color=CURRENT_THEME["gold"], font=ctk.CTkFont(weight="bold"))
        self.lbl_totals.pack(padx=14, pady=6, anchor="e")

        self.tabview = ctk.CTkTabview(self, fg_color=CURRENT_THEME["panel"], segmented_button_selected_color=CURRENT_THEME["gold"], segmented_button_selected_hover_color=CURRENT_THEME["gold_hover"], segmented_button_unselected_color=CURRENT_THEME["panel_alt"], command=self.refresh_totals)
        self.tabview.grid(row=3, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.trees = {}
        for tab_name in ["Disponibles", "Usados", "XML"]:
            tab = self.tabview.add(tab_name)
            tab.grid_rowconfigure(0, weight=1)
            tab.grid_columnconfigure(0, weight=1)
            tree = self.app.create_treeview(tab, [
                ("sucursal", "Sucursal", 110),
                ("modelo", "Modelo", 150),
                ("color", "Color", 100),
                ("serie", "Serie", 180),
                ("total", "Total", 120),
                ("extra", "Extra", 180),
            ])
            tree.grid(row=0, column=0, sticky="nsew", padx=8, pady=8)
            self.trees[tab_name] = tree

    def _update_options(self, inventory):
        dfs = [df for df in [inventory.get("reporte"), inventory.get("usados"), inventory.get("xml")] if df is not None and not df.empty]
        total_df = pd.concat(dfs) if dfs else pd.DataFrame()
        if total_df.empty:
            return
        has_suc = "SUCURSAL" in total_df.columns
        has_mod = "MODELO BASE" in total_df.columns
        if not (has_suc and has_mod):
            if has_suc:
                sucursales = sorted([str(x) for x in total_df["SUCURSAL"].dropna().unique() if str(x).strip()])
                self.sucursal_opt.set_values(sucursales)
            if has_mod:
                modelos = sorted([str(x) for x in total_df["MODELO BASE"].dropna().unique() if str(x).strip()])
                self.modelo_opt.set_values(modelos)
            return

        selected_sucs = set(self.sucursal_opt.get())
        selected_mods = set(self.modelo_opt.get())

        all_sucs_df = set(str(x) for x in total_df["SUCURSAL"].dropna().tolist() if str(x).strip())
        all_mods_df = set(str(x) for x in total_df["MODELO BASE"].dropna().tolist() if str(x).strip())

        # Si no hay selección explícita o está todo seleccionado, no filtra esa dimensión.
        suc_filter = selected_sucs if selected_sucs and selected_sucs != set(self.sucursal_opt.values) else None
        mod_filter = selected_mods if selected_mods and selected_mods != set(self.modelo_opt.values) else None

        df_for_models = total_df if suc_filter is None else total_df[total_df["SUCURSAL"].astype(str).isin(suc_filter)]
        df_for_sucs = total_df if mod_filter is None else total_df[total_df["MODELO BASE"].astype(str).isin(mod_filter)]

        modelos = sorted([str(x) for x in df_for_models["MODELO BASE"].dropna().unique() if str(x).strip()])
        sucursales = sorted([str(x) for x in df_for_sucs["SUCURSAL"].dropna().unique() if str(x).strip()])

        self.modelo_opt.set_values(modelos if modelos else sorted(all_mods_df))
        self.sucursal_opt.set_values(sucursales if sucursales else sorted(all_sucs_df))

    def clear_filters(self):
        self.search_entry.delete(0, "end")
        self.sucursal_opt.set_values(self.sucursal_opt.values)
        self.modelo_opt.set_values(self.modelo_opt.values)
        for var in self.sucursal_opt.variables.values():
            var.set(1)
        for var in self.modelo_opt.variables.values():
            var.set(1)
        self.refresh()

    def _update_active_filters_badge(self):
        active = 0
        if self.sucursal_opt.values and len(self.sucursal_opt.get()) != len(self.sucursal_opt.values):
            active += 1
        if self.modelo_opt.values and len(self.modelo_opt.get()) != len(self.modelo_opt.values):
            active += 1
        if self.search_entry.get().strip():
            active += 1
        color = CURRENT_THEME["gold"] if active > 0 else CURRENT_THEME["muted"]
        self.active_filters_label.configure(text=f"Filtros activos: {active}", text_color=color)

    def export_full_excel(self):
        import db_export
        from datetime import datetime

        out_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            title="Exportar Inventario Completo",
            initialfile=f"Inventario_Completo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        )
        if not out_path:
            return

        self.app.log("Generando reporte completo del inventario en segundo plano...")
        self.lbl_totals.configure(text="Generando Excel completo...", text_color=CURRENT_THEME["warning"])

        def _task():
            try:
                db_export.export_inventory_to_excel(out_path)
                self.app.after(0, self._export_full_success, out_path)
            except Exception as e:
                self.app.after(0, self._export_full_error, e)

        self.app.run_in_thread(_task)

    def _export_full_success(self, path):
        self.app.log(f"Inventario completo exportado exitosamente a {path}")
        messagebox.showinfo("Exportado", f"Inventario completo generado correctamente en:\n{path}")
        self.refresh_totals() # Restore label

    def _export_full_error(self, exc):
        import traceback
        self.app.log(f"Error generando exportacion completa:\n{traceback.format_exc()}")
        messagebox.showerror("Error exportando", f"No se pudo generar el archivo.\n\n{exc}")
        self.refresh_totals()

    def export_view(self):
        current_tab = self.tabview.get()
        tree = self.trees[current_tab]
        rows = []
        for item in tree.get_children():
            rows.append(tree.item(item)["values"])
        if not rows:
            messagebox.showwarning("Aviso", "La vista está vacía. No hay nada que exportar.")
            return
        import pandas as pd
        cols = ["Sucursal", "Modelo", "Color", "Serie", "Total", "Extra"]
        df = pd.DataFrame(rows, columns=cols)
        out_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], title="Exportar Vista", initialfile=f"Vista_{current_tab}.xlsx")
        if out_path:
            df.to_excel(out_path, index=False)
            self.app.log(f"Vista exportada: {out_path}")
            messagebox.showinfo("Exportado", f"Archivo creado:\n{out_path}")

    def refresh(self):
        inventory = self.app.get_inventory_data(refresh=False)
        if not inventory:
            return
        self._update_options(inventory)
        mapping = {
            "Disponibles": (inventory["reporte"], None),
            "Usados": (inventory["usados"], "MACHOTE"),
            "XML": (inventory["xml"], "UUID"),
        }
        term = self.search_entry.get().strip().lower()
        self._update_active_filters_badge()
        sucursal_filter = set(self.sucursal_opt.get())
        modelo_filter = set(self.modelo_opt.get())
        all_sucs = set(self.sucursal_opt.values)
        all_mods = set(self.modelo_opt.values)

        for name, (df, extra_col) in mapping.items():
            tree = self.trees[name]
            for item in tree.get_children():
                tree.delete(item)
            if df is None or df.empty:
                continue
            for _, row in df.iterrows():
                suc_val = str(row.get("SUCURSAL", ""))
                mod_val = str(row.get("MODELO BASE", ""))
                if sucursal_filter != all_sucs and suc_val not in sucursal_filter:
                    continue
                if modelo_filter != all_mods and mod_val not in modelo_filter:
                    continue
                serie = str(row.get("No de SERIE:", ""))
                values = [
                    suc_val,
                    mod_val,
                    format_color_for_display(row.get("COLOR", "")),
                    serie,
                    self.app.money(row.get("TOTAL", 0)),
                    str(row.get(extra_col, "")) if extra_col and extra_col in df.columns else "",
                ]
                haystack = " ".join(values).lower()
                if not term or term in haystack:
                    tree.insert("", "end", values=values)
        self.refresh_totals()

    def refresh_totals(self):
        import math
        current_tab = self.tabview.get()
        tree = self.trees[current_tab]
        count = 0
        total_val = 0.0
        for item in tree.get_children():
            count += 1
            val_str = tree.item(item)["values"][4]
            try:
                val = float(str(val_str).replace("$", "").replace(",", ""))
                if not math.isnan(val):
                    total_val += val
            except Exception:
                pass
        self.lbl_totals.configure(text=f"{count} piezas visibles · Total: ${total_val:,.2f}")

class GeneratorView(BaseView):
    title = "Forja del Machote"
    subtitle = "Calcula una combinación inteligente, revísala y expórtala como si fuera una reliquia sagrada."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.preview_df = pd.DataFrame()
        self.create_header()

        top = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        top.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        for i in range(4):
            top.grid_columnconfigure(i, weight=1)

        self.amount_entry = self._entry(top, 0, 0, "Monto objetivo", "150000")
        self.company_entry = self._entry(top, 0, 1, "Empresa", self.app.app_state.config.get("empresa_default", ""))
        self.account_entry = self._entry(top, 0, 2, "Cuenta", self.app.app_state.config.get("cuenta_default", "MP"))
        self.rfc_entry = self._entry(top, 0, 3, "RFC (opcional)", self.app.app_state.config.get("rfc_default", ""))
        self.company_options = []
        company_tools = ctk.CTkFrame(self.company_entry.master, fg_color="transparent")
        company_tools.pack(fill="x", pady=(6, 0))
        combo_values = ["Elegir empresa CSF...", "(Sin CSF detectados)"]
        self.company_combo = ctk.CTkComboBox(
            company_tools,
            values=combo_values,
            command=self.on_company_selected,
            state="readonly",
        )
        self.company_combo.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            company_tools,
            text="Recargar",
            width=90,
            fg_color=CURRENT_THEME["panel_alt"],
            hover_color=CURRENT_THEME["gold_hover"],
            command=self.refresh_company_options,
        ).pack(side="left", padx=(6, 0))
        self.company_combo.set("Elegir empresa CSF...")
        self.refresh_company_options()

        filter_frame = ctk.CTkFrame(top, fg_color="transparent")
        filter_frame.grid(row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=10)
        self.include_children = ctk.CTkSwitch(filter_frame, text="Incluir infantiles", progress_color=CURRENT_THEME["gold"], command=self._update_active_filters_badge)
        self.include_children.pack(side="left", padx=12)
        self.include_motor = ctk.CTkSwitch(filter_frame, text="Incluir motocicletas", progress_color=CURRENT_THEME["gold"], command=self._update_active_filters_badge)
        self.include_motor.pack(side="left", padx=12)

        ctk.CTkLabel(filter_frame, text="Sucursal:", text_color=CURRENT_THEME["muted"]).pack(side="left", padx=(20, 5))
        self.sucursal_opt = MultiSelectMenu(filter_frame, title="Seleccionar", values=[], command=self.refresh, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"])
        self.sucursal_opt.pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="Modelo:", text_color=CURRENT_THEME["muted"]).pack(side="left", padx=(20, 5))
        self.modelo_opt = MultiSelectMenu(filter_frame, title="Seleccionar", values=[], command=self.refresh, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"])
        self.modelo_opt.pack(side="left", padx=5)
        ctk.CTkButton(filter_frame, text="X Filtros", width=90, fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], command=self.clear_filters).pack(side="left", padx=(10, 0))
        self.active_filters_label = ctk.CTkLabel(filter_frame, text="Filtros activos: 0", text_color=CURRENT_THEME["muted"])
        self.active_filters_label.pack(side="left", padx=(10, 0))

        controls = ctk.CTkFrame(top, fg_color="transparent")
        controls.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 12))
        ctk.CTkButton(controls, text="Previsualizar combinación", fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", command=self.calculate_preview).pack(side="left", padx=(0, 10))
        ctk.CTkButton(controls, text="Exportar machote", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.export_machote).pack(side="left")

        ctk.CTkButton(controls, text="Importar Machote Externo", fg_color=CURRENT_THEME["sky"], hover_color="#4F7C7A", command=self.import_external_machote).pack(side="right", padx=(10, 0))

        preview_card = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        preview_card.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        preview_card.grid_rowconfigure(1, weight=1)
        preview_card.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.preview_label = ctk.CTkLabel(preview_card, text="Aún no se ha invocado una combinación.", text_color=CURRENT_THEME["text"], font=ctk.CTkFont(size=16, weight="bold"))
        self.preview_label.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))
        self.preview_tree = self.app.create_treeview(preview_card, [
            ("sucursal", "Sucursal", 110),
            ("modelo", "Modelo", 150),
            ("serie", "Serie", 180),
            ("total", "Total", 120),
        ])
        self.preview_tree.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def refresh(self):
        inventory = self.app.get_inventory_data(refresh=False)
        if not inventory:
            return
        df_rep = inventory.get("reporte")
        if df_rep is not None and not df_rep.empty:
            self._update_correlated_options(df_rep)
        self._update_active_filters_badge()

    def _update_correlated_options(self, df_rep):
        if "SUCURSAL" not in df_rep.columns or "MODELO BASE" not in df_rep.columns:
            return

        selected_sucs = set(self.sucursal_opt.get())
        selected_mods = set(self.modelo_opt.get())
        current_suc_values = set(self.sucursal_opt.values)
        current_mod_values = set(self.modelo_opt.values)

        suc_filter = selected_sucs if selected_sucs and selected_sucs != current_suc_values else None
        mod_filter = selected_mods if selected_mods and selected_mods != current_mod_values else None

        df_for_models = df_rep if suc_filter is None else df_rep[df_rep["SUCURSAL"].astype(str).isin(suc_filter)]
        df_for_sucs = df_rep if mod_filter is None else df_rep[df_rep["MODELO BASE"].astype(str).isin(mod_filter)]

        modelos = sorted([str(x) for x in df_for_models["MODELO BASE"].dropna().unique() if str(x).strip()])
        sucursales = sorted([str(x) for x in df_for_sucs["SUCURSAL"].dropna().unique() if str(x).strip()])

        if not modelos:
            modelos = sorted([str(x) for x in df_rep["MODELO BASE"].dropna().unique() if str(x).strip()])
        if not sucursales:
            sucursales = sorted([str(x) for x in df_rep["SUCURSAL"].dropna().unique() if str(x).strip()])

        self.modelo_opt.set_values(modelos)
        self.sucursal_opt.set_values(sucursales)

    def clear_filters(self):
        self.sucursal_opt.set_values(self.sucursal_opt.values)
        self.modelo_opt.set_values(self.modelo_opt.values)
        for var in self.sucursal_opt.variables.values():
            var.set(1)
        for var in self.modelo_opt.variables.values():
            var.set(1)
        self.preview_df = None
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self.preview_label.configure(text="Vista previa vacía. Define monto y filtros para consultar.", text_color=CURRENT_THEME["muted"])
        self.refresh()

    def _update_active_filters_badge(self):
        active = 0
        if self.sucursal_opt.values and len(self.sucursal_opt.get()) != len(self.sucursal_opt.values):
            active += 1
        if self.modelo_opt.values and len(self.modelo_opt.get()) != len(self.modelo_opt.values):
            active += 1
        if self.include_children.get() == 1:
            active += 1
        if self.include_motor.get() == 1:
            active += 1
        color = CURRENT_THEME["gold"] if active > 0 else CURRENT_THEME["muted"]
        self.active_filters_label.configure(text=f"Filtros activos: {active}", text_color=color)

    def _entry(self, parent, row, column, label, value=""):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=column, sticky="ew", padx=10, pady=(12, 0))
        ctk.CTkLabel(frame, text=label, text_color=CURRENT_THEME["muted"]).pack(anchor="w")
        entry = ctk.CTkEntry(frame)
        entry.pack(fill="x", pady=(4, 0))
        if value:
            entry.insert(0, value)
        return entry

    def on_company_selected(self, selected_company):
        if not selected_company or selected_company.startswith("(Sin CSF") or selected_company.startswith("Elegir empresa"):
            return
        self.company_entry.delete(0, "end")
        self.company_entry.insert(0, selected_company)
        try:
            rfc, razon = mg.extraer_datos_empresa(selected_company)
            if razon:
                self.company_entry.delete(0, "end")
                self.company_entry.insert(0, razon)
            if rfc:
                self.rfc_entry.delete(0, "end")
                self.rfc_entry.insert(0, rfc)
            self.app.log(f"Empresa CSF seleccionada: {selected_company}")
        except Exception as exc:
            self.app.log(f"No se pudo autocompletar empresa/RFC desde CSF: {exc}")

    def refresh_company_options(self):
        self.company_options = mg.obtener_empresas_csf()
        values = ["Elegir empresa CSF..."] + (self.company_options if self.company_options else ["(Sin CSF detectados)"])
        self.company_combo.configure(values=values)
        self.company_combo.set("Elegir empresa CSF...")
        self.app.log(f"CSF detectados: {len(self.company_options)}")

    def calculate_preview(self):
        amount_text = self.amount_entry.get().replace(",", "").strip()
        if not amount_text:
            messagebox.showwarning("Monto requerido", "Ingresa un monto objetivo para forjar el machote.")
            return
        try:
            target = float(amount_text)
        except ValueError:
            messagebox.showwarning("Monto inválido", "El monto objetivo debe ser un número válido.")
            return

        inventory = self.app.get_inventory_data(refresh=False)
        if not inventory:
            return

        self.preview_label.configure(text="Calculando combinaciones posibles...", text_color=CURRENT_THEME["warning"])
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        suc_list = self.sucursal_opt.get()
        if len(suc_list) == len(self.sucursal_opt.values): suc_list = None
        mod_list = self.modelo_opt.get()
        if len(mod_list) == len(self.modelo_opt.values): mod_list = None

        inc_children = self.include_children.get() == 1
        inc_motor = self.include_motor.get() == 1

        def _task():
            try:
                df_available = mg.procesar_inventario(
                    inventory["reporte"],
                    inventory["precios"],
                    incluir_infantiles=inc_children,
                    incluir_motobicis=inc_motor,
                    sucursales=suc_list,
                    modelos=mod_list
                )
                preview = mg.seleccionar_articulos(df_available, target)
                self.app.after(0, self._calculate_success, preview, target)
            except Exception as exc:
                self.app.after(0, self._calculate_error, exc)

        self.app.run_in_thread(_task)

    def _calculate_success(self, preview, target):
        self.preview_df = preview
        self.app.app_state.last_preview = preview
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        total = pd.to_numeric(preview.get("TOTAL", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not preview.empty else 0
        diff = abs(total - target)
        self.preview_label.configure(text=f"Resultado: {len(preview)} piezas · {self.app.money(total)} · diferencia {self.app.money(diff)}", text_color=CURRENT_THEME["text"])

        for _, row in preview.iterrows():
            self.preview_tree.insert("", "end", values=(
                str(row.get("SUCURSAL", "")),
                str(row.get("MODELO BASE", "")),
                str(row.get("No de SERIE:", "")),
                self.app.money(row.get("TOTAL", 0)),
            ))

        self.app.log(f"Vista previa generada para ${target:,.2f} con {len(preview)} artículos.")

    def _calculate_error(self, exc):
        import traceback
        self.preview_label.configure(text="Error calculando vista previa.", text_color=CURRENT_THEME["danger"])
        self.app.log(f"Error en simulación:\n{traceback.format_exc()}")
        messagebox.showerror("Error calculando", f"No se pudo generar la vista previa.\n\n{exc}")

    def export_machote(self):
        if self.preview_df is None or self.preview_df.empty:
            messagebox.showwarning("Aviso", "Primero previsualiza una combinación antes de exportar.")
            return

        company = self.company_entry.get().strip() or self.app.app_state.config.get("empresa_default", "MOVILIDAD ELECTRICA DE JALISCO")
        account = self.account_entry.get().strip() or self.app.app_state.config.get("cuenta_default", "MP")
        rfc = self.rfc_entry.get().strip() or self.app.app_state.config.get("rfc_default", "MEJ123456789")
        target = float(self.amount_entry.get().replace(",", "").strip())

        self.app.log("Forjando machote en segundo plano...")
        self.preview_label.configure(text="Generando Excel y actualizando inventario...", text_color=CURRENT_THEME["warning"])

        def _task():
            try:
                route, file_name, inventory_path = mg.generar_machote_y_actualizar(
                    self.preview_df,
                    target,
                    company,
                    rfc,
                    account,
                )
                self.app.after(0, self._export_success, route, file_name, inventory_path, company, rfc, account)
            except Exception as exc:
                self.app.after(0, self._export_error, exc)

        self.app.run_in_thread(_task)

    def _export_success(self, route, file_name, inventory_path, company, rfc, account):
        self.preview_label.configure(text="Machote forjado con éxito.", text_color=CURRENT_THEME["emerald"])
        self.app.app_state.last_generated_file = route
        self.app.app_state.record_event(
            "machote",
            f"Machote generado: {file_name}",
            {
                "archivo": route,
                "inventario_actualizado": inventory_path,
                "empresa": company,
                "cuenta": account,
                "rfc": rfc,
                "piezas": len(self.preview_df),
            },
        )
        self.app.refresh_data(force=True)
        self.app.history_view.refresh()
        self.app.log(f"Machote exportado: {file_name}")
        messagebox.showinfo("Machote creado", f"Se generó correctamente:\n\n{route}\n\nInventario actualizado:\n{inventory_path}")

    def _export_error(self, exc):
        import traceback
        self.preview_label.configure(text="Error forjando machote.", text_color=CURRENT_THEME["danger"])
        self.app.log(f"Error en exportación:\n{traceback.format_exc()}")
        messagebox.showerror("Error exportando", f"No se pudo exportar el machote.\n\n{exc}")

    def import_external_machote(self):
        file_path = filedialog.askopenfilename(
            title="Seleccionar Machote Externo",
            filetypes=[("Excel", "*.xlsx *.xls")]
        )
        if not file_path:
            return

        self.app.log(f"Procesando machote externo: {file_path}")
        self.preview_label.configure(text="Cruzando series del machote externo...", text_color=CURRENT_THEME["warning"])

        def _task():
            try:
                coincidentes, detectadas = mg.importar_machote_externo(file_path)
                self.app.after(0, self._import_external_success, coincidentes, detectadas, file_path)
            except Exception as exc:
                self.app.after(0, self._import_external_error, exc)

        self.app.run_in_thread(_task)

    def _import_external_success(self, coincidentes, detectadas, file_path):
        import os
        filename = os.path.basename(file_path)
        if coincidentes:
            self.app.app_state.record_event(
                "machote_externo",
                f"Machote externo importado: {filename}",
                {"archivo": file_path, "series_detectadas": detectadas, "series_coincidentes": len(coincidentes)}
            )
            self.app.refresh_data(force=True)
            self.app.history_view.refresh()
            self.preview_label.configure(text=f"Importado: {len(coincidentes)}/{detectadas} series coinciden.", text_color=CURRENT_THEME["emerald"])
            self.app.log(f"Importación de machote externo exitosa. {len(coincidentes)} series marcadas como usadas.")
            messagebox.showinfo("Importación exitosa", f"Se encontraron {len(coincidentes)} de {detectadas} series del machote.\nFueron movidas a 'USADOS' bajo '{filename}'.")
        else:
            self.preview_label.configure(text=f"No hubo coincidencias ({detectadas} detectadas).", text_color=CURRENT_THEME["danger"])
            messagebox.showwarning("Sin coincidencias", f"Se detectaron {detectadas} series en el Excel,\npero ninguna coincide con el inventario disponible.")

    def _import_external_error(self, exc):
        import traceback
        self.preview_label.configure(text="Error importando machote externo.", text_color=CURRENT_THEME["danger"])
        self.app.log(f"Error en importación externa:\n{traceback.format_exc()}")
        messagebox.showerror("Error de importación", f"Hubo un error al procesar el machote externo:\n\n{exc}")

    # End of Export Machote


class ImportView(BaseView):
    title = "Puerto Mercante"
    subtitle = "Carga nueva mercancía desde un PDF, valida el contenido y actualiza el inventario."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.selected_pdf = ctk.StringVar(value="")
        self.selected_pdfs = []
        self.items_loaded = []
        self.parse_report = {}
        self.parse_warnings = []
        self.create_header()

        card = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        ctk.CTkButton(top, text="Elegir PDF", fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", command=self.select_pdf).pack(side="left")
        ctk.CTkButton(top, text="Limpiar selección", fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"], command=self.clear_loaded_pdf).pack(side="left", padx=(10, 0))
        ctk.CTkButton(top, text="Simular importación", fg_color=CURRENT_THEME["warning"], hover_color="#A55A18", command=self.simulate_import).pack(side="left", padx=10)
        ctk.CTkButton(top, text="Ver warnings", fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"], command=self.show_parse_warnings).pack(side="left", padx=(0, 10))
        ctk.CTkButton(top, text="Importar mercancía", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.import_pdf).pack(side="left", padx=10)
        ctk.CTkButton(top, text="Deshacer última carga", fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], command=self.undo_last_import).pack(side="left", padx=10)
        ctk.CTkLabel(top, textvariable=self.selected_pdf, text_color=CURRENT_THEME["text"]).pack(side="left", padx=8)

        self.summary_label = ctk.CTkLabel(card, text="Sin PDF seleccionado.", text_color=CURRENT_THEME["muted"])
        self.summary_label.grid(row=1, column=0, sticky="w", padx=18)

        self.preview_tree = self.app.create_treeview(card, [
            ("incluir", "Incluir", 60),
            ("archivo", "Archivo", 170),
            ("sucursal", "Sucursal", 120),
            ("modelo", "Modelo", 180),
            ("color", "Color", 100),
            ("serie", "Serie", 180),
        ])
        self.preview_tree.grid(row=2, column=0, sticky="nsew", padx=12, pady=(8, 12))
        self.preview_tree.bind("<Double-1>", self.toggle_inclusion)

    def select_pdf(self):
        pdf_paths = filedialog.askopenfilenames(title="Seleccionar PDF(s) de mercancía", filetypes=[("PDF", "*.pdf")])
        if not pdf_paths:
            return
        self.selected_pdfs = list(pdf_paths)
        self.selected_pdf.set(f"{len(self.selected_pdfs)} PDF(s) seleccionados")
        all_items = []
        all_warnings = []
        parse_reports = []
        errors = []
        for pdf_path in self.selected_pdfs:
            try:
                items, warnings, report = mg.extraer_nuevos_articulos(pdf_path, with_report=True)
                for it in items:
                    it["_source_pdf"] = os.path.basename(pdf_path)
                all_items.extend(items)
                all_warnings.extend([f"{os.path.basename(pdf_path)}: {w}" for w in warnings])
                parse_reports.append((pdf_path, report))
            except Exception as exc:
                errors.append(f"{os.path.basename(pdf_path)} -> {exc}")

        # Dedupe por serie para evitar dobles inserciones al combinar PDFs
        dedup = {}
        for item in all_items:
            serie = str(item.get("No de SERIE:", "")).strip()
            if serie and serie not in dedup:
                dedup[serie] = item
        self.items_loaded = list(dedup.values())
        self.parse_warnings = all_warnings
        self.parse_report = {
            "pdf_count": len(self.selected_pdfs),
            "items_raw": len(all_items),
            "items_dedup": len(self.items_loaded),
            "warnings": len(all_warnings),
            "warnings_log": parse_reports[0][1].get("warnings_log") if parse_reports else "N/D",
            "errors": errors,
        }
        if errors:
            messagebox.showwarning("PDFs con errores", "Algunos PDFs no se pudieron procesar:\n\n" + "\n".join(errors[:8]))

        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        for idx, item in enumerate(self.items_loaded):
            color_display = self._format_color_for_display(item.get("COLOR", ""))
            # Store index in tag to easily identify it later
            self.preview_tree.insert("", "end", values=("[X]", item.get("_source_pdf", ""), item.get("SUCURSAL", ""), item.get("MODELO BASE", ""), color_display, item.get("No de SERIE:", "")), tags=(str(idx),))
        inv = self.app.get_inventory_data(refresh=False) or {}
        existentes = set()
        for key in ("reporte", "usados", "xml"):
            df = inv.get(key)
            if df is not None and not df.empty and "No de SERIE:" in df.columns:
                existentes.update(df["No de SERIE:"].astype(str).str.strip().tolist())
        duplicados = sum(1 for item in self.items_loaded if str(item.get("No de SERIE:", "")).strip() in existentes)
        self.summary_label.configure(text=f"Se detectaron {len(self.items_loaded)} artículos únicos de {len(self.selected_pdfs)} PDF(s) ({duplicados} potencialmente duplicados). Haz doble clic para desmarcar/marcar.")
        if self.parse_warnings:
            self.app.log(f"Advertencias de parseo PDF: {len(self.parse_warnings)} (ver {self.parse_report.get('warnings_log', 'log')})")
        self.app.log(f"PDF(s) analizado(s): {len(self.selected_pdfs)} con {len(self.items_loaded)} artículos únicos detectados.")

    def _format_color_for_display(self, color_value):
        # Solo formato visual: mantenemos dato interno intacto
        return format_color_for_display(color_value)

    def clear_loaded_pdf(self):
        self.selected_pdf.set("")
        self.selected_pdfs = []
        self.items_loaded = []
        self.parse_report = {}
        self.parse_warnings = []
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        self.summary_label.configure(text="Selección limpiada. Sin PDF seleccionado.", text_color=CURRENT_THEME["muted"])
        self.app.log("Selección de PDF limpiada manualmente.")

    def show_parse_warnings(self):
        if not self.parse_warnings:
            messagebox.showinfo("Warnings de parseo", "No se registraron warnings en el PDF actual.")
            return
        preview = "\n".join(f"- {w}" for w in self.parse_warnings[:15])
        extra = ""
        if len(self.parse_warnings) > 15:
            extra = f"\n... y {len(self.parse_warnings) - 15} más."
        log_path = self.parse_report.get("warnings_log", "N/D")
        messagebox.showinfo(
            "Warnings de parseo",
            f"Se detectaron {len(self.parse_warnings)} warnings.\n\n{preview}{extra}\n\nLog:\n{log_path}",
        )

    def _create_pre_import_backup(self):
        src = Path(mg.PATH_INVENTARIO)
        if not src.exists():
            return None
        backup_dir = DATA_DIR / "import_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = backup_dir / f"inventario_pre_import_{stamp}.xlsx"
        shutil.copy2(src, dst)
        return str(dst)

    def undo_last_import(self):
        backup = self.app.app_state.last_import_backup
        if not backup:
            messagebox.showwarning("Sin respaldo", "No hay una carga reciente para deshacer.")
            return
        backup_path = Path(backup)
        if not backup_path.exists():
            messagebox.showwarning("Respaldo no encontrado", f"No existe el respaldo:\n{backup_path}")
            return
        try:
            shutil.copy2(backup_path, Path(mg.PATH_INVENTARIO))
            self.app.refresh_data(force=True)
            self.app.history_view.refresh()
            self.summary_label.configure(text="Última carga revertida con éxito.", text_color=CURRENT_THEME["emerald"])
            self.app.log(f"Carga revertida usando respaldo: {backup_path.name}")
            messagebox.showinfo("Reversión completada", f"Inventario restaurado desde:\n{backup_path}")
        except Exception as exc:
            self.app.log(f"Error revirtiendo carga: {exc}")
            messagebox.showerror("Error revirtiendo", f"No se pudo revertir la carga.\n\n{exc}")

    def _get_selected_items(self):
        selected_items = []
        for item_id in self.preview_tree.get_children():
            values = self.preview_tree.item(item_id, "values")
            if values[0] == "[X]":
                idx = int(self.preview_tree.item(item_id, "tags")[0])
                selected_items.append(self.items_loaded[idx])
        return selected_items

    def simulate_import(self):
        if not self.selected_pdfs:
            messagebox.showwarning("PDF requerido", "Primero selecciona uno o más PDFs para simular.")
            return
        selected_items = self._get_selected_items()
        if not selected_items:
            messagebox.showwarning("Aviso", "No hay artículos seleccionados para simular.")
            return

        inv = self.app.get_inventory_data(refresh=False) or {}
        existentes = set()
        for key in ("reporte", "usados", "xml"):
            df = inv.get(key)
            if df is not None and not df.empty and "No de SERIE:" in df.columns:
                existentes.update(df["No de SERIE:"].astype(str).str.strip().tolist())
        duplicados = [it for it in selected_items if str(it.get("No de SERIE:", "")).strip() in existentes]
        nuevos = len(selected_items) - len(duplicados)
        detalles = (
            f"PDFs: {len(self.selected_pdfs)}\n"
            f"Seleccionados: {len(selected_items)}\n"
            f"Nuevos estimados: {nuevos}\n"
            f"Duplicados estimados: {len(duplicados)}\n"
            f"Advertencias parseo: {len(self.parse_warnings)}"
        )
        self.summary_label.configure(text=f"Simulación lista: {nuevos} nuevos, {len(duplicados)} duplicados.", text_color=CURRENT_THEME["gold"])
        self.app.log(f"Simulación de carga:\n{detalles}")
        messagebox.showinfo("Simulación de importación", detalles)

    def toggle_inclusion(self, event):
        region = self.preview_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        column = self.preview_tree.identify_column(event.x)
        if column != "#1":
            return
        item_id = self.preview_tree.identify_row(event.y)
        if not item_id:
            return
        values = list(self.preview_tree.item(item_id, "values"))
        if values[0] == "[X]":
            values[0] = "[ ]"
        else:
            values[0] = "[X]"
        self.preview_tree.item(item_id, values=values)

    def import_pdf(self):
        if not self.selected_pdfs:
            messagebox.showwarning("PDF requerido", "Primero selecciona uno o más PDFs para importar.")
            return
        selected_items = self._get_selected_items()
        if not selected_items:
            messagebox.showwarning("Aviso", "No hay ningún artículo seleccionado para importar.")
            return
        threshold = int(self.app.app_state.config.get("parse_warning_threshold", 3))
        if len(self.parse_warnings) >= threshold:
            proceed = messagebox.askyesno(
                "Confirmación reforzada",
                f"Este PDF tiene {len(self.parse_warnings)} warnings (umbral {threshold}).\n\n"
                "Se recomienda revisar 'Ver warnings' antes de importar.\n\n¿Deseas continuar?",
            )
            if not proceed:
                self.summary_label.configure(text="Importación cancelada por warnings.", text_color=CURRENT_THEME["warning"])
                self.app.log("Importación cancelada por usuario tras confirmación reforzada.")
                return

        self.app.log("Iniciando importación en segundo plano...")
        self.summary_label.configure(text="Importando mercancía, por favor espera...", text_color=CURRENT_THEME["warning"])

        def _task():
            try:
                backup_path = self._create_pre_import_backup()
                output_path = mg.cargar_inventario_y_reemplazar(self.selected_pdfs[0], lista_articulos=selected_items)
                self.app.after(0, self._import_success, output_path, selected_items, list(self.selected_pdfs), backup_path)
            except Exception as exc:
                self.app.after(0, self._import_error, exc)

        self.app.run_in_thread(_task)

    def _import_success(self, output_path, selected_items, pdf_paths, backup_path):
        self.app.app_state.last_import_backup = backup_path
        self.app.app_state.record_event(
            "carga",
            f"Mercancía importada ({len(selected_items)} piezas)",
            {"pdfs": pdf_paths, "inventario": output_path, "backup_previo": backup_path},
        )
        self.app.refresh_data(force=True)
        self.app.history_view.refresh()
        self.summary_label.configure(text=f"Carga completa. {len(selected_items)} artículos importados.", text_color=CURRENT_THEME["emerald"])
        self.app.log(f"Reporte post-carga: seleccionados={len(selected_items)} warnings_parseo={len(self.parse_warnings)}")
        self.app.log(f"Mercancía importada: {len(selected_items)} piezas desde {len(pdf_paths)} PDF(s).")
        messagebox.showinfo("Carga completada", f"Se guardaron {len(selected_items)} piezas.\nInventario actualizado en:\n\n{output_path}")

    def _import_error(self, exc):
        import traceback
        self.summary_label.configure(text="Error durante la importación.", text_color=CURRENT_THEME["danger"])
        self.app.log(f"Error importando PDF:\n{traceback.format_exc()}")
        messagebox.showerror("Error importando", f"No se pudo cargar la mercancía.\n\n{exc}")

class XMLView(BaseView):
    title = "Templo de UUID"
    subtitle = "Cruza XMLs, encuentra coincidencias y mueve piezas facturadas a su santuario correcto."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.selected_dir = ctk.StringVar(value="")
        self.create_header()

        card = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        ctk.CTkButton(top, text="Elegir carpeta XML", fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", command=self.select_dir).pack(side="left")
        ctk.CTkButton(top, text="Validar y actualizar", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.process_xml).pack(side="left", padx=10)
        ctk.CTkLabel(top, textvariable=self.selected_dir, text_color=CURRENT_THEME["text"]).pack(side="left", padx=8)

        self.summary_label = ctk.CTkLabel(card, text="Aún no se ha inspeccionado ninguna carpeta.", text_color=CURRENT_THEME["muted"])
        self.summary_label.grid(row=1, column=0, sticky="w", padx=18)

        self.preview_tree = self.app.create_treeview(card, [
            ("serie", "Serie", 200),
            ("uuid", "UUID", 360),
        ])
        self.preview_tree.grid(row=2, column=0, sticky="nsew", padx=12, pady=(8, 12))

    def select_dir(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta de XMLs")
        if not folder:
            return
        self.selected_dir.set(folder)
        try:
            results = mg.procesar_xmls(folder)
        except Exception as exc:
            messagebox.showerror("Error leyendo XMLs", f"No se pudo inspeccionar la carpeta.\n\n{exc}")
            return
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        for serie, uuid in list(results.items())[:250]:
            self.preview_tree.insert("", "end", values=(serie, uuid))
        self.summary_label.configure(text=f"Se encontraron {len(results)} series en los XML analizados.")
        self.app.log(f"Carpeta XML analizada: {folder}")

    def process_xml(self):
        folder = self.selected_dir.get().strip()
        if not folder:
            messagebox.showwarning("Carpeta requerida", "Primero selecciona una carpeta de XMLs.")
            return

        self.app.log("Conciliando XMLs en segundo plano...")
        self.summary_label.configure(text="Cruzando datos Sheikah con el inventario...", text_color=CURRENT_THEME["warning"])

        def _task():
            try:
                output_path = mg.validar_xml_y_reemplazar(folder)
                self.app.after(0, self._process_success, output_path, folder)
            except Exception as exc:
                self.app.after(0, self._process_error, exc)

        self.app.run_in_thread(_task)

    def _process_success(self, output_path, folder):
        self.app.app_state.record_event("xml", "UUIDs conciliados", {"carpeta": folder, "inventario": output_path})
        self.app.refresh_data(force=True)
        self.app.history_view.refresh()
        self.summary_label.configure(text="Sincronización de UUID completada.", text_color=CURRENT_THEME["emerald"])
        self.app.log(f"XMLs conciliados desde {folder}")
        messagebox.showinfo("XML conciliados", f"Inventario actualizado en:\n\n{output_path}")

    def _process_error(self, exc):
        import traceback
        self.summary_label.configure(text="Error conciliando XMLs.", text_color=CURRENT_THEME["danger"])
        self.app.log(f"Error procesando XML:\n{traceback.format_exc()}")
        messagebox.showerror("Error procesando XMLs", f"No se pudo actualizar el inventario con XMLs.\n\n{exc}")


class HistoryView(BaseView):
    title = "Crónicas del Héroe"
    subtitle = "Registro histórico de machotes, cargas, conciliaciones y cambios importantes."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(1, weight=1)
        card = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.tree = self.app.create_treeview(card, [
            ("fecha", "Fecha", 160),
            ("tipo", "Tipo", 100),
            ("resumen", "Resumen", 420),
        ])
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for entry in self.app.app_state.history:
            self.tree.insert("", "end", values=(entry.get("timestamp", ""), entry.get("type", ""), entry.get("summary", "")))


class MachoteHistoryView(BaseView):
    title = "Registro de Machotes"
    subtitle = "Administra los machotes generados, revierte asignaciones y localiza archivos."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(2, weight=1)

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        ctk.CTkButton(controls, text="Deshacer Machote Seleccionado", fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], command=self.undo_machote).pack(side="left", padx=(0, 10))
        ctk.CTkButton(controls, text="Abrir Archivo de Machote", fg_color=CURRENT_THEME["sky"], hover_color="#4F7C7A", command=self.open_machote_file).pack(side="left")

        card = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.tree = self.app.create_treeview(card, [
            ("fecha", "Fecha", 160),
            ("archivo", "Archivo", 450),
            ("piezas", "Piezas", 100),
        ])
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Extract machote events from history
        machotes = [m for m in self.app.app_state.history if m.get("type") in ("machote", "machote_externo")]

        for entry in machotes:
            details = entry.get("details", {})

            if entry.get("type") == "machote":
                # Regular generated machote
                archivo = details.get("archivo", "")
                piezas = str(details.get("piezas", ""))
            elif entry.get("type") == "machote_externo":
                # External imported machote
                archivo = details.get("archivo", "")
                piezas = str(details.get("series_coincidentes", ""))

            self.tree.insert("", "end", values=(entry.get("timestamp", ""), archivo, piezas))

    def get_selected_machote(self):
        selected = self.tree.selection()
        if not selected:
            return None
        item = self.tree.item(selected[0])
        return item["values"][1]

    def undo_machote(self):
        archivo = self.get_selected_machote()
        if not archivo:
            messagebox.showwarning("Aviso", "Selecciona un machote de la lista para deshacer.")
            return

        import os
        filename = os.path.basename(archivo)

        # Check if it's an external machote (prefix EXT:)
        # We need to find the name used in the db
        history_entry = next((m for m in self.app.app_state.history if m.get("details", {}).get("archivo") == archivo), None)

        if history_entry and history_entry.get("type") == "machote_externo":
            db_machote_name = f"EXT: {filename}"
        else:
            db_machote_name = filename

        confirm = messagebox.askyesno(
            "Deshacer Machote",
            f"¿Estás seguro de que deseas deshacer la asignación para el machote '{db_machote_name}'?\n\nEsto moverá todas las piezas asociadas de 'USADOS' de vuelta a 'DISPONIBLES'."
        )

        if not confirm:
            return

        self.app.log(f"Intentando deshacer machote: {db_machote_name}")

        def _task():
            try:
                success = mg.deshacer_machote(db_machote_name)
                self.app.after(0, self._undo_success, success, db_machote_name)
            except Exception as exc:
                self.app.after(0, self._undo_error, exc)

        self.app.run_in_thread(_task)

    def _undo_success(self, success, db_machote_name):
        if success:
            self.app.app_state.record_event("machote_undo", f"Machote deshecho: {db_machote_name}")
            self.app.refresh_data(force=True)
            self.refresh()
            self.app.log(f"Machote deshecho exitosamente: {db_machote_name}")
            messagebox.showinfo("Machote Deshecho", f"El machote '{db_machote_name}' ha sido deshecho.\nLas piezas regresaron a DISPONIBLES.")
        else:
            self.app.log(f"No se pudo deshacer {db_machote_name} (no se encontraron piezas).")
            messagebox.showwarning("Sin efecto", f"No se encontraron piezas en el inventario actual asignadas al machote '{db_machote_name}'.")

    def _undo_error(self, exc):
        import traceback
        self.app.log(f"Error deshaciendo machote:\n{traceback.format_exc()}")
        messagebox.showerror("Error", f"No se pudo deshacer el machote.\n\n{exc}")

    def open_machote_file(self):
        archivo = self.get_selected_machote()
        if not archivo:
            messagebox.showwarning("Aviso", "Selecciona un machote de la lista para abrir.")
            return

        import os
        import platform
        import subprocess

        if not os.path.exists(archivo):
            messagebox.showerror("Archivo no encontrado", f"El archivo ya no existe en la ruta:\n{archivo}")
            return

        try:
            if platform.system() == 'Windows':
                os.startfile(archivo)
            elif platform.system() == 'Darwin': # macOS
                subprocess.call(('open', archivo))
            else: # Linux
                subprocess.call(('xdg-open', archivo))
            self.app.log(f"Archivo abierto: {archivo}")
        except Exception as exc:
            self.app.log(f"Error abriendo archivo {archivo}: {exc}")
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{exc}")


class SettingsView(BaseView):
    title = "Cámara del Sabio"
    subtitle = "Ajustes visuales, nombres por defecto y rutas clave del sistema."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        card = ctk.CTkScrollableFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.grid_rowconfigure(1, weight=1)
        self.entries = {}

        fields = [
            ("empresa_default", "Empresa por defecto"),
            ("cuenta_default", "Cuenta por defecto"),
            ("rfc_default", "RFC por defecto"),
            ("logo_text", "Texto principal"),
            ("parse_warning_threshold", "Umbral warnings (importación PDF)"),
            ("inventario_path", "Ruta inventario"),
            ("machote_path", "Ruta plantilla machote"),
            ("precios_path", "Ruta lista de precios"),
            ("output_dir", "Carpeta de salida"),
        ]
        for idx, (key, label) in enumerate(fields):
            frame = ctk.CTkFrame(card, fg_color="transparent")
            frame.grid(row=idx, column=0, sticky="ew", padx=8, pady=6)
            frame.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(frame, text=label, text_color=CURRENT_THEME["muted"]).grid(row=0, column=0, sticky="w")
            entry = ctk.CTkEntry(frame)
            entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
            entry.insert(0, str(self.app.app_state.config.get(key, "")))
            self.entries[key] = entry

        mode_frame = ctk.CTkFrame(card, fg_color="transparent")
        mode_frame.grid(row=len(fields), column=0, sticky="ew", padx=8, pady=12)
        ctk.CTkLabel(mode_frame, text="Modo visual (Requiere Reinicio)", text_color=CURRENT_THEME["muted"]).pack(anchor="w")
        self.mode_option = ctk.CTkOptionMenu(mode_frame, values=["Dark", "HoneyWhale", "Light", "System"], command=self.change_mode, fg_color=CURRENT_THEME["gold"], button_color=CURRENT_THEME["gold_hover"], text_color="#221A0C")
        self.mode_option.pack(anchor="w", pady=(6, 0))
        self.mode_option.set(self.app.app_state.config.get("theme_mode", "Dark"))

        ctk.CTkButton(card, text="Guardar ajustes", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.save).grid(row=len(fields) + 1, column=0, sticky="w", padx=8, pady=(8, 16))

    def change_mode(self, mode):
        if mode in ["Dark", "Light", "System"]:
            ctk.set_appearance_mode(mode)
        else:
            ctk.set_appearance_mode("Dark") # Fallback to Dark for HoneyWhale which uses Dark appearance inherently

        self.app.app_state.config["theme_mode"] = mode
        self.app.app_state.save_config()
        messagebox.showinfo("Reinicio Requerido", "Cambiar el modo visual de la aplicación requiere reiniciar para surtir efecto completo.")

    def save(self):
        for key, entry in self.entries.items():
            value = entry.get().strip()
            if key == "parse_warning_threshold":
                try:
                    value_int = int(value)
                except ValueError:
                    messagebox.showwarning("Valor inválido", "El umbral de warnings debe ser un número entero.")
                    return
                if value_int < 0:
                    messagebox.showwarning("Valor inválido", "El umbral de warnings no puede ser negativo.")
                    return
                self.app.app_state.config[key] = value_int
            else:
                self.app.app_state.config[key] = value
        self.app.app_state.save_config()
        self.app.apply_runtime_config()
        self.app.log("Ajustes guardados correctamente.")
        messagebox.showinfo("Ajustes guardados", "La configuración del sabio ha sido preservada.")


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
        mg.PATH_INVENTARIO = self.app_state.config.get("inventario_path", mg.PATH_INVENTARIO)
        mg.PATH_MACHOTE = self.app_state.config.get("machote_path", mg.PATH_MACHOTE)
        mg.PATH_PRECIOS = self.app_state.config.get("precios_path", mg.PATH_PRECIOS)
        mg.OUTPUT_DIR = self.app_state.config.get("output_dir", mg.OUTPUT_DIR)

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
        output_dir = Path(self.app_state.config.get("output_dir", mg.OUTPUT_DIR))
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
