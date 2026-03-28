import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox

from ui.components import BaseView, MultiSelectMenu, format_color_for_display, CURRENT_THEME
import core.config as config

class InventoryView(BaseView):
    title = "Salón del Inventario"
    subtitle = "Explora, filtra y exporta las piezas disponibles, usadas y facturadas."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(3, weight=0)
        # Row 1: Filters & Search
        filter_controls = ctk.CTkFrame(self, fg_color="transparent")
        filter_controls.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 6))
        filter_controls.grid_columnconfigure(3, weight=1)

        self.sucursal_opt = MultiSelectMenu(filter_controls, title="Sucursal", values=[], command=self.refresh, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"])
        self.sucursal_opt.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.modelo_opt = MultiSelectMenu(filter_controls, title="Modelo", values=[], command=self.refresh, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["panel"])
        self.modelo_opt.grid(row=0, column=1, padx=(0, 10), sticky="w")

        ctk.CTkLabel(filter_controls, text="Buscar:", text_color=CURRENT_THEME["text"]).grid(row=0, column=2, padx=(0, 10), sticky="w")
        self.search_entry = ctk.CTkEntry(filter_controls, placeholder_text="serie, color...")
        self.search_entry.grid(row=0, column=3, sticky="ew")
        self.search_entry.bind("<KeyRelease>", lambda _e: self.refresh())

        ctk.CTkButton(filter_controls, text="X Filtros", width=80, fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], command=self.clear_filters).grid(row=0, column=4, padx=(10, 0), sticky="e")
        self.active_filters_label = ctk.CTkLabel(filter_controls, text="Filtros activos: 0", width=120, text_color=CURRENT_THEME["muted"])
        self.active_filters_label.grid(row=0, column=5, padx=(10, 0), sticky="e")

        # Row 2: Actions & Recargar
        action_controls = ctk.CTkFrame(self, fg_color="transparent")
        action_controls.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 12))
        action_controls.grid_columnconfigure(0, weight=1)

        btn_container = ctk.CTkFrame(action_controls, fg_color="transparent")
        btn_container.grid(row=0, column=0, sticky="e")

        ctk.CTkButton(btn_container, text="Exportar Vista Actual", width=150, fg_color=CURRENT_THEME["emerald"], hover_color=CURRENT_THEME["forest_hover"], command=self.export_view).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_container, text="Exportar Excel Completo", width=170, fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", command=self.export_full_excel).pack(side="left", padx=(0, 10))
        ctk.CTkButton(btn_container, text="Recargar DB", width=100, fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=lambda: self.app.refresh_data(force=True)).pack(side="left")

        totals_frame = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel_alt"], corner_radius=8)
        totals_frame.grid(row=3, column=0, sticky="ew", padx=18)
        self.lbl_totals = ctk.CTkLabel(totals_frame, text="0 piezas visibles · Total: $0.00", text_color=CURRENT_THEME["gold"], font=ctk.CTkFont(weight="bold"))
        self.lbl_totals.pack(padx=14, pady=6, anchor="e")

        self.grid_rowconfigure(4, weight=1)
        self.tabview = ctk.CTkTabview(self, fg_color=CURRENT_THEME["panel"], segmented_button_selected_color=CURRENT_THEME["gold"], segmented_button_selected_hover_color=CURRENT_THEME["gold_hover"], segmented_button_unselected_color=CURRENT_THEME["panel_alt"], command=self.refresh_totals)
        self.tabview.grid(row=4, column=0, sticky="nsew", padx=18, pady=(0, 18))
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

            # Bind right click (Windows: <Button-3>, macOS: <Button-2> or <Control-1>)
            tree.bind("<Button-3>", self._show_context_menu)

            self.trees[tab_name] = tree

        # Create Context Menu
        import tkinter as tk
        self.context_menu = tk.Menu(self, tearoff=0, bg=CURRENT_THEME["panel"], fg=CURRENT_THEME["text"], activebackground=CURRENT_THEME["forest"], activeforeground=CURRENT_THEME["text"], bd=1, relief="solid")
        self.context_menu.add_command(label="Ver Trazabilidad de la Pieza", command=self._show_traceability)

    def _show_context_menu(self, event):
        current_tab = self.tabview.get()
        tree = self.trees[current_tab]

        # Identify row under mouse
        iid = tree.identify_row(event.y)
        if iid:
            tree.selection_set(iid) # Select the row
            try:
                self.context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.context_menu.grab_release()

    def _show_traceability(self):
        current_tab = self.tabview.get()
        tree = self.trees[current_tab]
        selected = tree.selection()
        if not selected:
            return

        values = tree.item(selected[0], "values")
        if not values or len(values) < 4:
            return

        serie = str(values[3]).strip()
        if not serie:
            return

        # Compile history events for this serial
        history = self.app.app_state.history
        trace = []

        for event in history:
            type_ = event.get("type", "")
            action = event.get("action", "")
            timestamp = event.get("timestamp", "")
            details = event.get("details", {})

            # Carga PDF
            if type_ == "carga":
                if serie in details.get("series_importadas", []):
                    pdfs = details.get("pdfs", [])
                    pdf_name = pdfs[0] if pdfs else "Desconocido"
                    trace.append((timestamp, "Ingreso a Almacén (PDF)", f"Desde archivo: {pdf_name}"))

            # Machote Generation (we will need to ensure series_usadas is saved going forward)
            elif type_ in ("machote", "machote_externo"):
                if serie in details.get("series_usadas", []):
                    archivo = details.get("archivo", "Desconocido")
                    trace.append((timestamp, "Asignación a Machote", f"Reservado en: {archivo}"))

            # XML Sync
            elif type_ == "xml":
                if serie in details.get("series_actualizadas", []):
                    carpeta = details.get("carpeta", "Desconocida")
                    trace.append((timestamp, "Conciliación XML (Facturado)", f"Cruce exitoso en carpeta: {carpeta}"))

            # Undos
            elif type_ == "carga_undo":
                # Undo events don't strictly have series lists in older versions, but if we do...
                if "series" in details and serie in details["series"]:
                    trace.append((timestamp, "Reversión de Carga", "Se eliminó el registro de importación."))
            elif type_ == "xml_undo":
                if "series" in details and serie in details["series"]:
                    trace.append((timestamp, "Reversión XML", "Regresó al estado de machote previo."))
            elif type_ == "machote_undo":
                if "series" in details and serie in details["series"]:
                    trace.append((timestamp, "Reversión Machote", "Regresó a estado DISPONIBLE."))

        # If no trace found, add a generic message
        if not trace:
            trace.append(("-", "Registro Preexistente", "Esta pieza fue importada antes de implementar la trazabilidad o vino en la base inicial."))

        # Sort trace chronologically
        trace.sort(key=lambda x: x[0] if x[0] != "-" else "0000")

        # Show Toplevel Window
        top = ctk.CTkToplevel(self)
        top.title(f"Trazabilidad: {serie}")
        top.geometry("600x400")
        top.attributes('-topmost', True)

        # Center window
        x = self.winfo_rootx() + (self.winfo_width() // 2) - 300
        y = self.winfo_rooty() + (self.winfo_height() // 2) - 200
        top.geometry(f"+{x}+{y}")

        main_frame = ctk.CTkFrame(top, fg_color=CURRENT_THEME["panel"], corner_radius=10, border_color=CURRENT_THEME["gold"], border_width=1)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(main_frame, text=f"Línea de Tiempo - Serie: {serie}", font=ctk.CTkFont(size=18, weight="bold"), text_color=CURRENT_THEME["gold"]).pack(pady=(15, 10))

        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 15))

        for date, action, detail in trace:
            card = ctk.CTkFrame(scroll, fg_color=CURRENT_THEME["panel_alt"], corner_radius=8)
            card.pack(fill="x", pady=5)

            ctk.CTkLabel(card, text=date, font=ctk.CTkFont(size=11, weight="bold"), text_color=CURRENT_THEME["emerald"], width=130, anchor="w").grid(row=0, column=0, padx=10, pady=8, sticky="nw")

            content_frame = ctk.CTkFrame(card, fg_color="transparent")
            content_frame.grid(row=0, column=1, sticky="w", pady=8)

            ctk.CTkLabel(content_frame, text=action, font=ctk.CTkFont(size=13, weight="bold"), text_color=CURRENT_THEME["text"], anchor="w").pack(anchor="w")
            ctk.CTkLabel(content_frame, text=detail, font=ctk.CTkFont(size=12), text_color=CURRENT_THEME["muted"], anchor="w").pack(anchor="w")

        ctk.CTkButton(main_frame, text="Cerrar", width=100, fg_color=CURRENT_THEME["gold"], text_color="#0D0D12", hover_color=CURRENT_THEME["gold_hover"], command=top.destroy).pack(pady=(0, 15))

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
        from database import db_export
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
        self.refresh_totals()

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
        cols = ["Sucursal", "Modelo", "Color", "Serie", "Total", "Extra"]
        df = pd.DataFrame(rows, columns=cols)
        out_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], title="Exportar Vista", initialfile=f"Vista_{current_tab}.xlsx")
        if out_path:
            with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name=current_tab[:31])
                worksheet = writer.sheets[current_tab[:31]]
                for idx, col in enumerate(df.columns):
                    max_len = len(str(col))
                    if not df[col].empty:
                        col_max = df[col].astype(str).map(len).max()
                        if not pd.isna(col_max):
                            max_len = max(max_len, col_max)
                    worksheet.column_dimensions[chr(65 + idx)].width = max_len + 2
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

        filter_sucs = sucursal_filter != all_sucs
        filter_mods = modelo_filter != all_mods

        for name, (df, extra_col) in mapping.items():
            tree = self.trees[name]
            for item in tree.get_children():
                tree.delete(item)

            if df is None or df.empty:
                continue

            mask = pd.Series(True, index=df.index)

            if filter_sucs and "SUCURSAL" in df.columns:
                mask = mask & df["SUCURSAL"].astype(str).isin(sucursal_filter)

            if filter_mods and "MODELO BASE" in df.columns:
                mask = mask & df["MODELO BASE"].astype(str).isin(modelo_filter)

            filtered_df = df[mask]

            if term:
                text_mask = pd.Series(False, index=filtered_df.index)
                for col in ["SUCURSAL", "MODELO BASE", "COLOR", "No de SERIE:", "TOTAL"]:
                    if col in filtered_df.columns:
                        text_mask = text_mask | filtered_df[col].astype(str).str.lower().str.contains(term, na=False, regex=False)
                if extra_col and extra_col in filtered_df.columns:
                     text_mask = text_mask | filtered_df[extra_col].astype(str).str.lower().str.contains(term, na=False, regex=False)
                filtered_df = filtered_df[text_mask]

            # Vectorized creation of values
            if not filtered_df.empty:
                # Prepare columns safely
                suc_col = filtered_df["SUCURSAL"].astype(str) if "SUCURSAL" in filtered_df.columns else pd.Series([""] * len(filtered_df), index=filtered_df.index)
                mod_col = filtered_df["MODELO BASE"].astype(str) if "MODELO BASE" in filtered_df.columns else pd.Series([""] * len(filtered_df), index=filtered_df.index)
                color_col = filtered_df["COLOR"].apply(lambda x: format_color_for_display(x)) if "COLOR" in filtered_df.columns else pd.Series([""] * len(filtered_df), index=filtered_df.index)
                serie_col = filtered_df["No de SERIE:"].astype(str) if "No de SERIE:" in filtered_df.columns else pd.Series([""] * len(filtered_df), index=filtered_df.index)
                total_col = filtered_df["TOTAL"].apply(lambda x: self.app.money(x)) if "TOTAL" in filtered_df.columns else pd.Series(["$0.00"] * len(filtered_df), index=filtered_df.index)
                extra_c = filtered_df[extra_col].astype(str) if extra_col and extra_col in filtered_df.columns else pd.Series([""] * len(filtered_df), index=filtered_df.index)

                # Combine into list of tuples for quick insertion
                data_to_insert = zip(suc_col, mod_col, color_col, serie_col, total_col, extra_c)
                for row_vals in data_to_insert:
                     tree.insert("", "end", values=row_vals)

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
