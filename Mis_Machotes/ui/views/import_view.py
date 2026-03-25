import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox
import os
from datetime import datetime

import machote_generator as mg
from ui.components import BaseView, format_color_for_display, CURRENT_THEME

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

        self.progress_bar = ctk.CTkProgressBar(card, fg_color=CURRENT_THEME["panel_alt"], progress_color=CURRENT_THEME["gold"], height=4)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 5))
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        self.summary_label = ctk.CTkLabel(card, text="Sin PDF seleccionado.", text_color=CURRENT_THEME["muted"])
        self.summary_label.grid(row=2, column=0, sticky="w", padx=18)

        self.preview_tree = self.app.create_treeview(card, [
            ("incluir", "Incluir", 60),
            ("archivo", "Archivo", 170),
            ("sucursal", "Sucursal", 120),
            ("modelo", "Modelo", 180),
            ("color", "Color", 100),
            ("serie", "Serie", 180),
        ])
        self.preview_tree.grid(row=3, column=0, sticky="nsew", padx=12, pady=(8, 12))
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
        return format_color_for_display(color_value)

    def undo_last_import(self):
        from database import db_manager
        last_carga = next((m for m in self.app.app_state.history if m.get("type") == "carga"), None)

        if not last_carga:
            messagebox.showwarning("Sin historial", "No hay un registro reciente de carga para deshacer.")
            return

        details = last_carga.get("details", {})
        imported_series = details.get("series_importadas", [])

        if not imported_series:
            messagebox.showwarning("Sin datos", "El registro de la última carga no contiene series específicas para deshacer.")
            return

        confirm = messagebox.askyesno(
            "Deshacer Importación",
            f"Se detectó una carga el {last_carga.get('timestamp')}.\n\n"
            f"¿Estás seguro de que deseas ELIMINAR los {len(imported_series)} artículos importados en ese momento?\n\n"
            "Solo se eliminarán si siguen estando 'DISPONIBLES'."
        )

        if not confirm:
            return

        try:
            deleted = db_manager.undo_last_import(imported_series)
            self.app.app_state.record_event("carga_undo", f"Carga revertida: {deleted} piezas eliminadas.")
            self.app.refresh_data(force=True)
            self.app.history_view.refresh()
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
        self.summary_label.configure(text=f"Carga completa. {len(selected_items)} artículos importados en DB.", text_color=CURRENT_THEME["emerald"])
        self.app.log(f"Reporte post-carga: seleccionados={len(selected_items)} warnings_parseo={len(self.parse_warnings)}")
        self.app.log(f"Mercancía importada: {len(selected_items)} piezas desde {len(pdf_paths)} PDF(s).")
        messagebox.showinfo("Carga completada", f"Se guardaron {len(selected_items)} piezas en base de datos.")

    def _import_error(self, exc):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        import traceback
        self.summary_label.configure(text="Error durante la importación.", text_color=CURRENT_THEME["danger"])
        self.app.log(f"Error importando PDF:\n{traceback.format_exc()}")
        messagebox.showerror("Error importando", f"No se pudo cargar la mercancía.\n\n{exc}")
