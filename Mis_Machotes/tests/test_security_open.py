import sys
from unittest.mock import MagicMock, patch

# Mock dependencies before importing MachoteHistoryView
mock_ctk = MagicMock()
sys.modules['customtkinter'] = mock_ctk
sys.modules['tkinter'] = MagicMock()
sys.modules['tkinter.messagebox'] = MagicMock()
sys.modules['tkinter.filedialog'] = MagicMock()
sys.modules['machote_generator'] = MagicMock()

# Mock ui.components and specifically BaseView
mock_ui_components = MagicMock()
sys.modules['ui.components'] = mock_ui_components

import unittest
import os
import platform
import subprocess

# We need to define a dummy BaseView and CURRENT_THEME
class DummyBaseView:
    def __init__(self, master, app):
        self.master = master
        self.app = app
    def grid_rowconfigure(self, *args, **kwargs): pass
    def grid_columnconfigure(self, *args, **kwargs): pass
    def grid(self, *args, **kwargs): pass
    def create_header(self): pass

mock_ui_components.BaseView = DummyBaseView
mock_ui_components.CURRENT_THEME = {
    "panel": "white",
    "gold": "gold",
    "forest": "green",
    "forest_hover": "darkgreen",
    "sky": "blue",
    "danger": "red",
    "danger_hover": "darkred",
    "panel_alt": "gray",
    "emerald": "green",
    "text": "black"
}

# Now we can safely import MachoteHistoryView
from ui.views.machote_hist_view import MachoteHistoryView

class TestSecurityOpen(unittest.TestCase):
    def setUp(self):
        self.app = MagicMock()
        self.master = MagicMock()
        self.app.app_state.history = []

        # Patching CTK components used in __init__
        with patch('customtkinter.CTkFrame', return_value=MagicMock()):
            with patch('customtkinter.CTkLabel', return_value=MagicMock()):
                with patch('customtkinter.CTkButton', return_value=MagicMock()):
                    with patch('customtkinter.CTkFont', return_value=MagicMock()):
                        # We also need to mock create_treeview which is called on self.app
                        self.app.create_treeview.return_value = MagicMock()
                        self.view = MachoteHistoryView(self.master, self.app)

                        # Manually ensure some attributes are mocked as needed
                        self.view.tree = MagicMock()
                        self.view.details_tree = MagicMock()

    @patch('os.path.exists', return_value=True)
    @patch('os.path.abspath')
    @patch('platform.system')
    @patch('subprocess.run')
    @patch('os.startfile', create=True)
    def test_open_machote_file_sanitization(self, mock_startfile, mock_run, mock_system, mock_abspath, mock_exists):
        # Vulnerable-like path: starts with a hyphen
        malicious_path = "-hyphenated_file.xlsx"
        absolute_path = os.path.abspath(malicious_path)
        mock_abspath.return_value = absolute_path

        self.view.get_selected_machote = MagicMock(return_value=malicious_path)

        # Test Windows
        mock_system.return_value = 'Windows'
        self.view.open_machote_file()
        mock_startfile.assert_called_with(absolute_path)

        # Test Darwin (macOS)
        mock_system.return_value = 'Darwin'
        self.view.open_machote_file()
        mock_run.assert_called_with(['open', '--', absolute_path], check=True)

        # Test Linux (xdg-open)
        mock_system.return_value = 'Linux'
        self.view.open_machote_file()
        mock_run.assert_called_with(['xdg-open', absolute_path], check=True)

    @patch('os.path.abspath')
    @patch('platform.system')
    @patch('subprocess.run')
    @patch('os.startfile', create=True)
    @patch('tkinter.messagebox.askyesno', return_value=True)
    def test_pdf_success_sanitization(self, mock_askyesno, mock_startfile, mock_run, mock_system, mock_abspath):
        # Vulnerable-like path
        malicious_path = "-hyphenated_report.pdf"
        absolute_path = os.path.abspath(malicious_path)
        mock_abspath.return_value = absolute_path

        # Test Darwin (macOS)
        mock_system.return_value = 'Darwin'
        self.view._pdf_success(malicious_path)
        mock_run.assert_called_with(['open', '--', absolute_path], check=True)

        # Test Linux
        mock_system.return_value = 'Linux'
        self.view._pdf_success(malicious_path)
        mock_run.assert_called_with(['xdg-open', absolute_path], check=True)

if __name__ == '__main__':
    unittest.main()
