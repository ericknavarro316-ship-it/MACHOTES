import customtkinter as ctk
from tkinter import messagebox
import machote_generator as mg
from ui.components import BaseView, CURRENT_THEME

class MachoteHistoryView(BaseView):
    title = "Registro de Machotes"
    subtitle = "Administra los machotes generados, revierte asignaciones y localiza archivos."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(1, weight=1)

        main_split = ctk.CTkFrame(self, fg_color="transparent")
        main_split.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        main_split.grid_rowconfigure(0, weight=1)
        main_split.grid_columnconfigure(0, weight=1) # List panel
        main_split.grid_columnconfigure(1, weight=2) # Details panel

        # --- LEFT PANEL (List) ---
        list_card = ctk.CTkFrame(main_split, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        list_card.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        list_card.grid_rowconfigure(1, weight=1)
        list_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(list_card, text="Historial de Creación", font=ctk.CTkFont(size=16, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 6))

        self.tree = self.app.create_treeview(list_card, [
            ("fecha", "Fecha", 140),
            ("archivo", "Archivo", 250),
        ])
        self.tree.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 12))
        self.tree.bind("<<TreeviewSelect>>", self.on_machote_selected)

        # --- RIGHT PANEL (Details) ---
        details_card = ctk.CTkFrame(main_split, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        details_card.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        details_card.grid_rowconfigure(2, weight=1)
        details_card.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(details_card, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 10))
        header_frame.grid_columnconfigure(0, weight=1)

        self.lbl_title = ctk.CTkLabel(header_frame, text="Selecciona un machote", font=ctk.CTkFont(size=18, weight="bold"), text_color=CURRENT_THEME["gold"])
        self.lbl_title.grid(row=0, column=0, sticky="w")

        self.btn_open = ctk.CTkButton(header_frame, text="Abrir Archivo", fg_color=CURRENT_THEME["sky"], hover_color="#4F7C7A", state="disabled", command=self.open_machote_file)
        self.btn_open.grid(row=0, column=1, sticky="e", padx=(0, 10))
        self.btn_undo = ctk.CTkButton(header_frame, text="Deshacer Machote", fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], state="disabled", command=self.undo_machote)
        self.btn_undo.grid(row=0, column=2, sticky="e")

        self.summary_frame = ctk.CTkFrame(details_card, fg_color=CURRENT_THEME["panel_alt"], corner_radius=12)
        self.summary_frame.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 14))
        self.summary_frame.grid_columnconfigure((0,1,2,3), weight=1)

        self.lbl_date = ctk.CTkLabel(self.summary_frame, text="Fecha: --", font=ctk.CTkFont(size=13))
        self.lbl_date.grid(row=0, column=0, pady=8, padx=10, sticky="w")
        self.lbl_company = ctk.CTkLabel(self.summary_frame, text="Empresa: --", font=ctk.CTkFont(size=13, weight="bold"), text_color=CURRENT_THEME["emerald"])
        self.lbl_company.grid(row=0, column=1, pady=8, padx=10, sticky="w")
        self.lbl_rfc = ctk.CTkLabel(self.summary_frame, text="RFC: --", font=ctk.CTkFont(size=13))
        self.lbl_rfc.grid(row=0, column=2, pady=8, padx=10, sticky="w")
        self.lbl_pieces = ctk.CTkLabel(self.summary_frame, text="Piezas: 0", font=ctk.CTkFont(size=14, weight="bold"), text_color=CURRENT_THEME["text"])
        self.lbl_pieces.grid(row=0, column=3, pady=8, padx=10, sticky="e")

        self.details_tree = self.app.create_treeview(details_card, [
            ("sucursal", "Sucursal", 110),
            ("modelo", "Modelo", 160),
            ("serie", "Serie", 180),
            ("total", "Total", 120),
        ])
        self.details_tree.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 12))

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        machotes = [m for m in self.app.app_state.history if m.get("type") in ("machote", "machote_externo")]

        for idx, entry in enumerate(machotes):
            details = entry.get("details", {})

            if entry.get("type") == "machote":
                archivo = details.get("archivo", "")
            elif entry.get("type") == "machote_externo":
                archivo = details.get("archivo", "")

            import os
            self.tree.insert("", "end", iid=str(idx), values=(entry.get("timestamp", ""), os.path.basename(archivo)))

        # Reset right panel
        self.btn_open.configure(state="disabled")
        self.btn_undo.configure(state="disabled")
        self.lbl_title.configure(text="Selecciona un machote")
        self.lbl_date.configure(text="Fecha: --")
        self.lbl_company.configure(text="Empresa: --")
        self.lbl_rfc.configure(text="RFC: --")
        self.lbl_pieces.configure(text="Piezas: 0")
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)

    def on_machote_selected(self, event):
        selected = self.tree.selection()
        if not selected:
            return

        idx = int(selected[0])
        machotes = [m for m in self.app.app_state.history if m.get("type") in ("machote", "machote_externo")]
        entry = machotes[idx]
        details = entry.get("details", {})

        import os
        filename = os.path.basename(details.get("archivo", "Desconocido"))

        self.lbl_title.configure(text=filename)
        self.lbl_date.configure(text=f"Fecha: {entry.get('timestamp', '--').split(' ')[0]}")

        if entry.get("type") == "machote":
            self.lbl_company.configure(text=f"Empresa: {details.get('empresa', '--')[:20]}")
            self.lbl_rfc.configure(text=f"RFC: {details.get('rfc', '--')}")
            self.lbl_pieces.configure(text=f"Piezas: {details.get('piezas', 0)}")
            db_machote_name = filename
        else:
            self.lbl_company.configure(text="Empresa: (Externa)")
            self.lbl_rfc.configure(text="RFC: --")
            self.lbl_pieces.configure(text=f"Piezas: {details.get('series_coincidentes', 0)}")
            db_machote_name = f"EXT: {filename}"

        self.btn_open.configure(state="normal")
        self.btn_undo.configure(state="normal")

        # Populate mini inventory from database cache
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)

        inventory = self.app.get_inventory_data(refresh=False)
        if inventory and inventory.get("usados") is not None:
            df_usados = inventory.get("usados")
            if "MACHOTE" in df_usados.columns:
                machote_items = df_usados[df_usados["MACHOTE"].astype(str) == db_machote_name]
                for _, row in machote_items.iterrows():
                    self.details_tree.insert("", "end", values=(
                        str(row.get("SUCURSAL", "")),
                        str(row.get("MODELO BASE", "")),
                        str(row.get("No de SERIE:", "")),
                        self.app.money(row.get("TOTAL", 0))
                    ))


    def get_selected_machote(self):
        selected = self.tree.selection()
        if not selected:
            return None
        idx = int(selected[0])
        machotes = [m for m in self.app.app_state.history if m.get("type") in ("machote", "machote_externo")]
        return machotes[idx].get("details", {}).get("archivo", "")

    def undo_machote(self):
        archivo = self.get_selected_machote()
        if not archivo:
            messagebox.showwarning("Aviso", "Selecciona un machote de la lista para deshacer.")
            return

        import os
        filename = os.path.basename(archivo)

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
            elif platform.system() == 'Darwin':
                subprocess.call(('open', archivo))
            else:
                subprocess.call(('xdg-open', archivo))
            self.app.log(f"Archivo abierto: {archivo}")
        except Exception as exc:
            self.app.log(f"Error abriendo archivo {archivo}: {exc}")
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{exc}")
