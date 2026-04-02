#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def create_desktop_shortcut():
    base_dir = Path(__file__).resolve().parent
    start_app_path = base_dir / "start_app.py"

    if os.name == "nt":
        # Windows - use VBScript's SpecialFolders to get the true Desktop path
        vbs_script = base_dir / "create_shortcut.vbs"

        vbs_content = f"""
Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.SpecialFolders("Desktop") & "\Machotes Of Time.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = "{sys.executable}"
oLink.Arguments = "{start_app_path}"
oLink.WorkingDirectory = "{base_dir}"
oLink.Description = "Machotes Of Time - Panel de Administración"
oLink.IconLocation = "{base_dir}\\triforce.ico"
oLink.Save
WScript.Echo sLinkFile
"""
        try:
            vbs_script.write_text(vbs_content, encoding="utf-8")
            print("Ejecutando script de acceso directo...")
            subprocess.run(["cscript", "//nologo", str(vbs_script)], check=True)
            vbs_script.unlink()
            print(f"Acceso directo creado exitosamente en tu Escritorio de Windows.")
        except Exception as e:
            print(f"Error creando acceso directo en Windows: {e}")

    else:
        # Linux / Mac - Attempt standard desktop paths
        desktop_dir = Path.home() / "Desktop"
        if not desktop_dir.exists():
            desktop_dir = Path.home() / "Escritorio"

        if not desktop_dir.exists():
            print("No se pudo encontrar la carpeta del Escritorio.")
            return

        shortcut_path = desktop_dir / "Machotes_Of_Time.desktop"

        content = f"""[Desktop Entry]
Version=1.0
Name=Machotes Of Time
Comment=Panel de Administración
Exec={sys.executable} "{start_app_path}"
Path={base_dir}
Icon={base_dir / "triforce.png"}
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