import tkinter as tk
from tkinter import messagebox, filedialog
import os
import sys
import threading

directorio_actual = os.path.dirname(os.path.abspath(__file__))
os.chdir(directorio_actual)

class RedirectText(object):
    def __init__(self, text_widget):
        self.output = text_widget

    def write(self, string):
        self.output.insert(tk.END, string)
        self.output.see(tk.END)

    def flush(self):
        pass

import machote_generator as mg

class AplicacionMachotes:
    def __init__(self, root):
        self.root = root
        self.root.title("Generador Automático de Machotes e Inventario")
        self.root.geometry("650x550")
        self.root.configure(padx=20, pady=20)
        
        frame_generar = tk.LabelFrame(root, text=" 1. Generar Nuevo Machote ", padx=10, pady=10)
        frame_generar.pack(fill="x", pady=5)
        
        tk.Label(frame_generar, text="Monto Objetivo ($):").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_monto = tk.Entry(frame_generar, width=15)
        self.entry_monto.grid(row=0, column=1, sticky="w", pady=2)
        
        tk.Label(frame_generar, text="Empresa (Opcional):").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_empresa = tk.Entry(frame_generar, width=30)
        self.entry_empresa.insert(0, "MOVILIDAD ELECTRICA DE JALISCO")
        self.entry_empresa.grid(row=1, column=1, sticky="w", pady=2)
        
        tk.Label(frame_generar, text="Cuenta:").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_cuenta = tk.Entry(frame_generar, width=15)
        self.entry_cuenta.insert(0, "MP")
        self.entry_cuenta.grid(row=2, column=1, sticky="w", pady=2)
        
        tk.Button(frame_generar, text="🚀 Generar Machote e Inventario", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
                  command=self.ejecutar_machote).grid(row=3, column=0, columnspan=2, pady=10)
                  
        frame_cargar = tk.LabelFrame(root, text=" 2. Ingresar Nueva Mercancía (PDF) ", padx=10, pady=10)
        frame_cargar.pack(fill="x", pady=5)
        
        tk.Button(frame_cargar, text="📄 Seleccionar PDF y Cargar", bg="#2196F3", fg="white", font=("Arial", 10),
                  command=self.ejecutar_carga).pack(pady=5)
                  
        frame_xml = tk.LabelFrame(root, text=" 3. Validar Facturas (XML) ", padx=10, pady=10)
        frame_xml.pack(fill="x", pady=5)
        
        tk.Button(frame_xml, text="📁 Seleccionar Carpeta de XMLs y Validar", bg="#FF9800", fg="white", font=("Arial", 10),
                  command=self.ejecutar_xml).pack(pady=5)
                  
        tk.Label(root, text="Registro de Actividades:").pack(anchor="w", pady=(10, 0))
        self.texto_log = tk.Text(root, height=10, bg="black", fg="lime", font=("Consolas", 9))
        self.texto_log.pack(fill="both", expand=True)
        
        sys.stdout = RedirectText(self.texto_log)
        
        print("✅ Sistema Iniciado y Listo.")
        print("-> Los archivos base (Excel y PDFs) deben estar en la carpeta 'machotes'.")

    def correr_en_hilo(self, funcion, *args):
        hilo = threading.Thread(target=funcion, args=args)
        hilo.start()

    def ejecutar_machote(self):
        monto_str = self.entry_monto.get().replace(",", "")
        empresa = self.entry_empresa.get()
        cuenta = self.entry_cuenta.get()
        
        if not monto_str:
            messagebox.showwarning("Error", "Debe ingresar un monto objetivo.")
            return
            
        try:
            monto = float(monto_str)
        except ValueError:
            messagebox.showwarning("Error", "El monto debe ser un número (Ej. 150000).")
            return
            
        def proceso():
            print(f"\n--- INICIANDO GENERACIÓN DE MACHOTE: ${monto} ---")
            try:
                # Modificamos los argumentos del sistema (sys.argv) como si lo corrieramos por terminal
                # Así usamos el mg.main() original entero sin omitir el descuento del inventario
                sys.argv = ['machote_generator.py', '--monto', str(monto), '--empresa', empresa, '--cuenta', cuenta]
                mg.main()
                
                # Una vez termina de generar el _NUEVO, renombramos automatico para que siga descontando
                import shutil
                if os.path.exists("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_NUEVO.xlsx"):
                    shutil.move("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_NUEVO.xlsx", "machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1).xlsx")
                    print("¡Inventario base actualizado listo para el siguiente machote!")
                    
                messagebox.showinfo("Éxito", "Machote y actualización de Inventario completados.")
            except Exception as e:
                import traceback
                print(f"Error fatal: {e}")
                traceback.print_exc()
                
        self.correr_en_hilo(proceso)
        
    def ejecutar_carga(self):
        ruta_pdf = filedialog.askopenfilename(title="Seleccionar PDF de Reporte de Productos", filetypes=[("PDF Files", "*.pdf")])
        if ruta_pdf:
            def proceso():
                print(f"\n--- INICIANDO CARGA DESDE: {os.path.basename(ruta_pdf)} ---")
                try:
                    sys.argv = ['machote_generator.py', '--monto', '0', '--cargar', ruta_pdf]
                    mg.main()
                    
                    import shutil
                    if os.path.exists("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_CARGADO.xlsx"):
                        shutil.move("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_CARGADO.xlsx", "machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1).xlsx")
                        print("¡Inventario base cargado con la nueva mercancía!")
                        
                    messagebox.showinfo("Éxito", "Inventario cargado exitosamente.")
                except SystemExit:
                    # Argparse o main llaman a sys.exit() que se cacha aquí, ignorar.
                    import shutil
                    if os.path.exists("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_CARGADO.xlsx"):
                        shutil.move("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_CARGADO.xlsx", "machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1).xlsx")
                        print("¡Inventario base cargado con la nueva mercancía!")
                    messagebox.showinfo("Éxito", "Inventario cargado exitosamente.")
                except Exception as e:
                    print(f"Error en carga: {e}")
            self.correr_en_hilo(proceso)

    def ejecutar_xml(self):
        carpeta_xml = filedialog.askdirectory(title="Seleccionar carpeta con facturas XML")
        if carpeta_xml:
            def proceso():
                print(f"\n--- INICIANDO VALIDACIÓN DE UUIDs EN: {os.path.basename(carpeta_xml)} ---")
                try:
                    sys.argv = ['machote_generator.py', '--monto', '0', '--xml_dir', carpeta_xml]
                    mg.main()
                    
                    import shutil
                    if os.path.exists("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_UUID_ACTUALIZADO.xlsx"):
                        shutil.move("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_UUID_ACTUALIZADO.xlsx", "machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1).xlsx")
                        print("¡Inventario base cruzado con UUIDs de los XMLs!")
                        
                    messagebox.showinfo("Éxito", "UUIDs procesados y guardados en el inventario.")
                except SystemExit:
                    import shutil
                    if os.path.exists("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_UUID_ACTUALIZADO.xlsx"):
                        shutil.move("machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1)_UUID_ACTUALIZADO.xlsx", "machotes/20 MAR 2026 REPORTE INVENTARIO_ACTUALIZADO (1).xlsx")
                        print("¡Inventario base cruzado con UUIDs de los XMLs!")
                    messagebox.showinfo("Éxito", "UUIDs procesados y guardados en el inventario.")
                except Exception as e:
                    print(f"Error procesando XMLs: {e}")
            self.correr_en_hilo(proceso)

if __name__ == "__main__":
    if not os.path.exists("machotes"):
        print("ADVERTENCIA: La carpeta 'machotes' no existe en este directorio.")
        
    root = tk.Tk()
    app = AplicacionMachotes(root)
    root.mainloop()
