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

        ctk.CTkButton(card, text="Guardar ajustes", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.save).grid(row=len(fields) + 1, column=0, sticky="w", padx=8, pady=(8, 16))

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
