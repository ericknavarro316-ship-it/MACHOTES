import threading
import database
import notifications
from gui import AgendaAppGUI
import customtkinter as ctk

def main():
    # Initialize database
    database.init_db()

    # Start notifications background thread
    notify_thread = threading.Thread(target=notifications.check_notifications, daemon=True)
    notify_thread.start()

    # Set CustomTkinter appearance
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")

    # Launch GUI
    app = AgendaAppGUI()
    app.mainloop()

if __name__ == "__main__":
    main()
