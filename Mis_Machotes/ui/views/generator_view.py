import customtkinter as ctk
import pandas as pd
from tkinter import filedialog, messagebox

import machote_generator as mg
from ui.components import BaseView, MultiSelectMenu, CURRENT_THEME

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
        messagebox.showinfo("Machote creado", f"Se generó correctamente en:\n\n{route}\n\nInventario DB actualizado.")

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
