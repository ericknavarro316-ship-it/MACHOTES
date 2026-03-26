import json
import customtkinter as ctk
from tkinter import messagebox
from ui.components import BaseView, CURRENT_THEME

class HistoryView(BaseView):
    title = "Crónicas del Héroe"
    subtitle = "Registro histórico de machotes, cargas, conciliaciones y cambios importantes."

    def __init__(self, master, app):
        super().__init__(master, app)
        self.create_header()
        self.grid_rowconfigure(2, weight=1)

        controls = ctk.CTkFrame(self, fg_color="transparent")
        controls.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 12))

        ctk.CTkLabel(controls, text="Filtrar por tipo:", text_color=CURRENT_THEME["muted"]).pack(side="left", padx=(0, 8))
        self.type_filter = ctk.CTkOptionMenu(
            controls,
            values=["Todos"],
            command=self.refresh,
            fg_color=CURRENT_THEME["panel_alt"],
            button_color=CURRENT_THEME["panel_alt"],
            button_hover_color=CURRENT_THEME["panel"]
        )
        self.type_filter.pack(side="left")

        ctk.CTkButton(controls, text="Ver Detalles del Evento", fg_color=CURRENT_THEME["sky"], hover_color="#4F7C7A", command=self.show_details).pack(side="right")

        card = ctk.CTkFrame(self, fg_color=CURRENT_THEME["panel"], corner_radius=18, border_width=1, border_color=CURRENT_THEME["gold"])
        card.grid(row=2, column=0, sticky="nsew", padx=18, pady=(0, 18))
        card.grid_rowconfigure(0, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self.tree = self.app.create_treeview(card, [
            ("fecha", "Fecha", 160),
            ("tipo", "Tipo", 140),
            ("resumen", "Resumen", 420),
        ])
        self.tree.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.tree.bind("<Double-1>", lambda e: self.show_details())

    def refresh(self, *args):
        # Update filter options dynamically
        types = set(entry.get("type", "") for entry in self.app.app_state.history if entry.get("type"))
        current_options = ["Todos"] + sorted(list(types))

        # Keep selected if it still exists
        current_selection = self.type_filter.get()
        self.type_filter.configure(values=current_options)
        if current_selection not in current_options:
            self.type_filter.set("Todos")
        else:
            self.type_filter.set(current_selection)

        selected_type = self.type_filter.get()

        for item in self.tree.get_children():
            self.tree.delete(item)

        for idx, entry in enumerate(self.app.app_state.history):
            e_type = entry.get("type", "")
            if selected_type != "Todos" and e_type != selected_type:
                continue
            self.tree.insert("", "end", iid=str(idx), values=(entry.get("timestamp", ""), e_type, entry.get("summary", "")))

    def show_details(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona un evento de la lista para ver sus detalles.")
            return

        idx = int(selected[0])
        entry = self.app.app_state.history[idx]

        details = entry.get("details", {})

        top = ctk.CTkToplevel(self)
        top.title("Detalles del Evento")
        top.geometry("600x400")
        top.attributes('-topmost', True)
        top.configure(fg_color=CURRENT_THEME["bg"])

        lbl = ctk.CTkLabel(top, text=f"[{entry.get('type', 'Evento')}] {entry.get('timestamp', '')}", font=ctk.CTkFont(size=16, weight="bold"), text_color=CURRENT_THEME["gold"])
        lbl.pack(pady=10, padx=10, anchor="w")

        lbl_sum = ctk.CTkLabel(top, text=entry.get("summary", ""), text_color=CURRENT_THEME["text"], wraplength=550, justify="left")
        lbl_sum.pack(pady=(0, 10), padx=10, anchor="w")

        if details:
            text = ctk.CTkTextbox(top, fg_color=CURRENT_THEME["panel"], text_color=CURRENT_THEME["text"], border_width=1, border_color=CURRENT_THEME["gold"], font=("Consolas", 11))
            text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

            try:
                formatted = json.dumps(details, indent=4, ensure_ascii=False)
                text.insert("0.0", formatted)
            except (TypeError, ValueError):
                text.insert("0.0", str(details))

            text.configure(state="disabled")
        else:
            ctk.CTkLabel(top, text="No hay metadatos adicionales para este evento.", text_color=CURRENT_THEME["muted"]).pack(pady=20)
