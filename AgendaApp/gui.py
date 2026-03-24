import customtkinter as ctk
from tkinter import ttk
import tkinter as tk
import datetime
import database

class AgendaAppGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Agenda y Calendario")
        self.geometry("900x600")

        # Configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Panel - Input Form
        self.frame_left = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.frame_left.grid(row=0, column=0, sticky="nswe")
        self.frame_left.grid_rowconfigure(8, weight=1)

        self.label_title = ctk.CTkLabel(self.frame_left, text="Nueva Tarea", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_title.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Task Name
        self.entry_name = ctk.CTkEntry(self.frame_left, placeholder_text="Nombre de la actividad")
        self.entry_name.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        # Priority
        self.label_priority = ctk.CTkLabel(self.frame_left, text="Prioridad:")
        self.label_priority.grid(row=2, column=0, padx=20, pady=(10, 0), sticky="w")
        self.option_priority = ctk.CTkOptionMenu(self.frame_left, values=["Alta", "Media", "Baja"])
        self.option_priority.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Start Date and Time
        self.label_datetime = ctk.CTkLabel(self.frame_left, text="Fecha y Hora (YYYY-MM-DD HH:MM):")
        self.label_datetime.grid(row=4, column=0, padx=20, pady=(10, 0), sticky="w")
        self.entry_datetime = ctk.CTkEntry(self.frame_left, placeholder_text="Ej: 2023-12-31 15:30")
        self.entry_datetime.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Repeatability
        self.label_repeat = ctk.CTkLabel(self.frame_left, text="Repetitividad (Días, 0=No):")
        self.label_repeat.grid(row=6, column=0, padx=20, pady=(10, 0), sticky="w")
        self.entry_repeat = ctk.CTkEntry(self.frame_left, placeholder_text="0")
        self.entry_repeat.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Add Button
        self.button_add = ctk.CTkButton(self.frame_left, text="Agregar Tarea", command=self.add_task)
        self.button_add.grid(row=8, column=0, padx=20, pady=20, sticky="s")

        # Right Panel - Agenda View
        self.frame_right = ctk.CTkFrame(self)
        self.frame_right.grid(row=0, column=1, padx=20, pady=20, sticky="nswe")
        self.frame_right.grid_columnconfigure(0, weight=1)
        self.frame_right.grid_rowconfigure(1, weight=1)

        self.label_agenda = ctk.CTkLabel(self.frame_right, text="Agenda de Tareas", font=ctk.CTkFont(size=20, weight="bold"))
        self.label_agenda.grid(row=0, column=0, padx=20, pady=(10, 10))

        # Treeview for tasks
        columns = ("id", "name", "priority", "start_datetime", "repeat_days", "status")
        self.tree = ttk.Treeview(self.frame_right, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("id", text="ID")
        self.tree.column("id", width=30, anchor="center")
        self.tree.heading("name", text="Actividad")
        self.tree.column("name", width=150)
        self.tree.heading("priority", text="Prioridad")
        self.tree.column("priority", width=80, anchor="center")
        self.tree.heading("start_datetime", text="Fecha/Hora")
        self.tree.column("start_datetime", width=120, anchor="center")
        self.tree.heading("repeat_days", text="Repite (Días)")
        self.tree.column("repeat_days", width=80, anchor="center")
        self.tree.heading("status", text="Estado")
        self.tree.column("status", width=80, anchor="center")

        # Configure style and tags
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0)
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#565b5e", foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[('active', '#343638')])

        self.tree.tag_configure('alta', background='#ff4d4d', foreground='white')

        self.tree.grid(row=1, column=0, sticky="nswe", padx=10, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.frame_right, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns")

        # Action Buttons
        self.frame_actions = ctk.CTkFrame(self.frame_right, fg_color="transparent")
        self.frame_actions.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        self.button_complete = ctk.CTkButton(self.frame_actions, text="Marcar Completada", command=self.complete_selected_task)
        self.button_complete.pack(side="left", padx=(0, 10))

        self.button_delete = ctk.CTkButton(self.frame_actions, text="Eliminar Tarea", fg_color="#d32f2f", hover_color="#b71c1c", command=self.delete_selected_task)
        self.button_delete.pack(side="left")

        # Load initial data
        self.load_tasks()

    def add_task(self):
        name = self.entry_name.get().strip()
        priority = self.option_priority.get()
        start_datetime_str = self.entry_datetime.get().strip()
        repeat_days_str = self.entry_repeat.get().strip()

        if not name or not start_datetime_str:
            self.show_error("Nombre y Fecha/Hora son obligatorios.")
            return

        try:
            # Validate datetime format
            datetime.datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
        except ValueError:
            self.show_error("Formato de fecha/hora inválido. Use YYYY-MM-DD HH:MM")
            return

        try:
            repeat_days = int(repeat_days_str) if repeat_days_str else 0
        except ValueError:
            self.show_error("Repetitividad debe ser un número entero.")
            return

        database.add_task(name, priority, start_datetime_str, repeat_days)

        # Clear inputs
        self.entry_name.delete(0, 'end')
        self.entry_datetime.delete(0, 'end')
        self.entry_repeat.delete(0, 'end')
        self.entry_repeat.insert(0, "0")

        self.load_tasks()

    def load_tasks(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        tasks = database.get_tasks()
        for task in tasks:
            task_id, name, priority, start_datetime, repeat_days, completed, last_notified = task
            status = "Completada" if completed else "Pendiente"

            tags = ()
            if priority == "Alta" and not completed:
                tags = ('alta',)

            self.tree.insert("", "end", values=(task_id, name, priority, start_datetime, repeat_days, status), tags=tags)

    def complete_selected_task(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item = self.tree.item(selected_item[0])
        task_id = item['values'][0]
        database.complete_task(task_id)
        self.load_tasks()

    def delete_selected_task(self):
        selected_item = self.tree.selection()
        if not selected_item:
            return

        item = self.tree.item(selected_item[0])
        task_id = item['values'][0]
        database.delete_task(task_id)
        self.load_tasks()

    def show_error(self, message):
        # A simple way to show errors, could be replaced with a proper dialog
        error_dialog = ctk.CTkToplevel(self)
        error_dialog.title("Error")
        error_dialog.geometry("300x150")
        error_dialog.transient(self)

        label = ctk.CTkLabel(error_dialog, text=message, wraplength=250)
        label.pack(pady=20, padx=20)

        button = ctk.CTkButton(error_dialog, text="OK", command=error_dialog.destroy)
        button.pack(pady=10)
