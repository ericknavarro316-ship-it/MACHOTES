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
