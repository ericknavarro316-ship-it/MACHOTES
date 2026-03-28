import customtkinter as ctk
from tkinter import filedialog, messagebox
import machote_generator as mg
from ui.components import BaseView, CURRENT_THEME
from plyer import notification

class XMLView(BaseView):
    title = "Templo de UUID"
    subtitle = "Cruza XMLs, encuentra coincidencias y mueve piezas facturadas a su santuario correcto."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.selected_dir = ctk.StringVar(value="")
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

        ctk.CTkLabel(list_card, text="Historial de XMLs", font=ctk.CTkFont(size=16, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))

        self.history_tree = self.app.create_treeview(list_card, [
            ("fecha", "Fecha", 140),
            ("info", "Carpeta", 250),
        ])
        self.history_tree.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.history_tree.bind("<<TreeviewSelect>>", self.on_history_selected)

        btn_new_sync = ctk.CTkButton(list_card, text="+ Nueva Conciliación", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.reset_workspace)
        btn_new_sync.grid(row=2, column=0, pady=12, padx=12, sticky="ew")

        # --- RIGHT PANEL (Workspace/Details) ---
        self.workspace_card = ctk.CTkFrame(main_split, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        self.workspace_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self.workspace_card.grid_rowconfigure(3, weight=1)
        self.workspace_card.grid_columnconfigure(0, weight=1)

        # Header of Workspace
        self.header_frame = ctk.CTkFrame(self.workspace_card, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.workspace_title = ctk.CTkLabel(self.header_frame, text="Nueva Conciliación XML", font=ctk.CTkFont(size=18, weight="bold"), text_color=CURRENT_THEME["gold"])
        self.workspace_title.grid(row=0, column=0, sticky="w")

        # Action buttons for New Sync
        self.action_frame_new = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.action_frame_new.grid(row=0, column=1, sticky="e")
        ctk.CTkButton(self.action_frame_new, text="Elegir carpeta XML", fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", command=self.select_dir).pack(side="left")
        ctk.CTkButton(self.action_frame_new, text="Validar y actualizar", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.process_xml).pack(side="left", padx=10)

        # Action buttons for History Details
        self.action_frame_hist = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.btn_undo = ctk.CTkButton(self.action_frame_hist, text="Deshacer Conciliación", fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], command=self.undo_selected_xml)
        self.btn_undo.pack(side="right")

        self.progress_bar = ctk.CTkProgressBar(self.workspace_card, fg_color=CURRENT_THEME["panel_alt"], progress_color=CURRENT_THEME["gold"], height=4)
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 5))
        self.progress_bar.set(0)
        self.progress_bar.grid_remove()

        self.summary_label = ctk.CTkLabel(self.workspace_card, text="Aún no se ha inspeccionado ninguna carpeta.", text_color=CURRENT_THEME["muted"])
        self.summary_label.grid(row=2, column=0, sticky="w", padx=18)

        self.preview_tree = self.app.create_treeview(self.workspace_card, [
            ("serie", "Serie", 180),
            ("uuid", "UUID", 250),
            ("machote", "Machote", 200),
        ])
        self.preview_tree.grid(row=3, column=0, sticky="nsew", padx=12, pady=(8, 12))

        self.reset_workspace()
        self.refresh()

    def refresh(self):
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        xmls = [m for m in self.app.app_state.history if m.get("type") == "xml"]

        for idx, entry in enumerate(xmls):
            details = entry.get("details", {})
            carpeta = details.get("carpeta", "")
            import os
            self.history_tree.insert("", "end", iid=str(idx), values=(entry.get("timestamp", ""), os.path.basename(carpeta)))

    def on_history_selected(self, event):
        selected = self.history_tree.selection()
        if not selected:
            return

        idx = int(selected[0])
        xmls = [m for m in self.app.app_state.history if m.get("type") == "xml"]
        entry = xmls[idx]
        details = entry.get("details", {})
        carpeta = details.get("carpeta", "")
        series_actualizadas = details.get("series_actualizadas", [])

        import os
        self.workspace_title.configure(text=f"Carpeta: {os.path.basename(carpeta)}")
        self.summary_label.configure(text=f"Se conciliarion {len(series_actualizadas)} UUIDs.")

        self.action_frame_new.grid_remove()
        self.action_frame_hist.grid(row=0, column=1, sticky="e")

        # Populate mini inventory
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

        inventory = self.app.get_inventory_data(refresh=False)
        if inventory and inventory.get("xml") is not None:
            df_xml = inventory.get("xml")
            if "No de SERIE:" in df_xml.columns:
                series_set = set(series_actualizadas)
                items_to_show = df_xml[df_xml["No de SERIE:"].astype(str).str.strip().isin(series_set)]
                for _, row in items_to_show.iterrows():
                    self.preview_tree.insert("", "end", values=(
                        str(row.get("No de SERIE:", "")),
                        str(row.get("UUID", "")),
                        str(row.get("MACHOTE", ""))
                    ))

    def reset_workspace(self):
        self.history_tree.selection_remove(self.history_tree.selection())
        self.workspace_title.configure(text="Nueva Conciliación XML")
        self.action_frame_hist.grid_remove()
        self.action_frame_new.grid(row=0, column=1, sticky="e")
        self.selected_dir.set("")
        self.summary_label.configure(text="Aún no se ha inspeccionado ninguna carpeta.", text_color=CURRENT_THEME["muted"])
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)

    def undo_selected_xml(self):
        selected = self.history_tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona una conciliación del historial para deshacer.")
            return

        idx = int(selected[0])
        xmls = [m for m in self.app.app_state.history if m.get("type") == "xml"]
        entry = xmls[idx]

        details = entry.get("details", {})
        series_actualizadas = details.get("series_actualizadas", [])

        if not series_actualizadas:
            messagebox.showwarning("Sin datos", "El registro seleccionado no contiene series específicas para deshacer.")
            return

        confirm = messagebox.askyesno(
            "Deshacer Conciliación XML",
            f"Se detectó una conciliación el {entry.get('timestamp')}.\n\n"
            f"¿Estás seguro de que deseas revertir los {len(series_actualizadas)} UUIDs asignados?\n\n"
            "Los artículos volverán a su estado anterior (USADO si tenían machote, DISPONIBLE en caso contrario)."
        )

        if not confirm:
            return

        from database import db_manager
        try:
            deleted = db_manager.undo_xml_import(series_actualizadas)
            self.app.app_state.record_event("xml_undo", f"Conciliación revertida: {deleted} UUIDs eliminados.", {"series": series_actualizadas})

            # Remove from history
            self.app.app_state.history.remove(entry)
            self.app.app_state.save_history()

            self.app.refresh_data(force=True)
            self.app.history_view.refresh()
            self.refresh()
            self.reset_workspace()

            self.summary_label.configure(text=f"Conciliación revertida. {deleted} artículos restaurados.", text_color=CURRENT_THEME["emerald"])
            self.app.log(f"Reversión de conciliación completada. {deleted} UUIDs eliminados.")
            messagebox.showinfo("Reversión completada", f"Se restauraron {deleted} artículos en la base de datos.")
        except Exception as exc:
            self.app.log(f"Error revirtiendo conciliación: {exc}")
            messagebox.showerror("Error revirtiendo", f"No se pudo revertir la conciliación.\n\n{exc}")

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
            self.preview_tree.insert("", "end", values=(serie, uuid, "Por asignar"))
        self.summary_label.configure(text=f"Se encontraron {len(results)} series en los XML analizados.")
        self.app.log(f"Carpeta XML analizada: {folder}")

    def process_xml(self):
        folder = self.selected_dir.get().strip()
        if not folder:
            messagebox.showwarning("Carpeta requerida", "Primero selecciona una carpeta de XMLs.")
            return

        self.app.log("Conciliando XMLs en segundo plano...")
        self.summary_label.configure(text="Cruzando datos Sheikah con el inventario...", text_color=CURRENT_THEME["warning"])
        self.progress_bar.grid()
        self.progress_bar.start()

        def _task():
            try:
                output_path, series_actualizadas = mg.validar_xml_y_reemplazar(folder)
                self.app.after(0, self._process_success, output_path, folder, series_actualizadas)
            except Exception as exc:
                self.app.after(0, self._process_error, exc)

        self.app.run_in_thread(_task)

    def _process_success(self, output_path, folder, series_actualizadas):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.app.app_state.record_event("xml", "UUIDs conciliados", {
            "carpeta": folder,
            "inventario": output_path,
            "series_actualizadas": series_actualizadas
        })
        self.app.refresh_data(force=True)
        self.app.history_view.refresh()
        self.refresh()
        self.reset_workspace()
        self.summary_label.configure(text="Sincronización de UUID completada.", text_color=CURRENT_THEME["emerald"])
        self.app.log(f"XMLs conciliados desde {folder}")
        try:
            app_name = self.app.app_state.config.get("logo_text", "MACHOTES OF TIME")
            notification.notify(
                title=app_name,
                message="Validación XML completada y UUIDs cruzados con el inventario.",
                app_name=app_name,
                timeout=5
            )
        except Exception as e:
            self.app.log(f"No se pudo mostrar la notificación nativa: {e}")
        messagebox.showinfo("XML conciliados", f"Inventario actualizado en base de datos.")

    def _process_error(self, exc):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        import traceback
        self.summary_label.configure(text="Error conciliando XMLs.", text_color=CURRENT_THEME["danger"])
        self.app.log(f"Error procesando XML:\n{traceback.format_exc()}")
        messagebox.showerror("Error procesando XMLs", f"No se pudo actualizar el inventario con XMLs.\n\n{exc}")
