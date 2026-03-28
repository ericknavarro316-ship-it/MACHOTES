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
        self.mode_option = ctk.CTkOptionMenu(mode_frame, values=["Dark", "HoneyWhale", "Custom", "Light", "System"], command=self.change_mode, fg_color=CURRENT_THEME["gold"], button_color=CURRENT_THEME["gold_hover"], text_color="#221A0C")
        self.mode_option.pack(anchor="w", pady=(6, 0))
        self.mode_option.set(self.app.app_state.config.get("theme_mode", "Dark"))

        # Custom colors section
        self.custom_colors_frame = ctk.CTkFrame(card, fg_color=CURRENT_THEME["panel_alt"], corner_radius=8)
        self.custom_colors_frame.grid(row=len(fields) + 1, column=0, sticky="ew", padx=8, pady=12)
        self.custom_colors_frame.grid_columnconfigure((0,1), weight=1)

        header_frame_custom = ctk.CTkFrame(self.custom_colors_frame, fg_color="transparent")
        header_frame_custom.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(10, 5))
        header_frame_custom.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header_frame_custom, text="Marca Blanca (Modo 'Custom')", text_color=CURRENT_THEME["gold"], font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, sticky="w", padx=10)

        self.btn_load_logo = ctk.CTkButton(header_frame_custom, text="Subir Logo y Extraer Colores", fg_color=CURRENT_THEME["sky"], hover_color="#4F7C7A", command=self.upload_logo_and_extract_colors)
        self.btn_load_logo.grid(row=0, column=1, sticky="e", padx=(0, 10))

        custom_fields = [
            ("logo_text", "Nombre del Software (Marca Blanca)", "MACHOTES OF TIME"),
            ("custom_color_bg", "Color de Fondo (bg)", "#121212"),
            ("custom_color_panel", "Color Panel (panel)", "#1E1E1E"),
            ("custom_color_gold", "Color Primario (gold)", "#3498DB"),
            ("custom_color_forest", "Color Secundario (forest)", "#2ECC71"),
            ("custom_color_text", "Color de Texto (text)", "#FFFFFF"),
        ]

        self.custom_entries = {}
        for idx, (key, label, default_val) in enumerate(custom_fields):
            row = (idx // 2) + 1
            col = idx % 2
            f = ctk.CTkFrame(self.custom_colors_frame, fg_color="transparent")
            f.grid(row=row, column=col, sticky="ew", padx=10, pady=5)
            f.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(f, text=label, text_color=CURRENT_THEME["muted"], font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
            ce = ctk.CTkEntry(f, height=24)
            ce.grid(row=1, column=0, sticky="ew", pady=(2, 0))
            val = self.app.app_state.config.get(key, default_val)
            ce.insert(0, str(val))
            self.custom_entries[key] = ce

        self._toggle_custom_colors(self.app.app_state.config.get("theme_mode", "Dark"))

        # Auto Backup Configuration
        self.backup_frame = ctk.CTkFrame(card, fg_color=CURRENT_THEME["panel_alt"], corner_radius=8)
        self.backup_frame.grid(row=len(fields) + 2, column=0, sticky="ew", padx=8, pady=12)
        self.backup_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.backup_frame, text="Respaldos Automáticos de la Nube (Auto-Backup)", text_color=CURRENT_THEME["gold"], font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        self.auto_backup_var = ctk.StringVar(value=str(self.app.app_state.config.get("auto_backup_enabled", "False")))
        self.auto_backup_cb = ctk.CTkCheckBox(self.backup_frame, text="Crear respaldo automáticamente al cerrar la aplicación", variable=self.auto_backup_var, onvalue="True", offvalue="False", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"])
        self.auto_backup_cb.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5)

        path_frame = ctk.CTkFrame(self.backup_frame, fg_color="transparent")
        path_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        path_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(path_frame, text="Carpeta de Respaldos (ej. OneDrive, Dropbox, etc):", text_color=CURRENT_THEME["muted"], font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
        self.backup_path_entry = ctk.CTkEntry(path_frame, height=28)
        self.backup_path_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0), padx=(0, 10))
        self.backup_path_entry.insert(0, str(self.app.app_state.config.get("auto_backup_path", "")))

        ctk.CTkButton(path_frame, text="Examinar...", width=80, fg_color=CURRENT_THEME["panel"], hover_color=CURRENT_THEME["gold_hover"], command=self._select_backup_folder).grid(row=1, column=1, sticky="e")

        # Smart Assistant Configuration
        self.assistant_frame = ctk.CTkFrame(card, fg_color=CURRENT_THEME["panel_alt"], corner_radius=8)
        self.assistant_frame.grid(row=len(fields) + 3, column=0, sticky="ew", padx=8, pady=12)
        self.assistant_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self.assistant_frame, text="Asistente Inteligente", text_color=CURRENT_THEME["gold"], font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 5))

        watcher_frame = ctk.CTkFrame(self.assistant_frame, fg_color="transparent")
        watcher_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        watcher_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(watcher_frame, text="Carpeta Monitoreo XML (Auto-Conciliación):", text_color=CURRENT_THEME["muted"], font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
        self.xml_watcher_entry = ctk.CTkEntry(watcher_frame, height=28)
        self.xml_watcher_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0), padx=(0, 10))
        self.xml_watcher_entry.insert(0, str(self.app.app_state.config.get("xml_watcher_path", "")))

        ctk.CTkButton(watcher_frame, text="Examinar...", width=80, fg_color=CURRENT_THEME["panel"], hover_color=CURRENT_THEME["gold_hover"], command=self._select_watcher_folder).grid(row=1, column=1, sticky="e")

        price_col_frame = ctk.CTkFrame(self.assistant_frame, fg_color="transparent")
        price_col_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        price_col_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(price_col_frame, text="Columna de Precio (en Excel de Precios):", text_color=CURRENT_THEME["muted"], font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w")
        self.price_col_entry = ctk.CTkEntry(price_col_frame, height=28, placeholder_text="D1, D2, MAYOREO...")
        self.price_col_entry.grid(row=1, column=0, sticky="ew", pady=(2, 0), padx=(0, 10))
        self.price_col_entry.insert(0, str(self.app.app_state.config.get("price_column", "D1")))

        buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
        buttons_frame.grid(row=len(fields) + 4, column=0, sticky="ew", padx=8, pady=(8, 16))

        ctk.CTkButton(buttons_frame, text="Guardar ajustes", fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], command=self.save).pack(side="left", padx=(0, 20))

        self.btn_wipe = ctk.CTkButton(buttons_frame, text="Destruir Reino (Resetear BD)", fg_color=CURRENT_THEME["danger"], hover_color=CURRENT_THEME["danger_hover"], command=self.wipe_database)
        self.btn_wipe.pack(side="right")

    def _select_backup_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Seleccionar Carpeta para Auto-Respaldo")
        if folder:
            self.backup_path_entry.delete(0, "end")
            self.backup_path_entry.insert(0, folder)

    def _select_watcher_folder(self):
        from tkinter import filedialog
        folder = filedialog.askdirectory(title="Seleccionar Carpeta Monitoreo XML")
        if folder:
            self.xml_watcher_entry.delete(0, "end")
            self.xml_watcher_entry.insert(0, folder)

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

        self._toggle_custom_colors(mode)
        self.app.app_state.config["theme_mode"] = mode
        self.app.app_state.save_config()
        messagebox.showinfo("Reinicio Requerido", "Cambiar el modo visual de la aplicación requiere reiniciar para surtir efecto completo.")

    def upload_logo_and_extract_colors(self):
        from tkinter import filedialog
        import shutil
        from pathlib import Path

        file_path = filedialog.askopenfilename(
            title="Seleccionar Logo de Empresa",
            filetypes=[("Archivos de imagen", "*.png *.jpg *.jpeg *.bmp"), ("Todos", "*.*")]
        )
        if not file_path:
            return

        try:
            # Import and run extractor
            from utils.color_extractor import get_dominant_colors
            colors = get_dominant_colors(file_path, num_colors=2)

            # Save the image to app_data
            from core.config import OUTPUT_DIR
            dest_path = Path(self.app.app_state.config.get("output_dir", OUTPUT_DIR)).parent / "app_data" / "custom_logo.png"
            dest_path.resolve().parent.mkdir(parents=True, exist_ok=True)

            from PIL import Image
            img = Image.open(file_path)
            # Resize image if it's too large to save space (e.g., max 500x500)
            img.thumbnail((500, 500))

            # Check for dark logos with transparency
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGBA')
                # Analyze brightness of non-transparent pixels
                pixels = list(img.getdata())
                dark_pixels = 0
                visible_pixels = 0
                for r, g, b, a in pixels:
                    if a > 50:
                        visible_pixels += 1
                        # Fast brightness calculation
                        brightness = (r * 299 + g * 587 + b * 114) / 1000
                        if brightness < 80:
                            dark_pixels += 1

                # If image is mostly transparent and very dark, add a white background
                if visible_pixels > 0 and (dark_pixels / visible_pixels) > 0.6:
                    bg = Image.new('RGBA', img.size, (255, 255, 255, 255))
                    bg.paste(img, (0, 0), img)
                    img = bg
            elif img.mode != 'RGBA':
                img = img.convert('RGBA')

            img.save(dest_path, "PNG")

            if colors:
                primary, secondary = colors

                # Fill the entries
                self.custom_entries["custom_color_gold"].delete(0, "end")
                self.custom_entries["custom_color_gold"].insert(0, primary)

                self.custom_entries["custom_color_forest"].delete(0, "end")
                self.custom_entries["custom_color_forest"].insert(0, secondary)

                # Auto set mode to Custom
                self.mode_option.set("Custom")
                self._toggle_custom_colors("Custom")

                messagebox.showinfo("Logo Cargado", f"Logo guardado exitosamente.\n\nColores detectados:\nPrimario: {primary}\nSecundario: {secondary}\n\nPresiona 'Guardar ajustes' para aplicar.")
            else:
                messagebox.showinfo("Logo Cargado", "Logo guardado, pero no se pudieron detectar colores dominantes claros.\nPuedes configurarlos manualmente.")

        except Exception as e:
            import traceback
            self.app.log(f"Error procesando logo:\n{traceback.format_exc()}")
            messagebox.showerror("Error", f"No se pudo procesar la imagen:\n{e}")

    def _toggle_custom_colors(self, mode):
        if hasattr(self, 'custom_colors_frame'):
            if mode == "Custom":
                for entry in self.custom_entries.values():
                    entry.configure(state="normal")
                if hasattr(self, 'btn_load_logo'):
                    self.btn_load_logo.configure(state="normal")
            else:
                for entry in self.custom_entries.values():
                    entry.configure(state="disabled")
                if hasattr(self, 'btn_load_logo'):
                    self.btn_load_logo.configure(state="disabled")

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

        # Save custom colors
        for key, entry in self.custom_entries.items():
            value = entry.get().strip()
            self.app.app_state.config[key] = value

        # Save backup settings
        self.app.app_state.config["auto_backup_enabled"] = self.auto_backup_var.get()
        self.app.app_state.config["auto_backup_path"] = self.backup_path_entry.get().strip()

        # Save smart assistant settings
        self.app.app_state.config["xml_watcher_path"] = self.xml_watcher_entry.get().strip()
        self.app.app_state.config["price_column"] = self.price_col_entry.get().strip() or "D1"

        self.app.app_state.save_config()
        self.app.apply_runtime_config()
        self.app.log("Ajustes guardados correctamente.")
        messagebox.showinfo("Ajustes guardados", "La configuración del sabio ha sido preservada.")
