import customtkinter as ctk
from tkinter import messagebox
from ui.components import BaseView, CURRENT_THEME

class SettingsView(BaseView):
    title = "Cámara del Sabio"
    subtitle = "Ajustes visuales, nombres por defecto y rutas clave del sistema."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        card = ctk.CTkScrollableFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        self.grid_rowconfigure(1, weight=1)
        self.entries = {}

        fields = [
            ("empresa_default", "Empresa por defecto"),
            ("cuenta_default", "Cuenta por defecto"),
            ("rfc_default", "RFC por defecto"),
            ("logo_text", "Texto principal"),
            ("parse_warning_threshold", "Umbral warnings (importación PDF)"),
            ("inventario_path", "Ruta inventario (Solo Lectura - Obsoleto)"),
            ("machote_path", "Ruta plantilla machote"),
            ("precios_path", "Ruta lista de precios"),
            ("output_dir", "Carpeta de salida machotes"),
        ]
        for idx, (key, label) in enumerate(fields):
            frame = ctk.CTkFrame(card, fg_color="transparent")
            frame.grid(row=idx, column=0, sticky="ew", padx=8, pady=6)
            frame.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(frame, text=label, text_color=CURRENT_THEME["muted"]).grid(row=0, column=0, sticky="w")
            entry = ctk.CTkEntry(frame)
            entry.grid(row=1, column=0, sticky="ew", pady=(4, 0))
            entry.insert(0, str(self.app.app_state.config.get(key, "")))
            if key == "inventario_path":
                entry.configure(state="disabled")
            self.entries[key] = entry

        mode_frame = ctk.CTkFrame(card, fg_color="transparent")
        mode_frame.grid(row=len(fields), column=0, sticky="ew", padx=8, pady=12)
        ctk.CTkLabel(mode_frame, text="Modo visual (Requiere Reinicio)", text_color=CURRENT_THEME["muted"]).pack(anchor="w")
        self.mode_option = ctk.CTkOptionMenu(mode_frame, values=["Dark", "HoneyWhale", "Light", "System"], command=self.change_mode, fg_color=CURRENT_THEME["gold"], button_color=CURRENT_THEME["gold_hover"], text_color="#221A0C")
        self.mode_option.pack(anchor="w", pady=(6, 0))
        self.mode_option.set(self.app.app_state.config.get("theme_mode", "Dark"))

        buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
        buttons_frame.grid(row=len(fields) + 1, column=0, sticky="ew", padx=8, pady=(8, 16))

        ctk.CTkButton(buttons_frame, text="Guardar ajustes", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.save).pack(side="left", padx=(0, 20))

        self.btn_wipe = ctk.CTkButton(buttons_frame, text="Destruir Reino (Resetear BD)", fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], command=self.wipe_database)
        self.btn_wipe.pack(side="right")

    def wipe_database(self):
        confirm1 = messagebox.askyesno(
            "⚠️ ADVERTENCIA CRÍTICA ⚠️",
            "Estás a punto de borrar ABSOLUTAMENTE TODOS los artículos de la base de datos (Disponibles, Usados y XML).\n\n"
            "Esto te dejará con un inventario vacío, como si la app estuviera recién instalada.\n\n"
            "¿Estás seguro de que quieres continuar?"
        )
        if not confirm1:
            return

        confirm2 = messagebox.askyesno(
            "Última Confirmación",
            "Esta acción NO se puede deshacer (a menos que restaures un respaldo manualmente).\n\n¿Destruir el reino y empezar de cero?"
        )
        if not confirm2:
            return

        self.app.log("Iniciando destrucción de la base de datos...")

        try:
            from database import db_manager
            db_manager.create_empty_inventory()

            # Limpiar historial tambien para evitar confusiones
            self.app.app_state.history = []
            self.app.app_state.save_history()

            self.app.refresh_data(force=True)
            self.app.log("El Reino ha renacido. Base de datos reseteada con éxito.")
            messagebox.showinfo("Reinicio Exitoso", "El inventario ha sido borrado por completo.\nPuedes empezar a cargar PDFs desde cero.")

            # Refrescar la vista actual si es necesario (el Dashboard ya se refresca con refresh_data)
        except Exception as e:
            import traceback
            self.app.log(f"Error reseteando BD:\n{traceback.format_exc()}")
            messagebox.showerror("Error", f"No se pudo resetear la base de datos:\n\n{e}")

    def change_mode(self, mode):
        if mode in ["Dark", "Light", "System"]:
            ctk.set_appearance_mode(mode)
        else:
            ctk.set_appearance_mode("Dark")

        self.app.app_state.config["theme_mode"] = mode
        self.app.app_state.save_config()
        messagebox.showinfo("Reinicio Requerido", "Cambiar el modo visual de la aplicación requiere reiniciar para surtir efecto completo.")

    def save(self):
        for key, entry in self.entries.items():
            if key == "inventario_path":
                continue # Do not save disabled fields
            value = entry.get().strip()
            if key == "parse_warning_threshold":
                try:
                    value_int = int(value)
                except ValueError:
                    messagebox.showwarning("Valor inválido", "El umbral de warnings debe ser un número entero.")
                    return
                if value_int < 0:
                    messagebox.showwarning("Valor inválido", "El umbral de warnings no puede ser negativo.")
                    return
                self.app.app_state.config[key] = value_int
            else:
                self.app.app_state.config[key] = value
        self.app.app_state.save_config()
        self.app.apply_runtime_config()
        self.app.log("Ajustes guardados correctamente.")
        messagebox.showinfo("Ajustes guardados", "La configuración del sabio ha sido preservada.")
