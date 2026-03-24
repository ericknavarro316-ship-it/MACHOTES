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

        machotes = [m for m in self.app.app_state.history if m.get("type") in ("machote", "machote_externo")]

        for entry in machotes:
            details = entry.get("details", {})

            if entry.get("type") == "machote":
                archivo = details.get("archivo", "")
                piezas = str(details.get("piezas", ""))
            elif entry.get("type") == "machote_externo":
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
