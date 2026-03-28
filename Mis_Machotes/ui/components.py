import customtkinter as ctk

OOT_THEME = {
    "bg": "#0F1A12",
    "panel": "#17271B",
    "panel_alt": "#203423",
    "gold": "#D7B56D",
    "gold_hover": "#C59C43",
    "forest": "#3E6B45",
    "forest_hover": "#50895A",
    "emerald": "#4FAF6D",
    "text": "#F3ECD2",
    "muted": "#A8A088",
    "danger": "#A64B3C",
    "danger_hover": "#8B3C31",
    "warning": "#B88A3B",
    "sky": "#6AA7A5",
}

HW_THEME = {
    "bg": "#121212",
    "panel": "#1E1E1E",
    "panel_alt": "#2C2C2C",
    "gold": "#FF3B30",
    "gold_hover": "#D32F2F",
    "forest": "#424242",
    "forest_hover": "#616161",
    "emerald": "#4CAF50",
    "text": "#FFFFFF",
    "muted": "#B0BEC5",
    "danger": "#F44336",
    "danger_hover": "#D32F2F",
    "warning": "#FF9800",
    "sky": "#2196F3",
}

CURRENT_THEME = OOT_THEME.copy()

def update_theme_colors(theme_name, custom_colors=None):
    global CURRENT_THEME
    if theme_name == "HoneyWhale":
        CURRENT_THEME.update(HW_THEME)
    elif theme_name == "Custom" and custom_colors:
        CURRENT_THEME.update(custom_colors)
    else:
        CURRENT_THEME.update(OOT_THEME)

def format_color_for_display(color_value):
    color = str(color_value or "").strip().upper()
    if not color:
        return ""
    return " / ".join(part.strip() for part in color.replace("-", "/").split("/") if part.strip())

class MultiSelectMenu(ctk.CTkButton):
    def __init__(self, master, title="Seleccionar", values=None, command=None, **kwargs):
        super().__init__(master, text=title, **kwargs)
        self.values = values or []
        self.command = command
        self.variables = {}
        self.dropdown = None
        self._title = title
        self.configure(command=self.toggle_dropdown)
        self.set_values(self.values)

    def set_values(self, values):
        old_vars = self.variables
        self.values = values
        self.variables = {}
        for val in values:
            if val in old_vars:
                self.variables[val] = old_vars[val]
            else:
                self.variables[val] = ctk.IntVar(value=1)
        self.update_text()

    def get(self):
        return [val for val, var in self.variables.items() if var.get() == 1]

    def update_text(self):
        selected = len(self.get())
        total = len(self.values)
        if selected == total:
            self.configure(text=f"{self._title} (Todos)")
        elif selected == 0:
            self.configure(text=f"{self._title} (Ninguno)")
        else:
            self.configure(text=f"{self._title} ({selected})")

    def toggle_dropdown(self):
        if self.dropdown is not None and self.dropdown.winfo_exists():
            self.dropdown.destroy()
            self.dropdown = None
            self.update_text()
            if self.command:
                self.command()
        else:
            self.dropdown = ctk.CTkToplevel(self)
            self.dropdown.overrideredirect(True)
            self.dropdown.attributes('-topmost', True)
            x = self.winfo_rootx()
            y = self.winfo_rooty() + self.winfo_height()
            self.dropdown.geometry(f"+{int(x)}+{int(y)}")

            main_frame = ctk.CTkFrame(self.dropdown, fg_color=CURRENT_THEME["panel"], border_color=CURRENT_THEME["gold"], border_width=1)
            main_frame.pack(fill="both", expand=True)

            self.search_var = ctk.StringVar()
            self.search_var.trace("w", self._filter_options)
            search_entry = ctk.CTkEntry(main_frame, textvariable=self.search_var, placeholder_text="Buscar...", height=28)
            search_entry.pack(fill="x", padx=10, pady=(10, 5))

            self.options_frame = ctk.CTkScrollableFrame(main_frame, fg_color="transparent", width=200, height=200)
            self.options_frame.pack(fill="both", expand=True)

            btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            btn_frame.pack(fill="x", pady=5, padx=5)
            def select_all():
                for cb, val in self.checkboxes:
                    if cb.winfo_ismapped():
                        self.variables[val].set(1)
            def deselect_all():
                for cb, val in self.checkboxes:
                    if cb.winfo_ismapped():
                        self.variables[val].set(0)
            def select_visible_only():
                for cb, val in self.checkboxes:
                    self.variables[val].set(1 if cb.winfo_ismapped() else 0)
            def close_dropdown():
                self.toggle_dropdown()

            ctk.CTkButton(btn_frame, text="Todo", width=50, height=24, command=select_all, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["forest_hover"]).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Nada", width=50, height=24, command=deselect_all, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["danger_hover"]).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Solo visibles", width=90, height=24, command=select_visible_only, fg_color=CURRENT_THEME["panel_alt"], hover_color=CURRENT_THEME["gold_hover"]).pack(side="left", padx=2)
            ctk.CTkButton(btn_frame, text="Cerrar", width=50, height=24, command=close_dropdown, fg_color=CURRENT_THEME["gold"], text_color="#0D0D12", hover_color=CURRENT_THEME["gold_hover"]).pack(side="right", padx=2)

            self.checkboxes = []
            for val in self.values:
                cb = ctk.CTkCheckBox(self.options_frame, text=val, variable=self.variables[val], onvalue=1, offvalue=0, fg_color=CURRENT_THEME["forest"], hover_color=CURRENT_THEME["forest_hover"], text_color=CURRENT_THEME["text"])
                cb.pack(anchor="w", padx=10, pady=5)
                self.checkboxes.append((cb, val))

    def _filter_options(self, *args):
        query = self.search_var.get().lower()
        for cb, val in self.checkboxes:
            if query in val.lower():
                if not cb.winfo_ismapped():
                    cb.pack(anchor="w", padx=10, pady=5)
            else:
                if cb.winfo_ismapped():
                    cb.pack_forget()

class TreeBundle:
    def __init__(self, frame, tree):
        self._frame = frame
        self._tree = tree

    def __getattr__(self, name):
        return getattr(self._tree, name)

    def grid(self, *args, **kwargs):
        return self._frame.grid(*args, **kwargs)

    def pack(self, *args, **kwargs):
        return self._frame.pack(*args, **kwargs)

    def place(self, *args, **kwargs):
        return self._frame.place(*args, **kwargs)

class BaseView(ctk.CTkFrame):
    title = ""
    subtitle = ""

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_columnconfigure(0, weight=1)

    def create_header(self):
        header = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 12))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=self.title, font=ctk.CTkFont(size=28, weight="bold"), text_color=CURRENT_THEME["gold"]).grid(row=0, column=0, sticky="w", padx=18, pady=(14, 2))
        ctk.CTkLabel(header, text=self.subtitle, font=ctk.CTkFont(size=13), text_color=CURRENT_THEME["text"]).grid(row=1, column=0, sticky="w", padx=18, pady=(0, 14))
        return header
