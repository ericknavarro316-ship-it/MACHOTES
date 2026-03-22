import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sys
import threading
import os
import machote_generator as mg
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# Estas 3 líneas mágicas obligan a Python a pararse en la carpeta correcta
directorio_actual = os.path.dirname(os.path.abspath(__file__))
os.chdir(directorio_actual)

ctk.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class RedirectText(object):
    def __init__(self, text_widget):
        self.output = text_widget

    def write(self, string):
        self.output.insert("end", string)
        self.output.see("end")

    def flush(self):
        pass

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Panel de Control - Inventario y Machotes")
        self.geometry("1100x700")

        # Configurar grid layout (1x2)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Frame de Navegación Lateral (Sidebar) ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="MOVILIDAD\n& SCOOTER ZONE", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_dashboard = ctk.CTkButton(self.sidebar_frame, text="📊 Dashboard", command=self.show_dashboard)
        self.btn_dashboard.grid(row=1, column=0, padx=20, pady=10)
        
        self.btn_inventario = ctk.CTkButton(self.sidebar_frame, text="📋 Ver Inventario", command=self.show_inventario)
        self.btn_inventario.grid(row=2, column=0, padx=20, pady=10)

        self.btn_machotes = ctk.CTkButton(self.sidebar_frame, text="🚀 Generador Machotes", command=self.show_machotes)
        self.btn_machotes.grid(row=3, column=0, padx=20, pady=10)

        self.btn_cargar = ctk.CTkButton(self.sidebar_frame, text="📦 Ingresar Mercancía", command=self.show_cargar)
        self.btn_cargar.grid(row=4, column=0, padx=20, pady=10)

        self.btn_xml = ctk.CTkButton(self.sidebar_frame, text="✅ Validar XML", command=self.show_xml)
        self.btn_xml.grid(row=5, column=0, padx=20, pady=10)

        self.appearance_mode_label = ctk.CTkLabel(self.sidebar_frame, text="Modo Visual:", anchor="w")
        self.appearance_mode_label.grid(row=6, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=7, column=0, padx=20, pady=(10, 20))

        # --- Contenedor Principal (Main Frame) ---
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_container.grid(row=0, column=1, sticky="nsew")
        self.main_container.grid_rowconfigure(0, weight=1)
        self.main_container.grid_columnconfigure(0, weight=1)

        # Crear los frames de cada sección
        self.frame_dashboard = FrameDashboard(self.main_container, self)
        self.frame_inventario = FrameInventario(self.main_container, self)
        self.frame_machotes = FrameMachotes(self.main_container, self)
        self.frame_cargar = FrameCargar(self.main_container, self)
        self.frame_xml = FrameXML(self.main_container, self)

        # Log de sistema unificado
        self.log_frame = ctk.CTkFrame(self, height=150, corner_radius=0)
        self.log_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.log_frame.grid_propagate(False)
        self.log_frame.grid_columnconfigure(0, weight=1)
        self.log_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(self.log_frame, text="Registro del Sistema:").grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
        self.log_text = ctk.CTkTextbox(self.log_frame, font=("Consolas", 12))
        self.log_text.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        
        sys.stdout = RedirectText(self.log_text)

        # Mostrar la primera vista
        self.show_dashboard()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

    def hide_all_frames(self):
        self.frame_dashboard.grid_forget()
        self.frame_inventario.grid_forget()
        self.frame_machotes.grid_forget()
        self.frame_cargar.grid_forget()
        self.frame_xml.grid_forget()

    def show_dashboard(self):
        self.hide_all_frames()
        self.frame_dashboard.grid(row=0, column=0, sticky="nsew")
        self.frame_dashboard.cargar_datos() # Refrescar al abrir

    def show_inventario(self):
        self.hide_all_frames()
        self.frame_inventario.grid(row=0, column=0, sticky="nsew")
        self.frame_inventario.cargar_datos()

    def show_machotes(self):
        self.hide_all_frames()
        self.frame_machotes.grid(row=0, column=0, sticky="nsew")

    def show_cargar(self):
        self.hide_all_frames()
        self.frame_cargar.grid(row=0, column=0, sticky="nsew")

    def show_xml(self):
        self.hide_all_frames()
        self.frame_xml.grid(row=0, column=0, sticky="nsew")

    def correr_en_hilo(self, funcion, *args):
        hilo = threading.Thread(target=funcion, args=args)
        hilo.start()


class FrameDashboard(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.app = app_instance
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.label_titulo = ctk.CTkLabel(self, text="Dashboard Analítico", font=ctk.CTkFont(size=24, weight="bold"))
        self.label_titulo.grid(row=0, column=0, columnspan=4, pady=(15, 10))

        # Tarjetas (Cards) - Más compactas
        self.card_total_dinero = ctk.CTkFrame(self, fg_color=("#E0E0E0", "#2B2B2B"), height=70)
        self.card_total_dinero.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.card_total_dinero.grid_propagate(False)
        ctk.CTkLabel(self.card_total_dinero, text="Valor Total ($)", font=ctk.CTkFont(size=12)).pack(pady=(5,0))
        self.lbl_total_dinero = ctk.CTkLabel(self.card_total_dinero, text="$0.00", font=ctk.CTkFont(size=20, weight="bold"), text_color="#4CAF50")
        self.lbl_total_dinero.pack()

        self.card_piezas = ctk.CTkFrame(self, fg_color=("#E0E0E0", "#2B2B2B"), height=70)
        self.card_piezas.grid(row=1, column=1, padx=10, pady=5, sticky="nsew")
        self.card_piezas.grid_propagate(False)
        ctk.CTkLabel(self.card_piezas, text="Total Piezas", font=ctk.CTkFont(size=12)).pack(pady=(5,0))
        self.lbl_piezas = ctk.CTkLabel(self.card_piezas, text="0", font=ctk.CTkFont(size=20, weight="bold"), text_color="#2196F3")
        self.lbl_piezas.pack()

        self.card_porcentaje_xml = ctk.CTkFrame(self, fg_color=("#E0E0E0", "#2B2B2B"), height=70)
        self.card_porcentaje_xml.grid(row=1, column=2, padx=10, pady=5, sticky="nsew")
        self.card_porcentaje_xml.grid_propagate(False)
        ctk.CTkLabel(self.card_porcentaje_xml, text="Inventario Facturado", font=ctk.CTkFont(size=12)).pack(pady=(5,0))
        self.lbl_porcentaje_xml = ctk.CTkLabel(self.card_porcentaje_xml, text="0%", font=ctk.CTkFont(size=20, weight="bold"), text_color="#FF9800")
        self.lbl_porcentaje_xml.pack()
        
        self.card_estado_actual = ctk.CTkFrame(self, fg_color=("#E0E0E0", "#2B2B2B"), height=70)
        self.card_estado_actual.grid(row=1, column=3, padx=10, pady=5, sticky="nsew")
        self.card_estado_actual.grid_propagate(False)
        ctk.CTkLabel(self.card_estado_actual, text="Filtro Analítico:", font=ctk.CTkFont(size=12)).pack(pady=(5,0))
        self.opcion_vista_graficas = ctk.CTkOptionMenu(self.card_estado_actual, values=["Disponible (REPORTE)", "Usado (USADOS)", "Facturado (XML)"], 
                                                       command=self.actualizar_vista_graficas, height=25, font=ctk.CTkFont(size=11))
        self.opcion_vista_graficas.pack(pady=(2,0))
        
        # Contenedor de visualización inferior (Gráfica + Tabla)
        self.frame_visual = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_visual.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)
        self.frame_visual.grid_columnconfigure(0, weight=1) # Pastel más grande
        self.frame_visual.grid_columnconfigure(1, weight=1) # Tabla
        self.frame_visual.grid_rowconfigure(0, weight=1)
        
        # Placeholder for matplotlib canvas
        self.canvas_sucursales = None
        self.dataframes_cache = {}
        self.totales_cache = {} # Para calcular porcentajes globales
        
        # Area Grafica Izquierda
        self.frame_grafica_container = ctk.CTkFrame(self.frame_visual, fg_color="transparent")
        self.frame_grafica_container.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Tabla Derecha
        self.frame_tabla_resumen = ctk.CTkFrame(self.frame_visual)
        self.frame_tabla_resumen.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
        self.frame_tabla_resumen.grid_rowconfigure(1, weight=1)
        self.frame_tabla_resumen.grid_columnconfigure(0, weight=1)
        
        self.lbl_tabla_titulo = ctk.CTkLabel(self.frame_tabla_resumen, text="Resumen de Modelos", font=ctk.CTkFont(weight="bold"))
        self.lbl_tabla_titulo.grid(row=0, column=0, pady=5)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2B2B2B", foreground="white", fieldbackground="#2B2B2B",
                        rowheight=25, borderwidth=0, font=('Arial', 10))
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", relief="flat", font=('Arial', 11, 'bold'))
        
        self.tree_resumen = ttk.Treeview(self.frame_tabla_resumen, columns=("Sucursal", "Modelo", "Total"), show="headings")
        self.tree_resumen.heading("Sucursal", text="Sucursal")
        self.tree_resumen.heading("Modelo", text="Modelo")
        self.tree_resumen.heading("Total", text="Valor Total ($)")
        
        self.tree_resumen.column("Sucursal", width=80, anchor="center")
        self.tree_resumen.column("Modelo", width=120, anchor="w")
        self.tree_resumen.column("Total", width=100, anchor="e")
        
        scroll_y = ctk.CTkScrollbar(self.frame_tabla_resumen, command=self.tree_resumen.yview)
        scroll_y.grid(row=1, column=1, sticky="ns")
        self.tree_resumen.configure(yscrollcommand=scroll_y.set)
        self.tree_resumen.grid(row=1, column=0, sticky="nsew", padx=(5,0), pady=(0,5))

    def cargar_datos(self):
        def proceso():
            try:
                df_reporte, df_usados, df_xml, _ = mg.load_data()
                
                self.dataframes_cache = {
                    "Disponible (REPORTE)": df_reporte,
                    "Usado (USADOS)": df_usados,
                    "Facturado (XML)": df_xml
                }
                
                # KPIs Globales para porcentajes
                total_piezas_reporte = len(df_reporte)
                total_piezas_usados = len(df_usados) if not df_usados.empty else 0
                total_piezas_xml = len(df_xml) if not df_xml.empty else 0
                
                total_historico = total_piezas_reporte + total_piezas_usados
                porcentaje_xml = (total_piezas_xml / total_historico * 100) if total_historico > 0 else 0
                
                self.totales_cache = {
                    "porcentaje_xml": porcentaje_xml
                }
                
                # Actualizar Graficas en el hilo principal usando la vista seleccionada actual
                self.after(0, self.actualizar_vista_graficas, self.opcion_vista_graficas.get())
                
            except Exception as e:
                print(f"Error cargando dashboard: {e}")
        self.app.correr_en_hilo(proceso)
        
    def actualizar_vista_graficas(self, vista_seleccionada):
        df_a_graficar = self.dataframes_cache.get(vista_seleccionada)
        if df_a_graficar is not None:
            # 1. Actualizar Tarjetas Dinámicas (Monto y Piezas de esta pestaña en específico)
            total_dinero = df_a_graficar['TOTAL'].sum() if 'TOTAL' in df_a_graficar.columns else 0
            total_piezas = len(df_a_graficar)
            
            self.lbl_total_dinero.configure(text=f"${total_dinero:,.2f}")
            self.lbl_piezas.configure(text=f"{total_piezas}")
            
            # El KPI de facturado es estático global
            porcentaje_xml = self.totales_cache.get("porcentaje_xml", 0)
            self.lbl_porcentaje_xml.configure(text=f"{porcentaje_xml:.1f}%")
            
            # 2. Dibujar Gráfica de Pastel Grande
            self.dibujar_grafica_pastel(df_a_graficar, vista_seleccionada)
            
            # 3. Llenar Tabla de Resumen
            self.llenar_tabla_resumen(df_a_graficar, vista_seleccionada)
            
    def llenar_tabla_resumen(self, df, titulo_estado):
        self.lbl_tabla_titulo.configure(text=f"Resumen de Modelos ({titulo_estado.split(' ')[0]})")
        
        for i in self.tree_resumen.get_children():
            self.tree_resumen.delete(i)
            
        if df is None or df.empty or 'SUCURSAL' not in df.columns or 'MODELO BASE' not in df.columns or 'TOTAL' not in df.columns:
            return
            
        # Agrupar por Sucursal y Modelo y sumar el Total
        df['TOTAL'] = pd.to_numeric(df['TOTAL'], errors='coerce').fillna(0)
        resumen = df.groupby(['SUCURSAL', 'MODELO BASE'])['TOTAL'].sum().reset_index()
        
        # Ordenar de mayor a menor por total
        resumen = resumen.sort_values(by='TOTAL', ascending=False)
        
        for _, row in resumen.iterrows():
            total_val = row['TOTAL']
            if total_val > 0:
                self.tree_resumen.insert("", "end", values=(row['SUCURSAL'], row['MODELO BASE'], f"${total_val:,.2f}"))
        
    def dibujar_grafica_pastel(self, df, titulo_estado):
        if self.canvas_sucursales:
            self.canvas_sucursales.get_tk_widget().destroy()
            
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#2B2B2B" if is_dark else "#F0F0F0"
        text_color = "white" if is_dark else "black"
        
        # Gráfica Sucursales Más Grande
        fig1 = Figure(figsize=(6, 4), dpi=100, facecolor=bg_color)
        ax1 = fig1.add_subplot(111)
        
        if df is not None and not df.empty and 'SUCURSAL' in df.columns:
            counts = df['SUCURSAL'].value_counts()
            if not counts.empty:
                wedges, texts, autotexts = ax1.pie(counts, labels=counts.index, autopct='%1.1f%%', startangle=90, 
                                                   textprops={'color': text_color, 'fontsize': 10},
                                                   colors=['#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#E91E63'])
                ax1.set_title(f"Distribución de Piezas por Sucursal", color=text_color, fontsize=12, pad=15)
                # Hacer que sea un gráfico de "Dona" (Donut chart) para verse más moderno
                centre_circle = fig1.gca().add_artist(Figure.patch.Circle((0,0),0.70,fc=bg_color))
            else:
                ax1.text(0.5, 0.5, "Sin datos de sucursal", ha='center', va='center', color=text_color)
                ax1.axis('off')
        else:
            ax1.text(0.5, 0.5, "Sin datos disponibles", ha='center', va='center', color=text_color)
            ax1.axis('off')
                
        fig1.tight_layout()
        self.canvas_sucursales = FigureCanvasTkAgg(fig1, master=self.frame_grafica_container)
        self.canvas_sucursales.draw()
        self.canvas_sucursales.get_tk_widget().pack(fill="both", expand=True)


class FrameInventario(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.app = app_instance
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.dfs = {}  # Para guardar los dataframes cargados
        
        # --- Top: Buscador ---
        self.frame_top = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_top.grid(row=0, column=0, padx=20, pady=(20, 10), sticky="ew")
        
        ctk.CTkLabel(self.frame_top, text="Inventario General", font=ctk.CTkFont(size=24, weight="bold")).pack(side="left")
        
        self.entry_busqueda = ctk.CTkEntry(self.frame_top, placeholder_text="Buscar modelo, serie o sucursal...", width=300)
        self.entry_busqueda.pack(side="right", padx=(10, 0))
        self.entry_busqueda.bind("<KeyRelease>", self.filtrar_tabla)
        
        # --- Medio: Pestañas ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, padx=20, pady=(0, 5), sticky="nsew")
        
        self.tab_reporte = self.tabview.add("Inventario Disponible (REPORTE)")
        self.tab_usados = self.tabview.add("Inventario Usados (USADOS)")
        self.tab_xml = self.tabview.add("Inventario Facturado (XML)")
        
        # Configurar las tablas
        self.tree_reporte = self.crear_tabla(self.tab_reporte)
        self.tree_usados = self.crear_tabla(self.tab_usados)
        self.tree_xml = self.crear_tabla(self.tab_xml)
        
        # --- Bottom: Estado ---
        self.frame_bottom = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.frame_bottom.grid(row=3, column=0, padx=20, pady=(0, 15), sticky="ew")
        self.lbl_estado = ctk.CTkLabel(self.frame_bottom, text="Mostrando 0 artículos", font=ctk.CTkFont(size=12, slant="italic"), text_color="gray")
        self.lbl_estado.pack(side="right")
        
        # Detectar cambio de pestaña para aplicar el filtro y actualizar contador
        self.tabview.configure(command=self.filtrar_tabla)
        
    def crear_tabla(self, parent_frame):
        parent_frame.grid_rowconfigure(0, weight=1)
        parent_frame.grid_columnconfigure(0, weight=1)
        
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2B2B2B", foreground="white", fieldbackground="#2B2B2B",
                        rowheight=25, borderwidth=0, font=('Arial', 10))
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", relief="flat", font=('Arial', 11, 'bold'))
        
        tree = ttk.Treeview(parent_frame, columns=("Sucursal", "Modelo", "Color", "Serie", "Total", "Extra"), show="headings")
        tree.heading("Sucursal", text="Sucursal")
        tree.heading("Modelo", text="Modelo Base")
        tree.heading("Color", text="Color")
        tree.heading("Serie", text="No. Serie")
        tree.heading("Total", text="Total")
        tree.heading("Extra", text="Dato Extra")
        
        tree.column("Sucursal", width=100)
        tree.column("Modelo", width=150)
        tree.column("Color", width=100)
        tree.column("Serie", width=150)
        tree.column("Total", width=100)
        tree.column("Extra", width=150)
        
        scroll_y = ctk.CTkScrollbar(parent_frame, command=tree.yview)
        scroll_y.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=scroll_y.set)
        
        scroll_x = ctk.CTkScrollbar(parent_frame, orientation="horizontal", command=tree.xview)
        scroll_x.grid(row=1, column=0, sticky="ew")
        tree.configure(xscrollcommand=scroll_x.set)
        
        tree.grid(row=0, column=0, sticky="nsew")
        return tree
        
    def cargar_datos(self):
        # Evitar sobrecargas y asegurar que se lea siempre que el cache esté vacío
        if self.dfs and len(self.dfs.get("Inventario Disponible (REPORTE)", [])) > 0:
            self.poblar_tablas() # Ya hay datos, solo repoblar visuales
            return
            
        def proceso():
            try:
                df_rep, df_usados, df_xml, _ = mg.load_data()
                self.dfs = {
                    "Inventario Disponible (REPORTE)": df_rep,
                    "Inventario Usados (USADOS)": df_usados,
                    "Inventario Facturado (XML)": df_xml
                }
                self.after(0, self.poblar_tablas)
            except Exception as e:
                print(f"Error cargando inventario completo: {e}")
        self.app.correr_en_hilo(proceso)
        
    def poblar_tablas(self):
        self._llenar_tree(self.tree_reporte, self.dfs.get("Inventario Disponible (REPORTE)"))
        self._llenar_tree(self.tree_usados, self.dfs.get("Inventario Usados (USADOS)"), extra_col="MACHOTE")
        self._llenar_tree(self.tree_xml, self.dfs.get("Inventario Facturado (XML)"), extra_col="UUID")
        self.filtrar_tabla() # Apply any existing search term
        
    def _llenar_tree(self, tree, df, extra_col=None):
        for i in tree.get_children():
            tree.delete(i)
            
        if df is None or df.empty:
            return
            
        # Determinar col de Serie
        col_serie = 'No de SERIE:' if 'No de SERIE:' in df.columns else None
        
        for idx, row in df.iterrows():
            sucursal = str(row.get('SUCURSAL', ''))
            modelo = str(row.get('MODELO BASE', ''))
            color = str(row.get('COLOR', ''))
            serie = str(row.get(col_serie, '')) if col_serie else ''
            
            try:
                total_val = float(row.get('TOTAL', 0))
                total_str = f"${total_val:,.2f}"
            except:
                total_str = str(row.get('TOTAL', ''))
                
            extra_val = str(row.get(extra_col, '')) if extra_col and extra_col in df.columns else ''
            
            # Guardamos un tag oculto con todo el texto para facilitar la busqueda
            texto_busqueda = f"{sucursal} {modelo} {serie}".lower()
            
            # Solo insertar si tiene serie (evitar filas vacias de encabezados)
            if serie and str(serie).lower() != 'nan':
                tree.insert("", "end", values=(sucursal, modelo, color, serie, total_str, extra_val), tags=(texto_busqueda,))
                
    def filtrar_tabla(self, event=None):
        termino = self.entry_busqueda.get().lower()
        tab_actual = self.tabview.get()
        
        if tab_actual == "Inventario Disponible (REPORTE)":
            tree = self.tree_reporte
        elif tab_actual == "Inventario Usados (USADOS)":
            tree = self.tree_usados
        else:
            tree = self.tree_xml
            
        for child in tree.get_children():
            tags = tree.item(child, "tags")
            if tags:
                texto_busqueda = tags[0]
                if termino in texto_busqueda:
                    tree.item(child, tags=(texto_busqueda, 'visible'))
                else:
                    tree.item(child, tags=(texto_busqueda, 'hidden'))
                    
        # Para ocultar realmente necesitamos usar dettach en Treeview,
        # Como es complejo, una manera sencilla es borrar y re-poblar.
        # Por rendimiento, haremos detach y reattach.
        self._aplicar_filtro_visual(tree, termino)

    def _aplicar_filtro_visual(self, tree, termino):
        # Desasociar todos y reasociar los que coinciden
        if not hasattr(tree, "all_items"):
            tree.all_items = tree.get_children()
            
        # Remover todos temporalmente
        for item in tree.get_children():
            tree.detach(item)
            
        # Re-insertar los que coinciden
        count = 0
        for item in tree.all_items:
            tags = tree.item(item, "tags")
            if tags and termino in tags[0]:
                tree.reattach(item, "", "end")
                count += 1
                
        # Actualizar label de estado
        if hasattr(self, 'lbl_estado'):
            total = len(tree.all_items)
            if termino:
                self.lbl_estado.configure(text=f"Mostrando {count} de {total} artículos (Filtrado)")
            else:
                self.lbl_estado.configure(text=f"Mostrando {total} artículos en total")

class FrameMachotes(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.app = app_instance
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        self.df_disponibles = None
        self.df_seleccion_actual = None

        # --- Zona de Filtros (Top) ---
        self.frame_filtros = ctk.CTkFrame(self)
        self.frame_filtros.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.frame_filtros.grid_columnconfigure((0,1,2,3), weight=1)

        ctk.CTkLabel(self.frame_filtros, text="Monto Objetivo ($):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.entry_monto = ctk.CTkEntry(self.frame_filtros, placeholder_text="Ej. 150000")
        self.entry_monto.grid(row=0, column=1, padx=10, pady=5, sticky="w")

        # Selector múltiple de sucursales
        self.frame_sucursales_selector = ctk.CTkFrame(self.frame_filtros, fg_color="transparent")
        self.frame_sucursales_selector.grid(row=0, column=2, columnspan=2, padx=10, pady=5, sticky="we")
        ctk.CTkLabel(self.frame_sucursales_selector, text="Sucursales:").pack(side="left", padx=(0,10))
        self.btn_select_sucursales = ctk.CTkButton(self.frame_sucursales_selector, text="Seleccionar Sucursal (Todas)", fg_color="#555555", hover_color="#666666", command=self.abrir_selector_sucursales)
        self.btn_select_sucursales.pack(side="left", fill="x", expand=True)
        self.sucursales_seleccionadas = ["TODAS"]
        self.sucursales_disponibles_cache = []
        
        self.sw_infantiles = ctk.CTkSwitch(self.frame_filtros, text="Incluir Infantiles")
        self.sw_infantiles.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        
        self.sw_motobicis = ctk.CTkSwitch(self.frame_filtros, text="Incluir Motocicletas")
        self.sw_motobicis.grid(row=1, column=1, padx=10, pady=5, sticky="w")
        
        # Selector múltiple de modelos
        self.frame_modelos_selector = ctk.CTkFrame(self.frame_filtros, fg_color="transparent")
        self.frame_modelos_selector.grid(row=1, column=2, columnspan=2, padx=10, pady=5, sticky="we")
        
        ctk.CTkLabel(self.frame_modelos_selector, text="Modelos Específicos:").pack(side="left", padx=(0,10))
        self.btn_select_modelos = ctk.CTkButton(self.frame_modelos_selector, text="Seleccionar Modelos (Todos)", fg_color="#555555", hover_color="#666666", command=self.abrir_selector_modelos)
        self.btn_select_modelos.pack(side="left", fill="x", expand=True)
        self.modelos_seleccionados = ["TODOS"]
        self.modelos_disponibles_cache = []

        self.btn_previa = ctk.CTkButton(self.frame_filtros, text="🔍 Calcular Vista Previa", command=self.calcular_previa)
        self.btn_previa.grid(row=2, column=0, columnspan=4, pady=10)
        
        # Cargar selectores dinámicos al iniciar el frame en un hilo
        self.app.correr_en_hilo(self._cargar_filtros_dinamicos)

    def _cargar_filtros_dinamicos(self):
        try:
            df_rep, _, _, _ = mg.load_data()
            if 'SUCURSAL' in df_rep.columns:
                self.sucursales_disponibles_cache = sorted([str(s) for s in df_rep['SUCURSAL'].dropna().unique() if str(s).strip() != ""])
                
            if 'MODELO BASE' in df_rep.columns:
                self.modelos_disponibles_cache = sorted([str(m) for m in df_rep['MODELO BASE'].dropna().unique() if str(m).strip() != ""])
        except Exception as e:
            print(f"Aviso: No se pudieron cargar los filtros dinámicos ({e}). Se usarán los valores por defecto.")
            
    def abrir_selector_sucursales(self):
        if not self.sucursales_disponibles_cache:
            messagebox.showinfo("Información", "Aún no hay sucursales cargadas. Espera un momento o revisa el inventario base.")
            return
            
        dialog = ctk.CTkToplevel(self)
        dialog.title("Seleccionar Sucursales")
        dialog.geometry("400x400")
        dialog.transient(self) # Hacerlo modal
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Selecciona las sucursales a incluir:", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        # Opciones globales
        frame_globals = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_globals.pack(fill="x", padx=20, pady=5)
        
        def select_all():
            for var in checkboxes_vars.values(): var.set(1)
        def deselect_all():
            for var in checkboxes_vars.values(): var.set(0)
            
        ctk.CTkButton(frame_globals, text="Seleccionar Todas", width=120, command=select_all).pack(side="left", padx=5)
        ctk.CTkButton(frame_globals, text="Ninguna", width=120, fg_color="#777777", command=deselect_all).pack(side="right", padx=5)
        
        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        checkboxes_vars = {}
        for suc in self.sucursales_disponibles_cache:
            var = ctk.IntVar(value=1 if "TODAS" in self.sucursales_seleccionadas or suc in self.sucursales_seleccionadas else 0)
            checkboxes_vars[suc] = var
            cb = ctk.CTkCheckBox(scroll, text=suc, variable=var)
            cb.pack(anchor="w", pady=5)
            
        def confirmar():
            seleccionados = [suc for suc, var in checkboxes_vars.items() if var.get() == 1]
            if len(seleccionados) == len(self.sucursales_disponibles_cache):
                self.sucursales_seleccionadas = ["TODAS"]
                self.btn_select_sucursales.configure(text="Seleccionar Sucursal (Todas)")
            elif len(seleccionados) == 0:
                self.sucursales_seleccionadas = ["NINGUNA"]
                self.btn_select_sucursales.configure(text="Seleccionar Sucursal (0 seleccionadas)")
            else:
                self.sucursales_seleccionadas = seleccionados
                self.btn_select_sucursales.configure(text=f"Seleccionar Sucursal ({len(seleccionados)} seleccionadas)")
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Confirmar", command=confirmar, fg_color="#4CAF50").pack(pady=10)

    def abrir_selector_modelos(self):
        if not self.modelos_disponibles_cache:
            messagebox.showinfo("Información", "Aún no hay modelos cargados. Espera un momento o revisa el inventario base.")
            return
            
        dialog = ctk.CTkToplevel(self)
        dialog.title("Seleccionar Modelos")
        dialog.geometry("400x500")
        dialog.transient(self) # Hacerlo modal
        dialog.grab_set()
        
        ctk.CTkLabel(dialog, text="Selecciona los modelos a incluir:", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        # Opciones globales
        frame_globals = ctk.CTkFrame(dialog, fg_color="transparent")
        frame_globals.pack(fill="x", padx=20, pady=5)
        
        def select_all():
            for var in checkboxes_vars.values(): var.set(1)
        def deselect_all():
            for var in checkboxes_vars.values(): var.set(0)
            
        ctk.CTkButton(frame_globals, text="Seleccionar Todos", width=120, command=select_all).pack(side="left", padx=5)
        ctk.CTkButton(frame_globals, text="Ninguno", width=120, fg_color="#777777", command=deselect_all).pack(side="right", padx=5)
        
        scroll = ctk.CTkScrollableFrame(dialog)
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        checkboxes_vars = {}
        for mod in self.modelos_disponibles_cache:
            var = ctk.IntVar(value=1 if "TODOS" in self.modelos_seleccionados or mod in self.modelos_seleccionados else 0)
            checkboxes_vars[mod] = var
            cb = ctk.CTkCheckBox(scroll, text=mod, variable=var)
            cb.pack(anchor="w", pady=5)
            
        def confirmar():
            seleccionados = [mod for mod, var in checkboxes_vars.items() if var.get() == 1]
            if len(seleccionados) == len(self.modelos_disponibles_cache):
                self.modelos_seleccionados = ["TODOS"]
                self.btn_select_modelos.configure(text="Seleccionar Modelos (Todos)")
            elif len(seleccionados) == 0:
                self.modelos_seleccionados = ["NINGUNO"] # Esto hará que no encuentre nada
                self.btn_select_modelos.configure(text="Seleccionar Modelos (0 seleccionados)")
            else:
                self.modelos_seleccionados = seleccionados
                self.btn_select_modelos.configure(text=f"Seleccionar Modelos ({len(seleccionados)} seleccionados)")
            dialog.destroy()
            
        ctk.CTkButton(dialog, text="Confirmar", command=confirmar, fg_color="#4CAF50").pack(pady=10)

        # --- Zona de Vista Previa (Centro) ---
        self.frame_tabla = ctk.CTkFrame(self)
        self.frame_tabla.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        
        self.lbl_resumen = ctk.CTkLabel(self.frame_tabla, text="Resumen: $0.00 (0 artículos)", font=ctk.CTkFont(weight="bold"))
        self.lbl_resumen.pack(pady=5)
        
        # Usar Treeview normal para la tabla dentro de un frame de customtkinter
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2B2B2B", foreground="white", fieldbackground="#2B2B2B",
                        rowheight=25, borderwidth=0, font=('Arial', 10))
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#1f538d", foreground="white", relief="flat", font=('Arial', 11, 'bold'))
        
        self.tree_frame = ctk.CTkFrame(self.frame_tabla)
        self.tree_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.tree = ttk.Treeview(self.tree_frame, columns=("Sucursal", "Modelo", "Serie", "Total"), show="headings", height=10)
        self.tree.heading("Sucursal", text="Sucursal")
        self.tree.heading("Modelo", text="Modelo")
        self.tree.heading("Serie", text="No. Serie")
        self.tree.heading("Total", text="Total ($)")
        
        self.tree.column("Sucursal", width=100)
        self.tree.column("Modelo", width=150)
        self.tree.column("Serie", width=150)
        self.tree.column("Total", width=100)
        
        scroll_y = ctk.CTkScrollbar(self.tree_frame, command=self.tree.yview)
        scroll_y.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.pack(fill="both", expand=True)

        # --- Zona de Acciones (Bottom) ---
        self.frame_acciones = ctk.CTkFrame(self)
        self.frame_acciones.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        ctk.CTkLabel(self.frame_acciones, text="Empresa:").pack(side="left", padx=5)
        self.entry_empresa = ctk.CTkEntry(self.frame_acciones, width=200)
        self.entry_empresa.insert(0, "MOVILIDAD ELECTRICA DE JALISCO")
        self.entry_empresa.pack(side="left", padx=5)
        
        ctk.CTkLabel(self.frame_acciones, text="Cuenta:").pack(side="left", padx=5)
        self.entry_cuenta = ctk.CTkEntry(self.frame_acciones, width=80)
        self.entry_cuenta.insert(0, "MP")
        self.entry_cuenta.pack(side="left", padx=5)

        self.btn_exportar = ctk.CTkButton(self.frame_acciones, text="💾 Confirmar y Exportar Excel", fg_color="#4CAF50", hover_color="#45a049", state="disabled", command=self.exportar_machote)
        self.btn_exportar.pack(side="right", padx=10, pady=10)
        
        self.btn_mezclar = ctk.CTkButton(self.frame_acciones, text="🔀 Mezclar de Nuevo", fg_color="#FF9800", hover_color="#F57C00", state="disabled", command=self.calcular_previa)
        self.btn_mezclar.pack(side="right", padx=10, pady=10)

    def calcular_previa(self):
        monto_str = self.entry_monto.get().replace(",", "")
        if not monto_str:
            messagebox.showwarning("Error", "Debe ingresar un monto objetivo.")
            return
            
        try:
            monto = float(monto_str)
        except ValueError:
            messagebox.showwarning("Error", "El monto debe ser un número (Ej. 150000).")
            return
            
        inc_infantiles = self.sw_infantiles.get() == 1
        inc_motobicis = self.sw_motobicis.get() == 1
        sucursales_list = self.sucursales_seleccionadas
        modelos_list = self.modelos_seleccionados
        
        def proceso():
            print(f"Calculando vista previa para ${monto}...")
            try:
                # 1. Cargar datos si no están cargados
                if self.df_disponibles is None:
                    df_reporte, _, _, df_precios = mg.load_data()
                    self.df_disponibles_base = df_reporte
                    self.df_precios_base = df_precios
                    
                # 2. Filtrar
                df_filtrado = mg.procesar_inventario(
                    self.df_disponibles_base, 
                    self.df_precios_base,
                    incluir_infantiles=inc_infantiles,
                    incluir_motobicis=inc_motobicis,
                    sucursales=sucursales_list,
                    modelos=modelos_list
                )
                
                # 3. Seleccionar
                df_seleccion = mg.seleccionar_articulos(df_filtrado, monto)
                
                if df_seleccion.empty:
                    print("⚠️ No se encontraron artículos suficientes con esos filtros para alcanzar el monto.")
                    self.after(0, self.limpiar_tabla_sin_deshabilitar_mezclar)
                    return
                    
                self.df_seleccion_actual = df_seleccion
                
                # 4. Actualizar UI
                total_real = df_seleccion['TOTAL'].sum()
                cant_articulos = len(df_seleccion)
                
                self.after(0, self.actualizar_tabla, df_seleccion, total_real, cant_articulos)
                print(f"✅ Selección completada: {cant_articulos} artículos por ${total_real:,.2f}")
                
            except Exception as e:
                import traceback
                print(f"Error en cálculo: {e}")
                traceback.print_exc()
                
        self.app.correr_en_hilo(proceso)

    def limpiar_tabla(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.lbl_resumen.configure(text="Resumen: $0.00 (0 artículos)")
        self.btn_exportar.configure(state="disabled")
        self.btn_mezclar.configure(state="disabled")
        
    def limpiar_tabla_sin_deshabilitar_mezclar(self):
        # Limpia pero deja el botón de mezclar encendido para que el usuario intente otra semilla aleatoria
        for i in self.tree.get_children():
            self.tree.delete(i)
        self.lbl_resumen.configure(text="⚠️ No se encontraron artículos suficientes. Intenta mezclar de nuevo o cambia filtros.")
        self.btn_exportar.configure(state="disabled")
        self.btn_mezclar.configure(state="normal")

    def actualizar_tabla(self, df, total, cant):
        for i in self.tree.get_children():
            self.tree.delete(i)
        
        for idx, row in df.iterrows():
            self.tree.insert("", "end", values=(row['SUCURSAL'], row['MODELO BASE'], row['No de SERIE:'], f"${row['TOTAL']:,.2f}"))
            
        self.lbl_resumen.configure(text=f"Resumen: ${total:,.2f} ({cant} artículos seleccionados)")
        self.btn_exportar.configure(state="normal")
        self.btn_mezclar.configure(state="normal")

    def exportar_machote(self):
        if self.df_seleccion_actual is None or self.df_seleccion_actual.empty:
            return
            
        empresa = self.entry_empresa.get()
        cuenta = self.entry_cuenta.get()
        monto = float(self.entry_monto.get().replace(",", ""))
        
        def proceso():
            print("Exportando machote y actualizando inventario base...")
            try:
                # Intentar extraer RFC
                rfc_pdf, empresa_pdf = mg.extraer_datos_empresa(empresa)
                rfc_final = rfc_pdf if rfc_pdf else "MEJ123456789"
                empresa_final = empresa_pdf if empresa_pdf else empresa
                
                # Generar Excel Machote
                ruta_machote, nombre_machote = mg.generar_machote(self.df_seleccion_actual, monto, empresa_final, rfc_final, cuenta)
                print(f"Machote generado en: {ruta_machote}")
                
                # Actualizar Inventario
                nuevo_inv_path = mg.actualizar_inventario_base(self.df_seleccion_actual, nombre_machote)
                
                # Reemplazar base por el nuevo
                import shutil
                if os.path.exists(nuevo_inv_path):
                    shutil.move(nuevo_inv_path, mg.PATH_INVENTARIO)
                    print("✅ Inventario base actualizado con éxito.")
                
                # Forzar recarga de datos en este frame y en el inventario general
                self.df_disponibles = None 
                self.after(0, self.limpiar_tabla)
                
                # Forzar al cache del inventario general a vaciarse para obligar su recarga si se entra a esa pestaña
                self.app.frame_inventario.dfs = {}
                
                self.after(0, lambda: messagebox.showinfo("Éxito", "Machote exportado y el inventario base ha sido actualizado."))
                self.after(0, self.app.show_dashboard) # Volver al dashboard para ver el nuevo inventario
                
            except Exception as e:
                import traceback
                print(f"Error fatal exportando: {e}")
                traceback.print_exc()
                
        self.app.correr_en_hilo(proceso)

class FrameCargar(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.app = app_instance
        
        self.label = ctk.CTkLabel(self, text="Ingresar Nueva Mercancía", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=40)
        
        self.info = ctk.CTkLabel(self, text="Selecciona el archivo PDF exportado del sistema de inventarios.\nEl programa extraerá los modelos, colores y números de serie\npara agregarlos automáticamente al inventario base.")
        self.info.pack(pady=20)
        
        self.btn_cargar = ctk.CTkButton(self, text="📄 Seleccionar PDF y Cargar", font=ctk.CTkFont(size=16), height=50, command=self.ejecutar_carga)
        self.btn_cargar.pack(pady=20)

    def ejecutar_carga(self):
        ruta_pdf = filedialog.askopenfilename(title="Seleccionar PDF de Reporte", filetypes=[("PDF Files", "*.pdf")])
        if ruta_pdf:
            def proceso():
                print(f"--- INICIANDO CARGA DESDE: {os.path.basename(ruta_pdf)} ---")
                try:
                    mg.cargar_inventario(ruta_pdf, mg.PATH_INVENTARIO)
                    
                    import shutil
                    path_cargado = mg.PATH_INVENTARIO.replace(".xlsx", "_CARGADO.xlsx")
                    if os.path.exists(path_cargado):
                        shutil.move(path_cargado, mg.PATH_INVENTARIO)
                        print("¡Inventario base actualizado con la nueva mercancía!")
                        
                    self.after(0, lambda: messagebox.showinfo("Éxito", "Inventario cargado exitosamente."))
                    self.after(0, self.app.show_dashboard)
                except Exception as e:
                    print(f"Error en carga: {e}")
            self.app.correr_en_hilo(proceso)

class FrameXML(ctk.CTkFrame):
    def __init__(self, master, app_instance):
        super().__init__(master, corner_radius=0, fg_color="transparent")
        self.app = app_instance
        
        self.label = ctk.CTkLabel(self, text="Validación de XMLs (UUIDs)", font=ctk.CTkFont(size=24, weight="bold"))
        self.label.pack(pady=40)
        
        self.info = ctk.CTkLabel(self, text="Selecciona la carpeta que contiene las facturas en formato XML.\nEl sistema buscará los números de serie dentro de los XML\ny actualizará el inventario con sus respectivos UUIDs.")
        self.info.pack(pady=20)
        
        self.btn_xml = ctk.CTkButton(self, text="📁 Seleccionar Carpeta de XMLs", font=ctk.CTkFont(size=16), height=50, fg_color="#FF9800", hover_color="#F57C00", command=self.ejecutar_xml)
        self.btn_xml.pack(pady=20)

    def ejecutar_xml(self):
        carpeta_xml = filedialog.askdirectory(title="Seleccionar carpeta con facturas XML")
        if carpeta_xml:
            def proceso():
                print(f"--- INICIANDO VALIDACIÓN DE UUIDs EN: {os.path.basename(carpeta_xml)} ---")
                try:
                    mg.actualizar_inventario_uuid(carpeta_xml, mg.PATH_INVENTARIO)
                    
                    import shutil
                    path_actualizado = mg.PATH_INVENTARIO.replace(".xlsx", "_UUID_ACTUALIZADO.xlsx")
                    if os.path.exists(path_actualizado):
                        shutil.move(path_actualizado, mg.PATH_INVENTARIO)
                        print("¡Inventario base cruzado con UUIDs de los XMLs!")
                        
                    self.after(0, lambda: messagebox.showinfo("Éxito", "UUIDs procesados y guardados en el inventario."))
                    self.after(0, self.app.show_dashboard)
                except Exception as e:
                    print(f"Error procesando XMLs: {e}")
            self.app.correr_en_hilo(proceso)

if __name__ == "__main__":
    app = App()
    app.mainloop()