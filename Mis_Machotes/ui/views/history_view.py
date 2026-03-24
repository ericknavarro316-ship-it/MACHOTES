import customtkinter as ctk
from ui.components import BaseView, CURRENT_THEME

class HistoryView(BaseView):
    title = "Crónicas del Héroe"
    subtitle = "Registro histórico de machotes, cargas, conciliaciones y cambios importantes."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(1, weight=1)
        card = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.tree = self.app.create_treeview(card, [
            ("fecha", "Fecha", 160),
            ("tipo", "Tipo", 100),
            ("resumen", "Resumen", 420),
        ])
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for entry in self.app.app_state.history:
            self.tree.insert("", "end", values=(entry.get("timestamp", ""), entry.get("type", ""), entry.get("summary", "")))
