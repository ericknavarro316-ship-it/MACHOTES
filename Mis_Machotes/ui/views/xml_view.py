import customtkinter as ctk
from tkinter import filedialog, messagebox
import machote_generator as mg
from ui.components import BaseView, CURRENT_THEME

class XMLView(BaseView):
    title = "Templo de UUID"
    subtitle = "Cruza XMLs, encuentra coincidencias y mueve piezas facturadas a su santuario correcto."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.selected_dir = ctk.StringVar(value="")
        self.create_header()

        card = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(2, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(card, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))
        ctk.CTkButton(top, text="Elegir carpeta XML", fg_color=CURRENT_THEME["gold"], hover_color=CURRENT_THEME["gold_hover"], text_color="#221A0C", command=self.select_dir).pack(side="left")
        ctk.CTkButton(top, text="Validar y actualizar", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.process_xml).pack(side="left", padx=10)
        ctk.CTkLabel(top, textvariable=self.selected_dir, text_color=CURRENT_THEME["text"]).pack(side="left", padx=8)

        self.summary_label = ctk.CTkLabel(card, text="Aún no se ha inspeccionado ninguna carpeta.", text_color=CURRENT_THEME["muted"])
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

        self.app.log("Conciliando XMLs en segundo plano...")
        self.summary_label.configure(text="Cruzando datos Sheikah con el inventario...", text_color=CURRENT_THEME["warning"])

        def _task():
            try:
                output_path = mg.validar_xml_y_reemplazar(folder)
                self.app.after(0, self._process_success, output_path, folder)
            except Exception as exc:
                self.app.after(0, self._process_error, exc)

        self.app.run_in_thread(_task)

    def _process_success(self, output_path, folder):
        self.app.app_state.record_event("xml", "UUIDs conciliados", {"carpeta": folder, "inventario": output_path})
        self.app.refresh_data(force=True)
        self.app.history_view.refresh()
        self.summary_label.configure(text="Sincronización de UUID completada.", text_color=CURRENT_THEME["emerald"])
        self.app.log(f"XMLs conciliados desde {folder}")
        messagebox.showinfo("XML conciliados", f"Inventario actualizado en base de datos.")

    def _process_error(self, exc):
        import traceback
        self.summary_label.configure(text="Error conciliando XMLs.", text_color=CURRENT_THEME["danger"])
        self.app.log(f"Error procesando XML:\n{traceback.format_exc()}")
        messagebox.showerror("Error procesando XMLs", f"No se pudo actualizar el inventario con XMLs.\n\n{exc}")
