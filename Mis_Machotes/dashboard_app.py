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

OOT_THEME = {
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
}


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

        ctk.set_appearance_mode(self.config.get("theme_mode", "Dark"))

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
        header = ctk.CTkFrame(self, fg_color=OOT_THEME["panel"], corner_radius=18, border_width=1, border_color=OOT_THEME["gold"])
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=self.title, font=ctk.CTkFont(size=28, weight="bold"), text_color=OOT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(header, text=self.subtitle, font=ctk.CTkFont(size=13), text_color=OOT_THEME["text"]).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))
        return header


class DashboardView(BaseView):
    title = "Santuario del Reino"
    subtitle = "Vista general del inventario, hallazgos y señales clave del negocio."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(2, weight=1)
        self.metric_labels = {}
        self.chart_canvas = None
        self.summary_tree = None

        metrics = ctk.CTkFrame(self, fg_color="transparent")
        metrics.grid(row=1, column=0, sticky="ew", padx=18)
        for idx in range(4):
            metrics.grid_columnconfigure(idx, weight=1)

        self._metric_card(metrics, 0, "Rupias Totales", "$0.00", "total")
        self._metric_card(metrics, 1, "Reliquias Activas", "0", "pieces")
        self._metric_card(metrics, 2, "Tasa XML", "0%", "xml")
        self._metric_card(metrics, 3, "Sucursales", "0", "branches")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, sticky="nsew", padx=18, pady=(12, 18))
        content.grid_columnconfigure((0, 1), weight=1)
        content.grid_rowconfigure(0, weight=1)

        chart_card = ctk.CTkFrame(content, fg_color=OOT_THEME["panel"], corner_radius=18, border_width=1, border_color=OOT_THEME["gold"])
        chart_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        chart_card.grid_rowconfigure(1, weight=1)
        chart_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(chart_card, text="Mapa de Sucursales", font=ctk.CTkFont(size=18, weight="bold"), text_color=OOT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))
        self.chart_container = ctk.CTkFrame(chart_card, fg_color="transparent")
        self.chart_container.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

        summary_card = ctk.CTkFrame(content, fg_color=OOT_THEME["panel"], corner_radius=18, border_width=1, border_color=OOT_THEME["gold"])
        summary_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        summary_card.grid_rowconfigure(1, weight=1)
        summary_card.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(summary_card, text="Reliquias Más Valiosas", font=ctk.CTkFont(size=18, weight="bold"), text_color=OOT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))
        self.summary_tree = self.app.create_treeview(summary_card, [
            ("sucursal", "Sucursal", 110),
            ("modelo", "Modelo", 160),
            ("total", "Total", 120),
        ])
        self.summary_tree.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def _metric_card(self, parent, column, title, value, key):
        card = ctk.CTkFrame(parent, fg_color=OOT_THEME["panel_alt"], corner_radius=16, border_width=1, border_color=OOT_THEME["gold"])
        card.grid(row=0, column=column, sticky="ew", padx=6)
        ctk.CTkLabel(card, text=title, text_color=OOT_THEME["muted"], font=ctk.CTkFont(size=13)).pack(anchor="w", padx=16, pady=(12, 0))
        label = ctk.CTkLabel(card, text=value, text_color=OOT_THEME["text"], font=ctk.CTkFont(size=24, weight="bold"))
        label.pack(anchor="w", padx=16, pady=(2, 14))
        self.metric_labels[key] = label

    def refresh(self):
        inventory = self.app.get_inventory_data(refresh=False)
        if not inventory:
            return
        df_reporte = inventory["reporte"]
        df_usados = inventory["usados"]
        df_xml = inventory["xml"]

        total_df = pd.concat([df for df in [df_reporte, df_usados, df_xml] if not df.empty], ignore_index=True) if any(not df.empty for df in [df_reporte, df_usados, df_xml]) else pd.DataFrame()
        total_money = pd.to_numeric(total_df.get("TOTAL", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not total_df.empty else 0
        total_pieces = len(total_df)
        xml_rate = (len(df_xml) / total_pieces * 100) if total_pieces else 0
        branch_count = total_df["SUCURSAL"].nunique() if not total_df.empty and "SUCURSAL" in total_df.columns else 0

        self.metric_labels["total"].configure(text=f"${total_money:,.2f}")
        self.metric_labels["pieces"].configure(text=str(total_pieces))
        self.metric_labels["xml"].configure(text=f"{xml_rate:.1f}%")
        self.metric_labels["branches"].configure(text=str(branch_count))

        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)

        if not total_df.empty and {"SUCURSAL", "MODELO BASE", "TOTAL"}.issubset(total_df.columns):
            top = total_df.copy()
            top["TOTAL"] = pd.to_numeric(top["TOTAL"], errors="coerce").fillna(0)
            top = top.groupby(["SUCURSAL", "MODELO BASE"], as_index=False)["TOTAL"].sum().sort_values("TOTAL", ascending=False).head(12)
            for _, row in top.iterrows():
                self.summary_tree.insert("", "end", values=(row["SUCURSAL"], row["MODELO BASE"], f"${row['TOTAL']:,.2f}"))

        self.draw_chart(total_df)

    def draw_chart(self, total_df):
        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()

        fig = Figure(figsize=(5.4, 4.2), dpi=100, facecolor=OOT_THEME["panel"])
        ax = fig.add_subplot(111)
        ax.set_facecolor(OOT_THEME["panel"])

        if not total_df.empty and "SUCURSAL" in total_df.columns:
            counts = total_df["SUCURSAL"].fillna("SIN SUCURSAL").value_counts().head(6)
            colors = [OOT_THEME["gold"], OOT_THEME["forest"], OOT_THEME["emerald"], OOT_THEME["sky"], OOT_THEME["warning"], OOT_THEME["danger"]]
            ax.pie(counts.values, labels=counts.index, autopct="%1.1f%%", startangle=90, colors=colors[: len(counts)], textprops={"color": OOT_THEME["text"], "fontsize": 10})
            ax.set_title("Distribución del Reino", color=OOT_THEME["gold"], fontsize=14)
        else:
            ax.text(0.5, 0.5, "No hay datos aún", color=OOT_THEME["text"], ha="center", va="center")
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
        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        controls.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(controls, text="Buscar:", text_color=OOT_THEME["text"]).grid(row=0, column=0, padx=(0, 10), sticky="w")
        self.search_entry = ctk.CTkEntry(controls, placeholder_text="modelo, serie, sucursal, color...")
        self.search_entry.grid(row=0, column=1, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda _e: self.refresh())
        ctk.CTkButton(controls, text="Recargar", fg_color=OOT_THEME["forest"], hover_color=OOT_THEME["forest_hover"], command=lambda: self.app.refresh_data(force=True)).grid(row=0, column=2, padx=10)

        self.tabview = ctk.CTkTabview(self, fg_color=OOT_THEME["panel"], segmented_button_selected_color=OOT_THEME["gold"], segmented_button_selected_hover_color=OOT_THEME["gold_hover"], segmented_button_unselected_color=OOT_THEME["panel_alt"])
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.grid_rowconfigure(2, weight=1)
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

    def refresh(self):
        inventory = self.app.get_inventory_data(refresh=False)
        if not inventory:
            return
        mapping = {
            "Disponibles": (inventory["reporte"], None),
            "Usados": (inventory["usados"], "MACHOTE"),
            "XML": (inventory["xml"], "UUID"),
        }
        term = self.search_entry.get().strip().lower()
        for name, (df, extra_col) in mapping.items():
            tree = self.trees[name]
            for item in tree.get_children():
                tree.delete(item)
            if df is None or df.empty:
                continue
            for _, row in df.iterrows():
                serie = str(row.get("No de SERIE:", ""))
                values = [
                    str(row.get("SUCURSAL", "")),
                    str(row.get("MODELO BASE", "")),
                    str(row.get("COLOR", "")),
                    serie,
                    self.app.money(row.get("TOTAL", 0)),
                    str(row.get(extra_col, "")) if extra_col and extra_col in df.columns else "",
                ]
                haystack = " ".join(values).lower()
                if not term or term in haystack:
                    tree.insert("", "end", values=values)


class GeneratorView(BaseView):
    title = "Forja del Machote"
    subtitle = "Calcula una combinación inteligente, revísala y expórtala como si fuera una reliquia sagrada."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.preview_df = pd.DataFrame()
        self.create_header()

        top = ctk.CTkFrame(self, fg_color=OOT_THEME["panel"], corner_radius=18, border_width=1, border_color=OOT_THEME["gold"])
        top.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))
        for i in range(4):
            top.grid_columnconfigure(i, weight=1)

        self.amount_entry = self._entry(top, 0, 0, "Monto objetivo", "150000")
        self.company_entry = self._entry(top, 0, 1, "Empresa", self.app.state.config.get("empresa_default", ""))
        self.account_entry = self._entry(top, 0, 2, "Cuenta", self.app.state.config.get("cuenta_default", "MP"))
        self.rfc_entry = self._entry(top, 0, 3, "RFC (opcional)", self.app.state.config.get("rfc_default", ""))

        self.include_children = ctk.CTkSwitch(top, text="Incluir infantiles", progress_color=OOT_THEME["gold"])
        self.include_children.grid(row=1, column=0, padx=12, pady=10, sticky="w")
        self.include_motor = ctk.CTkSwitch(top, text="Incluir motocicletas", progress_color=OOT_THEME["gold"])
        self.include_motor.grid(row=1, column=1, padx=12, pady=10, sticky="w")

        controls = ctk.CTkFrame(top, fg_color="transparent")
        controls.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10, pady=(0, 12))
        ctk.CTkButton(controls, text="Previsualizar combinación", fg_color=OOT_THEME["gold"], hover_color=OOT_THEME["gold_hover"], text_color="#221A0C", command=self.calculate_preview).pack(side="left", padx=(0, 10))
        ctk.CTkButton(controls, text="Exportar machote", fg_color=OOT_THEME["forest"], hover_color=OOT_THEME["forest_hover"], command=self.export_machote).pack(side="left")

        preview_card = ctk.CTkFrame(self, fg_color=OOT_THEME["panel"], corner_radius=18, border_width=1, border_color=OOT_THEME["gold"])
        preview_card.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        preview_card.grid_rowconfigure(1, weight=1)
        preview_card.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.preview_label = ctk.CTkLabel(preview_card, text="Aún no se ha invocado una combinación.", text_color=OOT_THEME["text"], font=ctk.CTkFont(size=16, weight="bold"))
        self.preview_label.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 8))
        self.preview_tree = self.app.create_treeview(preview_card, [
            ("sucursal", "Sucursal", 110),
            ("modelo", "Modelo", 150),
            ("serie", "Serie", 180),
            ("total", "Total", 120),
        ])
        self.preview_tree.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def _entry(self, parent, row, column, label, value=""):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=column, sticky="ew", padx=10, pady=(12, 0))
        ctk.CTkLabel(frame, text=label, text_color=OOT_THEME["muted"]).pack(anchor="w")
        entry = ctk.CTkEntry(frame)
        entry.pack(fill="x", pady=(4, 0))
        if value:
            entry.insert(0, value)
        return entry

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

        try:
            df_available = mg.procesar_inventario(
                inventory["reporte"],
                inventory["precios"],
                incluir_infantiles=self.include_children.get() == 1,
                incluir_motobicis=self.include_motor.get() == 1,
            )
            preview = mg.seleccionar_articulos(df_available, target)
        except Exception as exc:
            messagebox.showerror("Error calculando", f"No se pudo generar la vista previa.\n\n{exc}")
            return

        self.preview_df = preview
        self.app.state.last_preview = preview
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        total = pd.to_numeric(preview.get("TOTAL", pd.Series(dtype=float)), errors="coerce").fillna(0).sum() if not preview.empty else 0
        diff = abs(total - target)
        self.preview_label.configure(text=f"Resultado: {len(preview)} piezas · {self.app.money(total)} · diferencia {self.app.money(diff)}")

        for _, row in preview.iterrows():
            self.preview_tree.insert("", "end", values=(
                str(row.get("SUCURSAL", "")),
                str(row.get("MODELO BASE", "")),
                str(row.get("No de SERIE:", "")),
                self.app.money(row.get("TOTAL", 0)),
            ))

        self.app.log(f"Vista previa generada para ${target:,.2f} con {len(preview)} artículos.")

    def export_machote(self):
        if self.preview_df is None or self.preview_df.empty:
            self.calculate_preview()
            if self.preview_df is None or self.preview_df.empty:
                return

        company = self.company_entry.get().strip() or self.app.state.config.get("empresa_default", "MOVILIDAD ELECTRICA DE JALISCO")
        account = self.account_entry.get().strip() or self.app.state.config.get("cuenta_default", "MP")
        rfc = self.rfc_entry.get().strip() or self.app.state.config.get("rfc_default", "MEJ123456789")
        target = float(self.amount_entry.get().replace(",", "").strip())

        try:
            route, file_name, inventory_path = mg.generar_machote_y_actualizar(
                self.preview_df,
                target,
                company,
                rfc,
                account,
            )
        except Exception as exc:
            messagebox.showerror("Error exportando", f"No se pudo exportar el machote.\n\n{exc}")
            return

        self.app.state.last_generated_file = route
        self.app.state.record_event(
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


class ImportView(BaseView):
    title = "Puerto Mercante"
    subtitle = "Carga nueva mercancía desde un PDF, valida el contenido y actualiza el inventario."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.selected_pdf = ctk.StringVar(value="")
        self.create_header()

        card = ctk.CTkFrame(self, fg_color=OOT_THEME["panel"], corner_radius=18, border_width=1, border_color=OOT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        ctk.CTkButton(top, text="Elegir PDF", fg_color=OOT_THEME["gold"], hover_color=OOT_THEME["gold_hover"], text_color="#221A0C", command=self.select_pdf).pack(side="left")
        ctk.CTkButton(top, text="Importar mercancía", fg_color=OOT_THEME["forest"], hover_color=OOT_THEME["forest_hover"], command=self.import_pdf).pack(side="left", padx=10)
        ctk.CTkLabel(top, textvariable=self.selected_pdf, text_color=OOT_THEME["text"]).pack(side="left", padx=8)

        self.summary_label = ctk.CTkLabel(card, text="Sin PDF seleccionado.", text_color=OOT_THEME["muted"])
        self.summary_label.grid(row=1, column=0, sticky="w", padx=18)

        self.preview_tree = self.app.create_treeview(card, [
            ("sucursal", "Sucursal", 120),
            ("modelo", "Modelo", 180),
            ("color", "Color", 100),
            ("serie", "Serie", 180),
        ])
        self.preview_tree.grid(row=2, column=0, sticky="nsew", padx=12, pady=(8, 12))

    def select_pdf(self):
        pdf_path = filedialog.askopenfilename(title="Seleccionar PDF de mercancía", filetypes=[("PDF", "*.pdf")])
        if not pdf_path:
            return
        self.selected_pdf.set(pdf_path)
        try:
            items = mg.extraer_nuevos_articulos(pdf_path)
        except Exception as exc:
            messagebox.showerror("Error leyendo PDF", f"No se pudo analizar el PDF.\n\n{exc}")
            return
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        for item in items[:250]:
            self.preview_tree.insert("", "end", values=(item.get("SUCURSAL", ""), item.get("MODELO BASE", ""), item.get("COLOR", ""), item.get("No de SERIE:", "")))
        self.summary_label.configure(text=f"Se detectaron {len(items)} artículos potenciales para importar.")
        self.app.log(f"PDF analizado: {os.path.basename(pdf_path)} con {len(items)} artículos detectados.")

    def import_pdf(self):
        pdf_path = self.selected_pdf.get().strip()
        if not pdf_path:
            messagebox.showwarning("PDF requerido", "Primero selecciona un PDF para importar.")
            return
        try:
            output_path = mg.cargar_inventario_y_reemplazar(pdf_path)
        except Exception as exc:
            messagebox.showerror("Error importando", f"No se pudo cargar la mercancía.\n\n{exc}")
            return
        self.app.state.record_event("carga", "Mercancía importada desde PDF", {"pdf": pdf_path, "inventario": output_path})
        self.app.refresh_data(force=True)
        self.app.history_view.refresh()
        self.app.log(f"Mercancía importada desde {os.path.basename(pdf_path)}")
        messagebox.showinfo("Carga completada", f"Inventario actualizado en:\n\n{output_path}")


class XMLView(BaseView):
    title = "Templo de UUID"
    subtitle = "Cruza XMLs, encuentra coincidencias y mueve piezas facturadas a su santuario correcto."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.selected_dir = ctk.StringVar(value="")
        self.create_header()

        card = ctk.CTkFrame(self, fg_color=OOT_THEME["panel"], corner_radius=18, border_width=1, border_color=OOT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        ctk.CTkButton(top, text="Elegir carpeta XML", fg_color=OOT_THEME["gold"], hover_color=OOT_THEME["gold_hover"], text_color="#221A0C", command=self.select_dir).pack(side="left")
        ctk.CTkButton(top, text="Validar y actualizar", fg_color=OOT_THEME["forest"], hover_color=OOT_THEME["forest_hover"], command=self.process_xml).pack(side="left", padx=10)
        ctk.CTkLabel(top, textvariable=self.selected_dir, text_color=OOT_THEME["text"]).pack(side="left", padx=8)

        self.summary_label = ctk.CTkLabel(card, text="Aún no se ha inspeccionado ninguna carpeta.", text_color=OOT_THEME["muted"])
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
        try:
            output_path = mg.validar_xml_y_reemplazar(folder)
        except Exception as exc:
            messagebox.showerror("Error procesando XMLs", f"No se pudo actualizar el inventario con XMLs.\n\n{exc}")
            return
        self.app.state.record_event("xml", "UUIDs conciliados", {"carpeta": folder, "inventario": output_path})
        self.app.refresh_data(force=True)
        self.app.history_view.refresh()
        self.app.log(f"XMLs conciliados desde {folder}")
        messagebox.showinfo("XML conciliados", f"Inventario actualizado en:\n\n{output_path}")


class HistoryView(BaseView):
    title = "Crónicas del Héroe"
    subtitle = "Registro histórico de machotes, cargas, conciliaciones y cambios importantes."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(1, weight=1)
        card = ctk.CTkFrame(self, fg_color=OOT_THEME["panel"], corner_radius=18, border_width=1, border_color=OOT_THEME["gold"])
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
        for entry in self.app.state.history:
            self.tree.insert("", "end", values=(entry.get("timestamp", ""), entry.get("type", ""), entry.get("summary", "")))


class SettingsView(BaseView):
    title = "Cámara del Sabio"
    subtitle = "Ajustes visuales, nombres por defecto y rutas clave del sistema."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        card = ctk.CTkScrollableFrame(self, fg_color=OOT_THEME["panel"], corner_radius=18, border_width=1, border_color=OOT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.grid_rowconfigure(1, weight=1)
        self.entries = {}

        fields = [
            ("empresa_default", "Empresa por defecto"),
            ("cuenta_default", "Cuenta por defecto"),
            ("rfc_default", "RFC por defecto"),
            ("logo_text", "Texto principal"),
            ("inventario_path", "Ruta inventario"),
            ("machote_path", "Ruta plantilla machote"),
            ("precios_path", "Ruta lista de precios"),
            ("output_dir", "Carpeta de salida"),
        ]
        for idx, (key, label) in enumerate(fields):
            frame = ctk.CTkFrame(card, fg_color="transparent")
            frame.grid(row=idx, column=0, sticky="ew", padx=8, pady=6)
            frame.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(frame, text=label, text_color=OOT_THEME["muted"]).grid(row=0, column=0, sticky="w")
            entry = ctk.CTkEntry(frame)
            entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
            entry.insert(0, str(self.app.state.config.get(key, "")))
            self.entries[key] = entry

        mode_frame = ctk.CTkFrame(card, fg_color="transparent")
        mode_frame.grid(row=len(fields), column=0, sticky="ew", padx=8, pady=12)
        ctk.CTkLabel(mode_frame, text="Modo visual", text_color=OOT_THEME["muted"]).pack(anchor="w")
        self.mode_option = ctk.CTkOptionMenu(mode_frame, values=["Dark", "Light", "System"], command=self.change_mode, fg_color=OOT_THEME["gold"], button_color=OOT_THEME["gold_hover"], text_color="#221A0C")
        self.mode_option.pack(anchor="w", pady=(6, 0))
        self.mode_option.set(self.app.state.config.get("theme_mode", "Dark"))

        ctk.CTkButton(card, text="Guardar ajustes", fg_color=OOT_THEME["forest"], hover_color=OOT_THEME["forest_hover"], command=self.save).grid(row=len(fields) + 1, column=0, sticky="w", padx=8, pady=(8, 16))

    def change_mode(self, mode):
        ctk.set_appearance_mode(mode)
        self.app.state.config["theme_mode"] = mode
        self.app.state.save_config()

    def save(self):
        for key, entry in self.entries.items():
            self.app.state.config[key] = entry.get().strip()
        self.app.state.save_config()
        self.app.apply_runtime_config()
        self.app.log("Ajustes guardados correctamente.")
        messagebox.showinfo("Ajustes guardados", "La configuración del sabio ha sido preservada.")


class ZeldaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.state = AppState()
        self.title("MACHOTES OF TIME · Hero's Admin Panel")
        self.geometry("1480x900")
        self.minsize(1280, 760)
        self.configure(fg_color=OOT_THEME["bg"])
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.style_treeview()
        self.create_sidebar()
        self.create_main_area()
        self.create_log_panel()

        sys.stdout = RedirectText(self.log_text)
        sys.stderr = RedirectText(self.log_text)

        self.apply_runtime_config()
        self.refresh_data(force=True)
        self.show_view("dashboard")


    def apply_runtime_config(self):
        mg.PATH_INVENTARIO = self.state.config.get("inventario_path", mg.PATH_INVENTARIO)
        mg.PATH_MACHOTE = self.state.config.get("machote_path", mg.PATH_MACHOTE)
        mg.PATH_PRECIOS = self.state.config.get("precios_path", mg.PATH_PRECIOS)
        mg.OUTPUT_DIR = self.state.config.get("output_dir", mg.OUTPUT_DIR)

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        style.configure(
            "Treeview",
            background="#162318",
            foreground=OOT_THEME["text"],
            fieldbackground="#162318",
            rowheight=28,
            borderwidth=0,
            font=("Segoe UI", 10),
        )
        style.configure(
            "Treeview.Heading",
            background=OOT_THEME["gold"],
            foreground="#241B0B",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        style.map("Treeview", background=[("selected", OOT_THEME["forest"])])

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=270, fg_color=OOT_THEME["panel"], corner_radius=0, border_width=1, border_color=OOT_THEME["gold"])
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(9, weight=1)

        ctk.CTkLabel(self.sidebar, text=self.state.config.get("logo_text", "MACHOTES OF TIME"), text_color=OOT_THEME["gold"], justify="left", font=ctk.CTkFont(size=28, weight="bold")).grid(row=0, column=0, sticky="w", padx=20, pady=(24, 6))
        ctk.CTkLabel(self.sidebar, text="Panel inspirado en Ocarina of Time", text_color=OOT_THEME["text"], font=ctk.CTkFont(size=12)).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 20))

        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "🗺 Dashboard"),
            ("inventario", "📦 Inventario"),
            ("machotes", "⚔ Generador"),
            ("carga", "🚢 Carga PDF"),
            ("xml", "🧾 Validar XML"),
            ("history", "📜 Historial"),
            ("settings", "🔮 Ajustes"),
        ]
        for idx, (key, label) in enumerate(nav_items, start=2):
            btn = ctk.CTkButton(self.sidebar, text=label, anchor="w", fg_color=OOT_THEME["panel_alt"], hover_color=OOT_THEME["forest_hover"], text_color=OOT_THEME["text"], height=42, command=lambda k=key: self.show_view(k))
            btn.grid(row=idx, column=0, sticky="ew", padx=18, pady=6)
            self.nav_buttons[key] = btn

        quick = ctk.CTkFrame(self.sidebar, fg_color=OOT_THEME["panel_alt"], corner_radius=16, border_width=1, border_color=OOT_THEME["gold"])
        quick.grid(row=10, column=0, sticky="ew", padx=18, pady=18)
        ctk.CTkLabel(quick, text="Atajos del Héroe", text_color=OOT_THEME["gold"], font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=14, pady=(12, 4))
        ctk.CTkButton(quick, text="Recargar datos", fg_color=OOT_THEME["gold"], hover_color=OOT_THEME["gold_hover"], text_color="#221A0C", command=lambda: self.refresh_data(force=True)).pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(quick, text="Abrir carpeta salida", fg_color=OOT_THEME["forest"], hover_color=OOT_THEME["forest_hover"], command=self.open_output_folder).pack(fill="x", padx=12, pady=(0, 12))

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
            "settings": SettingsView(self.main_area, self),
        }
        self.history_view = self.views["history"]

    def create_log_panel(self):
        log_frame = ctk.CTkFrame(self, fg_color=OOT_THEME["panel"], corner_radius=0, border_width=1, border_color=OOT_THEME["gold"])
        log_frame.grid(row=1, column=1, sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(log_frame, text="Sheikah Log", text_color=OOT_THEME["gold"], font=ctk.CTkFont(size=16, weight="bold")).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 4))
        self.log_text = ctk.CTkTextbox(log_frame, height=150, fg_color="#101712", text_color=OOT_THEME["text"], border_width=1, border_color=OOT_THEME["gold"], font=("Consolas", 11))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.log("Santuario inicializado. Bienvenido al reino de los machotes.")

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
        try:
            return f"${float(value):,.2f}"
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
        if self.state.inventory_cache is None or refresh:
            try:
                df_reporte, df_usados, df_xml, df_precios = mg.load_data()
                self.state.inventory_cache = {
                    "reporte": df_reporte,
                    "usados": df_usados,
                    "xml": df_xml,
                    "precios": df_precios,
                }
            except Exception as exc:
                self.log(f"Error cargando datos base: {exc}")
                messagebox.showerror("Datos no disponibles", f"No se pudieron leer los archivos base.\n\n{exc}")
                return None
        return self.state.inventory_cache

    def refresh_data(self, force=False):
        self.state.inventory_cache = None if force else self.state.inventory_cache
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
            btn.configure(fg_color=OOT_THEME["gold"] if active else OOT_THEME["panel_alt"], text_color="#241B0B" if active else OOT_THEME["text"])
        if hasattr(self.views[key], "refresh"):
            self.views[key].refresh()

    def open_output_folder(self):
        output_dir = Path(self.state.config.get("output_dir", mg.OUTPUT_DIR))
        output_dir.mkdir(exist_ok=True)
        self.log(f"Carpeta de salida lista en {output_dir}")
        messagebox.showinfo("Carpeta de salida", f"Ubicación actual:\n\n{output_dir.resolve()}")

    def on_close(self):
        self.state.save_config()
        self.state.save_history()
        self.destroy()


if __name__ == "__main__":
    app = ZeldaApp()
    app.mainloop()