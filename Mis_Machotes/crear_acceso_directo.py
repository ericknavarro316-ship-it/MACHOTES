#!/usr/bin/env python3
import os
import sys
from pathlib import Path

def create_desktop_shortcut():
    base_dir = Path(__file__).resolve().parent
    start_app_path = base_dir / "start_app.py"

    desktop_dir = Path.home() / "Desktop"
    if not desktop_dir.exists():
        desktop_dir = Path.home() / "Escritorio"

    if not desktop_dir.exists():
        print("No se pudo encontrar la carpeta del Escritorio.")
        return

    if os.name == "nt":
        # Windows
        vbs_script = base_dir / "create_shortcut.vbs"
        shortcut_path = desktop_dir / "Machotes Of Time.lnk"

        vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = "{shortcut_path}"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{sys.executable}"
oLink.Arguments = "{start_app_path}"
oLink.WorkingDirectory = "{base_dir}"
oLink.Description = "Zelda-themed Admin Panel for Inventory and Machotes"
oLink.Save
"""
        try:
            vbs_script.write_text(vbs_content, encoding="utf-8")
            os.system(f'cscript //nologo "{vbs_script}"')
            vbs_script.unlink()
            print(f"Acceso directo creado en: {shortcut_path}")
        except Exception as e:
            print(f"Error creando acceso directo en Windows: {e}")

    else:
        # Linux / Mac
        shortcut_path = desktop_dir / "Machotes_Of_Time.desktop"

        content = f"""[Desktop Entry]
Version=1.0
Name=Machotes Of Time
Comment=Zelda-themed Admin Panel for Inventory and Machotes
Exec={sys.executable} "{start_app_path}"
Path={base_dir}
Icon=utilities-terminal
Terminal=false
Type=Application
Categories=Utility;
"""

        try:
            shortcut_path.write_text(content, encoding="utf-8")
            shortcut_path.chmod(0o755) # Make it executable
            print(f"Acceso directo creado en: {shortcut_path}")
        except Exception as e:
            print(f"Error creando acceso directo en Linux/Mac: {e}")

if __name__ == "__main__":
    create_desktop_shortcut()