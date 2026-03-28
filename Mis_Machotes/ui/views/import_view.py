import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
import os
from datetime import datetime

import machote_generator as mg
from ui.components import BaseView, format_color_for_display, CURRENT_THEME
from plyer import notification

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
        self.grid_rowconfigure(1, weight=1)

        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        main_split.grid_rowconfigure(0, weight=1)
        main_split.grid_columnconfigure(0, weight=1) # List panel
        main_split.grid_columnconfigure(1, weight=2) # Workspace panel

        # --- LEFT PANEL (History) ---
        list_card = ctk.CTkFrame(main_split, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        list_card.grid_rowconfigure(1, weight=1)
        list_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(list_card, text="Historial de Cargas", font=ctk.CTkFont(size=16, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))

        self.history_tree = self.app.create_treeview(list_card, [
            ("fecha", "Fecha", 140),
            ("info", "Información", 250),
        ])
        self.history_tree.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.history_tree.bind("<<TreeviewSelect>>", self.on_history_selected)

        btn_new_import = ctk.CTkButton(list_card, text="+ Nueva Carga", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.reset_workspace)
        btn_new_import.grid(row=2, column=0, pady=12, padx=12, sticky="ew")

        # --- RIGHT PANEL (Workspace/Details) ---
        self.workspace_card = ctk.CTkFrame(main_split, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        self.workspace_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self.workspace_card.grid_rowconfigure(3, weight=1)
        self.workspace_card.grid_columnconfigure(0, weight=1)

        # Header of Workspace
        self.header_frame = ctk.CTkFrame(self.workspace_card, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.workspace_title = ctk.CTkLabel(self.header_frame, text="Nueva Carga de Mercancía", font=ctk.CTkFont(size=18, weight="bold"), text_color=CURRENT_THEME["gold"])
        self.workspace_title.grid(row=0, column=0, sticky="w")

        # Action buttons for New Import
        self.action_frame_new = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.action_frame_new.grid(row=0, column=1, sticky="e")
        ctk.CTkButton(self.action_frame_new, text="Elegir PDF", fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", width=80, command=self.select_pdf).pack(side="left")
        ctk.CTkButton(self.action_frame_new, text="Elegir Excel", fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", width=80, command=self.select_excel).pack(side="left", padx=(10, 0))
        ctk.CTkButton(self.action_frame_new, text="Limpiar", width=60, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"], command=self.clear_loaded_pdf).pack(side="left", padx=(10, 0))
        ctk.CTkButton(self.action_frame_new, text="Simular", width=60, fg_color=CURRENT_THEME["warning"], hover_color="#A55A18", command=self.simulate_import).pack(side="left", padx=10)
        ctk.CTkButton(self.action_frame_new, text="Warnings", width=70, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"], command=self.show_parse_warnings).pack(side="left", padx=(0, 10))
        ctk.CTkButton(self.action_frame_new, text="Importar", width=80, fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.import_pdf).pack(side="left", padx=10)

        # Action buttons for History Details
        self.action_frame_hist = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.btn_undo = ctk.CTkButton(self.action_frame_hist, text="Deshacer Importación", fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], command=self.undo_selected_import)
        self.btn_undo.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(self.workspace_card, fg_color=CURRENT_THEME["panel_alt"], progress_color=CURRENT_THEME["gold"], height=4)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 5))
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        self.summary_label = ctk.CTkLabel(self.workspace_card, text="Sin archivo seleccionado.", text_color=CURRENT_THEME["muted"])
        self.summary_label.grid(row=2, column=0, sticky="w", padx=18)

        self.preview_tree = self.app.create_treeview(self.workspace_card, [
            ("incluir", "Incluir", 60),
            ("archivo", "Archivo", 170),
            ("sucursal", "Sucursal", 120),
            ("modelo", "Modelo", 180),
            ("color", "Color", 100),
            ("serie", "Serie", 180),
        ])
        self.preview_tree.grid(row=3, column=0, sticky="nsew", padx=12, pady=(8, 12))
        self.preview_tree.bind("<Double-1>", self.toggle_inclusion)
        self.preview_tree.bind("<space>", self.toggle_inclusion_keyboard)

        self.reset_workspace()
        self.refresh()

    def refresh(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        cargas = [m for m in self.app.app_state.history if m.get("type") == "carga"]

        for idx, entry in enumerate(cargas):
            details = entry.get("details", {})
            series_importadas = details.get("series_importadas", [])
            pdfs = details.get("pdfs", [])

            info = f"{len(series_importadas)} piezas "
            if pdfs:
                import os
                info += f"({os.path.basename(pdfs[0])})"

            self.history_tree.insert("", "end", iid=str(idx), values=(entry.get("timestamp", ""), info))

    def on_history_selected(self, event):
        selected = self.history_tree.selection()
        if not selected:
            return

        idx = int(selected[0])
        cargas = [m for m in self.app.app_state.history if m.get("type") == "carga"]
        entry = cargas[idx]
        details = entry.get("details", {})
        series_importadas = details.get("series_importadas", [])

        self.workspace_title.configure(text=f"Detalle de Carga: {entry.get('timestamp', '').split(' ')[0]}")
        self.summary_label.configure(text=f"Esta carga introdujo {len(series_importadas)} artículos.")

        self.action_frame_new.grid_remove()
        self.action_frame_hist.grid(row=0, column=1, sticky="e")

        # Populate mini inventory
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        inventory = self.app.get_inventory_data(refresh=False)
        if inventory and inventory.get("reporte") is not None:
            df_rep = inventory.get("reporte")
            if "No de SERIE:" in df_rep.columns:
                series_set = set(series_importadas)
                items_to_show = df_rep[df_rep["No de SERIE:"].astype(str).str.strip().isin(series_set)]
                for _, row in items_to_show.iterrows():
                    color_display = self._format_color_for_display(row.get("COLOR", ""))
                    self.preview_tree.insert("", "end", values=(
                        "-",
                        "Historial",
                        str(row.get("SUCURSAL", "")),
                        str(row.get("MODELO BASE", "")),
                        color_display,
                        str(row.get("No de SERIE:", ""))
                    ))

    def reset_workspace(self):
        self.history_tree.selection_remove(self.history_tree.selection())
        self.workspace_title.configure(text="Nueva Carga de Mercancía")
        self.action_frame_hist.grid_remove()
        self.action_frame_new.grid(row=0, column=1, sticky="e")
        self.clear_loaded_pdf()

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
            self.preview_tree.insert("", "end", values=("☑", item.get("_source_pdf", ""), item.get("SUCURSAL", ""), item.get("MODELO BASE", ""), color_display, item.get("No de SERIE:", "")), tags=(str(idx),))
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

    def select_excel(self):
        excel_path = filedialog.askopenfilename(title="Seleccionar Excel de mercancía", filetypes=[("Excel", "*.xlsx *.xls")])
        if not excel_path:
            return
        self.selected_pdfs = [excel_path]  # Reuse the same variable for simplicity
        self.selected_pdf.set(f"Excel seleccionado: {os.path.basename(excel_path)}")

        try:
            items, warnings, report = mg.extraer_nuevos_articulos_excel(excel_path, with_report=True)
            for it in items:
                it["_source_pdf"] = os.path.basename(excel_path)
            self.items_loaded = items
            self.parse_warnings = warnings
            self.parse_report = report
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo procesar el Excel:\n{exc}")
            return

        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        for idx, item in enumerate(self.items_loaded):
            color_display = self._format_color_for_display(item.get("COLOR", ""))
            self.preview_tree.insert("", "end", values=("☑", item.get("_source_pdf", ""), item.get("SUCURSAL", ""), item.get("MODELO BASE", ""), color_display, item.get("No de SERIE:", "")), tags=(str(idx),))

        inv = self.app.get_inventory_data(refresh=False) or {}
        existentes = set()
        for key in ("reporte", "usados", "xml"):
            df = inv.get(key)
            if df is not None and not df.empty and "No de SERIE:" in df.columns:
                existentes.update(df["No de SERIE:"].astype(str).str.strip().tolist())

        duplicados = sum(1 for item in self.items_loaded if str(item.get("No de SERIE:", "")).strip() in existentes)
        self.summary_label.configure(text=f"Se detectaron {len(self.items_loaded)} artículos únicos en el Excel ({duplicados} potencialmente duplicados).")
        self.app.log(f"Excel analizado: {os.path.basename(excel_path)} con {len(self.items_loaded)} artículos.")

    def _format_color_for_display(self, color_value):
        return format_color_for_display(color_value)

    def undo_selected_import(self):
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona una carga del historial para deshacer.")
            return

        idx = int(selected[0])
        cargas = [m for m in self.app.app_state.history if m.get("type") == "carga"]
        entry = cargas[idx]

        details = entry.get("details", {})
        imported_series = details.get("series_importadas", [])

        if not imported_series:
            messagebox.showwarning("Sin datos", "El registro seleccionado no contiene series específicas para deshacer.")
            return

        confirm = messagebox.askyesno(
            "Deshacer Importación",
            f"Se detectó una carga el {entry.get('timestamp')}.\n\n"
            f"¿Estás seguro de que deseas ELIMINAR los {len(imported_series)} artículos importados en ese momento?\n\n"
            "Solo se eliminarán si siguen estando 'DISPONIBLES'."
        )

        if not confirm:
            return

        from database import db_manager
        try:
            deleted = db_manager.undo_last_import(imported_series)
            self.app.app_state.record_event("carga_undo", f"Carga revertida: {deleted} piezas eliminadas.")

            # Remove from history
            self.app.app_state.history.remove(entry)
            self.app.app_state.save_history()

            self.app.refresh_data(force=True)
            self.app.history_view.refresh()
            self.refresh()
            self.reset_workspace()

            self.summary_label.configure(text=f"Carga revertida. {deleted} artículos eliminados de la base de datos.", text_color=CURRENT_THEME["emerald"])
            self.app.log(f"Reversión de carga completada. {deleted} piezas eliminadas.")
            messagebox.showinfo("Reversión completada", f"Se eliminaron {deleted} artículos de la base de datos.")
        except Exception as exc:
            self.app.log(f"Error revirtiendo carga: {exc}")
            messagebox.showerror("Error revirtiendo", f"No se pudo revertir la carga.\n\n{exc}")

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

    def _get_selected_items(self):
        selected_items = []
        for item_id in self.preview_tree.get_children():
            values = self.preview_tree.item(item_id, "values")
            if values[0] in ("[X]", "☑"):
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
        if values[0] in ("[X]", "☑"):
            values[0] = "☐"
        else:
            values[0] = "☑"
        self.preview_tree.item(item_id, values=values)

    def toggle_inclusion_keyboard(self, event):
        selected = self.preview_tree.selection()
        if not selected:
            return
        for item_id in selected:
            values = list(self.preview_tree.item(item_id, "values"))
            if values[0] in ("[X]", "☑"):
                values[0] = "☐"
            else:
                values[0] = "☑"
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
        self.progress_bar.grid()
        self.progress_bar.start()

        def _task():
            try:
                output_path = mg.cargar_inventario_y_reemplazar(self.selected_pdfs[0], lista_articulos=selected_items)
                self.app.after(0, self._import_success, output_path, selected_items, list(self.selected_pdfs))
            except Exception as exc:
                self.app.after(0, self._import_error, exc)

        self.app.run_in_thread(_task)

    def _import_success(self, output_path, selected_items, pdf_paths):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        series_importadas = [str(item.get("No de SERIE:", "")) for item in selected_items]
        self.app.app_state.record_event(
            "carga",
            f"Mercancía importada ({len(selected_items)} piezas)",
            {"pdfs": pdf_paths, "inventario": output_path, "series_importadas": series_importadas},
        )
        self.app.refresh_data(force=True)
        self.app.history_view.refresh()
        self.refresh()
        self.reset_workspace()
        self.summary_label.configure(text=f"Carga completa. {len(selected_items)} artículos importados en DB.", text_color=CURRENT_THEME["emerald"])
        self.app.log(f"Reporte post-carga: seleccionados={len(selected_items)} warnings_parseo={len(self.parse_warnings)}")
        self.app.log(f"Mercancía importada: {len(selected_items)} piezas desde {len(pdf_paths)} PDF(s).")
        try:
            app_name = self.app.app_state.config.get("logo_text", "MACHOTES OF TIME")
            notification.notify(
                title=app_name,
                message=f"Carga completada: {len(selected_items)} piezas guardadas en base de datos.",
                app_name=app_name,
                timeout=5
            )
        except Exception as e:
            self.app.log(f"No se pudo mostrar la notificación nativa: {e}")
        messagebox.showinfo("Carga completada", f"Se guardaron {len(selected_items)} piezas en base de datos.")

    def _import_error(self, exc):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        import traceback
        self.summary_label.configure(text="Error durante la importación.", text_color=CURRENT_THEME["danger"])
        self.app.log(f"Error importando PDF:\n{traceback.format_exc()}")
        messagebox.showerror("Error importando", f"No se pudo cargar la mercancía.\n\n{exc}")
