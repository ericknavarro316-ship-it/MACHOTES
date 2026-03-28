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
from ui.components import TreeBundle, CURRENT_THEME, update_theme_colors
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

        # Apply theme colors before building UI
        theme_mode = self.app_state.config.get("theme_mode", "Dark")
        custom_colors = {
            "bg": self.app_state.config.get("custom_color_bg", "#121212"),
            "panel": self.app_state.config.get("custom_color_panel", "#1E1E1E"),
            "panel_alt": self.app_state.config.get("custom_color_panel", "#2C2C2C"), # slightly lighter than panel usually, but user only inputs panel
            "gold": self.app_state.config.get("custom_color_gold", "#3498DB"),
            "gold_hover": self.app_state.config.get("custom_color_gold", "#2980B9"),
            "forest": self.app_state.config.get("custom_color_forest", "#2ECC71"),
            "forest_hover": self.app_state.config.get("custom_color_forest", "#27AE60"),
            "emerald": self.app_state.config.get("custom_color_forest", "#2ECC71"), # Use forest for emerald
            "text": self.app_state.config.get("custom_color_text", "#FFFFFF"),
            "muted": "#95A5A6",
            "danger": "#E74C3C",
            "danger_hover": "#C0392B",
            "warning": "#F1C40F",
            "sky": "#3498DB",
        }
        update_theme_colors(theme_mode, custom_colors)

        app_name = self.app_state.config.get("logo_text", "MACHOTES OF TIME")
        self.title(f"{app_name} · Admin Panel")
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

        # Start smart assistant watcher
        self.after(5000, self._xml_watcher_tick)
        self.after(2000, self._check_zero_prices)

    def _check_zero_prices(self):
        inventory = self.get_inventory_data(refresh=False)
        if inventory and inventory.get("reporte") is not None:
            df = inventory["reporte"]
            if not df.empty and "TOTAL" in df.columns:
                zero_prices = df[pd.to_numeric(df["TOTAL"], errors='coerce').fillna(0) <= 0]
                if not zero_prices.empty:
                    from tkinter import messagebox
                    count = len(zero_prices)
                    self.log(f"Asistente: Detectadas {count} piezas en DISPONIBLES con precio $0.00.")
                    messagebox.showwarning("Asistente Inteligente: Precios en $0.00", f"Se detectaron {count} artículos disponibles que no tienen un precio asignado.\n\nEs posible que falte registrar el modelo en la lista de Excel o hayas escrito mal el nombre de la columna de precio en la configuración.")


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

        # Load custom logo image if exists
        self.logo_img_ctk = None
        self.logo_img_collapsed_ctk = None
        self.has_custom_logo = False
        try:
            from PIL import Image
            custom_logo_path = Path(self.app_state.config.get("output_dir", config.OUTPUT_DIR)).parent / "app_data" / "custom_logo.png"
            if custom_logo_path.exists():
                img = Image.open(custom_logo_path)
                self.logo_img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(160, max(40, int(160 * img.height / img.width))))
                self.logo_img_collapsed_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(40, max(10, int(40 * img.height / img.width))))
                self.has_custom_logo = True
        except Exception as e:
            self.log(f"No se pudo cargar el logo personalizado: {e}")

        if self.has_custom_logo:
            self.logo_label = ctk.CTkLabel(self.sidebar_header, text="", image=self.logo_img_ctk, justify="center")
        else:
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

        subtitle_text = "Panel de control administrativo" if self.has_custom_logo else "Panel inspirado en Ocarina of Time"
        self.sidebar_subtitle = ctk.CTkLabel(self.sidebar, text=subtitle_text, text_color=CURRENT_THEME["text"], font=ctk.CTkFont(size=12))
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
            if self.has_custom_logo:
                self.logo_label.configure(image=self.logo_img_collapsed_ctk, text="")
            else:
                self.logo_label.configure(text="△")
            self.sidebar_subtitle.grid_remove()
            self.quick.grid_remove()
            self.sidebar_toggle_btn.configure(text="👁")
            for key, btn in self.nav_buttons.items():
                icon = self.nav_labels_full[key].split(" ")[0]
                btn.configure(text=icon, anchor="center")
        else:
            self.sidebar.configure(width=270)
            if self.has_custom_logo:
                self.logo_label.configure(image=self.logo_img_ctk, text="")
            else:
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

        self.global_search_var = tk.StringVar()
        self.global_search_entry = ctk.CTkEntry(
            header,
            textvariable=self.global_search_var,
            placeholder_text="Buscar serie rápida...",
            width=180,
            height=28
        )
        self.global_search_entry.grid(row=0, column=1, sticky="e", padx=(0, 10))
        self.global_search_entry.bind("<Return>", self.perform_global_search)

        ctk.CTkButton(header, text="Buscar", width=60, height=28, fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.perform_global_search).grid(row=0, column=2, sticky="e", padx=(0, 10))

        self.log_toggle_btn = ctk.CTkButton(
            header,
            text="◣",
            width=40,
            height=28,
            fg_color=CURRENT_THEME["panel_alt"],
            hover_color=CURRENT_THEME["forest_hover"],
            command=self.toggle_log_panel,
        )
        self.log_toggle_btn.grid(row=0, column=3, sticky="e", padx=(6, 0))

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
            self.grid_rowconfigure(1, weight=0, minsize=0)
            self.log_text.grid()
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

    def perform_global_search(self, event=None):
        term = self.global_search_var.get().strip().lower()
        if not term:
            return

        inventory = self.get_inventory_data(refresh=False)
        if not inventory:
            self.log("Búsqueda global: no hay datos cargados.")
            return

        found = []
        for state_name, db_key in [("Disponible", "reporte"), ("Usado", "usados"), ("XML", "xml")]:
            df = inventory.get(db_key)
            if df is not None and not df.empty and "No de SERIE:" in df.columns:
                match = df[df["No de SERIE:"].astype(str).str.lower().str.contains(term, na=False, regex=False)]
                if not match.empty:
                    for _, row in match.iterrows():
                        found.append({
                            "Estado": state_name,
                            "Serie": str(row.get("No de SERIE:", "")),
                            "Modelo": str(row.get("MODELO BASE", "")),
                            "Sucursal": str(row.get("SUCURSAL", ""))
                        })

        if not found:
            messagebox.showinfo("Búsqueda Global", f"No se encontró nada con '{term}'.")
            self.log(f"Búsqueda global: '{term}' sin resultados.")
            return

        msg = f"Resultados para '{term}':\n\n"
        for item in found:
            msg += f"[{item['Estado']}] {item['Serie']} - {item['Modelo']} ({item['Sucursal']})\n"

        if len(found) == 1:
            msg += "\n¿Ir al Inventario y filtrar?"
            if messagebox.askyesno("Búsqueda Global", msg):
                self.show_view("inventario")
                inv_view = self.views["inventario"]
                inv_view.clear_filters()

                state_to_tab = {"Disponible": "Disponibles", "Usado": "Usados", "XML": "XML"}
                inv_view.tabview.set(state_to_tab[found[0]["Estado"]])

                inv_view.search_entry.delete(0, "end")
                inv_view.search_entry.insert(0, found[0]["Serie"])
                inv_view.refresh()
        else:
            messagebox.showinfo("Búsqueda Global", msg)

        self.global_search_var.set("")
        self.log(f"Búsqueda global: {len(found)} resultados para '{term}'.")

    def open_output_folder(self):
        output_dir = Path(self.app_state.config.get("output_dir", config.OUTPUT_DIR))
        output_dir.mkdir(exist_ok=True)
        self.log(f"Carpeta de salida lista en {output_dir}")
        messagebox.showinfo("Carpeta de salida", f"Ubicación actual:\n\n{output_dir.resolve()}")

    def _xml_watcher_tick(self):
        watcher_path = self.app_state.config.get("xml_watcher_path", "").strip()
        if watcher_path:
            import glob
            import os
            try:
                xml_files = glob.glob(os.path.join(watcher_path, "*.xml"))
                if xml_files:
                    self.log(f"Asistente: Detectados {len(xml_files)} XMLs nuevos en la carpeta vigilada. Procesando...")
                    self.run_in_thread(lambda: self._process_watched_xmls(watcher_path))
            except Exception as e:
                self.log(f"Error en watcher XML: {e}")

        # Check again in 30 seconds
        self.after(30000, self._xml_watcher_tick)

    def _process_watched_xmls(self, watcher_path):
        try:
            output_path, series_actualizadas = mg.validar_xml_y_reemplazar(watcher_path)

            # Move processed files to a subfolder so they aren't processed again
            import os, shutil
            processed_dir = os.path.join(watcher_path, "procesados")
            os.makedirs(processed_dir, exist_ok=True)
            import glob
            for xml_file in glob.glob(os.path.join(watcher_path, "*.xml")):
                try:
                    shutil.move(xml_file, os.path.join(processed_dir, os.path.basename(xml_file)))
                except Exception as move_err:
                    self.log(f"Asistente: No se pudo mover {xml_file}: {move_err}")

            self.after(0, lambda: self._on_watched_xml_success(watcher_path, output_path, series_actualizadas))
        except Exception as e:
            self.after(0, lambda: self.log(f"Asistente: Error procesando XMLs automáticamente: {e}"))

    def _on_watched_xml_success(self, folder, output_path, series_actualizadas):
        if series_actualizadas:
            self.app_state.record_event("xml", "UUIDs conciliados automáticamente", {
                "carpeta": folder,
                "inventario": output_path,
                "series_actualizadas": series_actualizadas
            })
            self.refresh_data(force=True)
            try:
                from plyer import notification
                app_name = self.app_state.config.get("logo_text", "MACHOTES OF TIME")
                notification.notify(
                    title=app_name,
                    message=f"Asistente: Auto-conciliación de XML completada ({len(series_actualizadas)} piezas).",
                    app_name=app_name,
                    timeout=5
                )
            except Exception as e:
                self.log(f"Asistente: Notificación fallida: {e}")
            self.log(f"Asistente: XMLs auto-conciliados exitosamente ({len(series_actualizadas)} UUIDs).")

    def on_close(self):
        self._perform_auto_backup()
        self.app_state.save_config()
        self.app_state.save_history()
        self.destroy()

    def _perform_auto_backup(self):
        auto_backup = self.app_state.config.get("auto_backup_enabled", "False")
        backup_path = self.app_state.config.get("auto_backup_path", "").strip()

        if auto_backup == "True" and backup_path:
            import shutil
            from datetime import datetime
            from core.config import PATH_INVENTARIO

            target_dir = Path(backup_path)
            if target_dir.exists() and target_dir.is_dir():
                try:
                    db_path = Path(PATH_INVENTARIO).resolve()
                    if db_path.exists():
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        target_file = target_dir / f"inventory_backup_{timestamp}.db"
                        shutil.copy2(db_path, target_file)

                        # Keep only last 10 backups in that folder to save space
                        backups = sorted(target_dir.glob("inventory_backup_*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
                        if len(backups) > 10:
                            for old_backup in backups[10:]:
                                old_backup.unlink(missing_ok=True)
                except Exception as e:
                    self.log(f"Error realizando auto-respaldo: {e}")


if __name__ == "__main__":
    app = ZeldaApp()
    app.mainloop()
