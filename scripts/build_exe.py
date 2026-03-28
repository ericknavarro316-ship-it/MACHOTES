import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("==================================================")
    print("   CONSTRUCTOR DE EJECUTABLE (MACHOTES OF TIME)   ")
    print("==================================================")
    print("Este script empaquetará toda la aplicación en un solo archivo .exe")
    print("Asegúrate de ejecutar esto desde una computadora con Windows.")
    print("Instalando PyInstaller si no lo tienes...\n")

    # Install pyinstaller
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Base directories
    project_dir = Path(__file__).resolve().parent.parent / "Mis_Machotes"
    if not project_dir.exists() or not (project_dir / "start_app.py").exists():
        print(f"Error: No se pudo encontrar el directorio del proyecto en {project_dir}")
        sys.exit(1)

    # Windows MAX_PATH limit check
    if len(str(project_dir)) > 100:
        print("\n==================================================")
        print("                 ⚠️ ADVERTENCIA ⚠️                  ")
        print("==================================================")
        print("La ruta actual donde guardaste la aplicacion es DEMASIADO LARGA:")
        print(f"Ruta: {project_dir}")
        print("\nWindows tiene un limite estricto de caracteres para los nombres de archivo (MAX_PATH).")
        print("PyInstaller fallará (FileNotFoundError) al intentar crear las carpetas internas.")
        print("\nSOLUCIÓN: Mueve la carpeta completa del proyecto a una ruta más corta, por ejemplo:")
        print("C:\\MACHOTES")
        print("Y vuelve a intentar correr este script desde ahí.")
        print("==================================================\n")

        sys.exit(1)

    os.chdir(project_dir)

    # PyInstaller options
    # We use start_app.py as the entry point so it shows the splash screen
    # --windowed hides the black console window
    # --icon sets the .exe icon
    # --name sets the generated .exe name

    # CustomTkinter requires its theme and assets to be included explicitly
    import customtkinter
    ctk_path = Path(customtkinter.__file__).parent

    # Verify icon exists, fallback to no icon if missing
    icon_args = []
    if (project_dir / "triforce.ico").exists():
        icon_args = ["--icon", "triforce.ico", "--add-data", f"triforce.ico{os.pathsep}."]

    png_args = []
    if (project_dir / "triforce.png").exists():
        png_args = ["--add-data", f"triforce.png{os.pathsep}."]

    # Building the command
    command = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--name", "Machotes",
    ] + icon_args + png_args + [

        # Include CustomTkinter assets
        "--add-data", f"{ctk_path}{os.pathsep}customtkinter/",

        # Hidden imports that PyInstaller sometimes misses
        "--hidden-import", "pandas",
        "--hidden-import", "matplotlib",
        "--hidden-import", "pdfplumber",
        "--hidden-import", "fitz",
        "--hidden-import", "openpyxl",
        "--hidden-import", "plyer",
        "--hidden-import", "plyer.platforms.win.notification",
        "--hidden-import", "defusedxml",
        "--hidden-import", "reportlab",
        "--hidden-import", "PIL",
        "--hidden-import", "PIL._tkinter_finder",

        "start_app.py"
    ]

    print("\nEjecutando PyInstaller. Esto puede tomar varios minutos...")
    print("Comando: " + " ".join(command))

    try:
        subprocess.check_call(command)
        print("\n==================================================")
        print("                 ¡CONSTRUCCIÓN EXITOSA!             ")
        print("==================================================")
        print(f"Tu archivo ejecutable está listo en:")
        print(f"{project_dir / 'dist' / 'Machotes' / 'Machotes.exe'}")
        print("\nPara distribuir la aplicación, simplemente copia toda la carpeta 'Machotes'")
        print("que está dentro de 'dist' a otra computadora, ¡y listo!")

        # Opcional: Limpiar carpetas temporales de compilación
        if (project_dir / "build").exists():
            shutil.rmtree(project_dir / "build")

    except subprocess.CalledProcessError as e:
        print(f"\n[Error] Ocurrió un problema durante la compilación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
