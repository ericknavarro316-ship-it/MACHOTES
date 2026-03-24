import pdfplumber
import re
import fitz
import glob
import pandas as pd
import openpyxl
from copy import copy
from openpyxl.styles import Font, Border, Side, PatternFill, Alignment, Protection
import os
import sys
import argparse
from datetime import datetime

PATH_INVENTARIO = "machotes/Inventario_Final.xlsx"
PATH_MACHOTE = "machotes/EJEMPLO MACHOTE.xlsx"
PATH_PRECIOS = "machotes/Lista de precios ok.xlsx"
OUTPUT_DIR = "machotes_generados"
APP_DATA_DIR = os.path.join(os.path.dirname(__file__), "app_data")
PDF_WARNINGS_LOG = os.path.join(APP_DATA_DIR, "pdf_parse_warnings.log")

MAPEOS_MODELOS = {
    "S2 AIR V2": "S2",
    "HN-C80": "HN-C80 PRO",
    "M2MAX": "M2MAX 8.5",
    "M2MAXB": "M2MAXB10"
}


def extraer_datos_empresa(empresa_busqueda):
    # Buscar el PDF en la carpeta machotes que contenga "CSF" y el nombre de la empresa
    archivos_pdf = glob.glob(os.path.join("machotes", "*CSF*.pdf"))
    
    empresa_lower = empresa_busqueda.lower()
    mejor_coincidencia = None
    
    for archivo in archivos_pdf:
        if empresa_lower in os.path.basename(archivo).lower():
            mejor_coincidencia = archivo
            break
            
    if not mejor_coincidencia:
        print(f"No se encontró un archivo CSF para la empresa '{empresa_busqueda}'. Se usarán los datos proporcionados por defecto o argumentos.")
        return None, None
        
    print(f"Extrayendo datos de CSF: {mejor_coincidencia}")
    doc = fitz.open(mejor_coincidencia)
    text = doc[0].get_text()
    
    rfc = None
    razon_social = None
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        if "RFC:" in line and not rfc:
            if i + 1 < len(lines) and re.match(r"^[A-Z0-9&]{12,13}$", lines[i+1].strip()):
                rfc = lines[i+1].strip()
        
        if "Denominación/Razón Social:" in line:
            if i + 1 < len(lines):
                razon_social = lines[i+1].strip()
                
    if not rfc or not razon_social:
        print(f"No se pudo extraer el RFC o Razón Social del PDF {mejor_coincidencia}.")
        
    return rfc, razon_social

import db_manager

def load_data():
    if not db_manager.is_db_initialized():
        print("Base de datos SQLite no inicializada. Migrando desde Excel...")
        if not db_manager.migrate_excel_to_sqlite(PATH_INVENTARIO):
            print("Error migrando Excel, usando modo solo lectura antiguo.")
            df_reporte = pd.read_excel(PATH_INVENTARIO, sheet_name='REPORTE', header=3)
            df_usados = pd.read_excel(PATH_INVENTARIO, sheet_name='USADOS', header=3)
            try:
                df_xml = pd.read_excel(PATH_INVENTARIO, sheet_name='XML_ENCONTRADOS', header=3)
            except Exception:
                df_xml = pd.DataFrame(columns=df_reporte.columns.tolist() + ['UUID'])
        else:
            df_reporte, df_usados, df_xml = db_manager.get_inventory_dataframes()
    else:
        df_reporte, df_usados, df_xml = db_manager.get_inventory_dataframes()
        
    df_precios = pd.read_excel(PATH_PRECIOS, sheet_name='Para imprimir', header=2)
    df_precios = df_precios[['CLAVE SAT', 'DESCRIPCION', 'MODELO', 'D1']]
    df_precios.dropna(subset=['MODELO'], inplace=True)
    df_precios['MODELO'] = df_precios['MODELO'].astype(str).str.strip().str.upper()
    df_precios['CLAVE SAT'] = df_precios['CLAVE SAT'].fillna(0).astype(int).astype(str)
    
    return df_reporte, df_usados, df_xml, df_precios

def aplicar_mapeo(modelo_base):
    if pd.isna(modelo_base):
        return modelo_base
    modelo_upper = str(modelo_base).strip().upper()
    return MAPEOS_MODELOS.get(modelo_upper, modelo_upper)

def procesar_inventario(df_reporte, df_precios, incluir_infantiles=False, incluir_motobicis=False, categoria="TODAS", modelos=None, sucursales=None):
    df = df_reporte.copy()
    df['CLAVE SAT'] = df['CLAVE SAT'].astype(str)
    
    if not incluir_motobicis:
        df = df[~df['DESCRIPCION'].astype(str).str.contains("MOTOCICLETA ELECTRICA", case=False, na=False)]
        
    df['MODELO_MAPPED'] = df['MODELO BASE'].apply(aplicar_mapeo)
    df_precios_dict = df_precios.drop_duplicates(subset=['MODELO'], keep='last').set_index('MODELO').to_dict('index')
    
    for idx, row in df.iterrows():
        modelo_busqueda = row['MODELO_MAPPED']
        if modelo_busqueda in df_precios_dict:
            datos_precio = df_precios_dict[modelo_busqueda]
            try:
                d1_val = float(datos_precio['D1'])
            except:
                d1_val = None
            if pd.notna(d1_val):
                df.at[idx, 'D1'] = d1_val
            df.at[idx, 'CLAVE SAT'] = str(datos_precio['CLAVE SAT'])
            
            desc_base = str(datos_precio['DESCRIPCION']).strip()
            color = str(row['COLOR']).strip() if pd.notna(row['COLOR']) else ""
            serie = str(row['No de SERIE:']).strip()
            if color.lower() != 'nan' and color != "":
                desc_final = f"{desc_base} {modelo_busqueda} {color} NO DE SERIE:{serie}"
            else:
                desc_final = f"{desc_base} {modelo_busqueda} NO DE SERIE:{serie}"
            df.at[idx, 'DESCRIPCION'] = desc_final.upper()
            
    if not incluir_infantiles:
        df = df[~df['DESCRIPCION'].astype(str).str.contains("INFANTIL ELECTRICO", case=False, na=False)]
        df = df[df['CLAVE SAT'].astype(str) != "60141000"]
        
    if sucursales and "TODAS" not in [str(s).upper() for s in sucursales]:
        sucursales_upper = [str(s).upper() for s in sucursales]
        df = df[df['SUCURSAL'].astype(str).str.upper().isin(sucursales_upper)]
        
    if categoria != "TODAS":
        # Simplified category logic - assumes category is part of the description or base model
        # You might need to adjust this depending on how categories are actually defined in your data
        pass # Placeholder: Implement specific category logic if needed. Currently rely on models
        
    if modelos and "TODOS" not in [str(m).upper() for m in modelos]:
        modelos_upper = [str(m).upper() for m in modelos]
        df = df[df['MODELO BASE'].astype(str).str.upper().isin(modelos_upper)]

    df = df[pd.notna(df['D1'])]
    df = df[df['D1'].astype(str).str.strip() != ""]
    df = df[pd.notna(df['CLAVE SAT'])]
    
    df['CANTIDAD'] = 1
    df['D1'] = pd.to_numeric(df['D1'], errors='coerce')
    df['P. UNITARIO'] = df['D1'] / 1.16
    df['SUBTOTAL'] = df['CANTIDAD'] * df['P. UNITARIO']
    df['IVA'] = df['SUBTOTAL'] * 0.16
    df['TOTAL'] = df['SUBTOTAL'] + df['IVA']
    return df

def seleccionar_articulos(df_disponibles, monto_objetivo):
    import random
    
    # Asegurar que el algoritmo intenta diferentes combinaciones
    mejor_diferencia = float('inf')
    mejor_combinacion = []
    
    items = df_disponibles.to_dict('records')
    
    # Para hacer que tome modelos más variados, en lugar de tomar secuencialmente, 
    # intentaremos tomar muestras aleatorias repetidas veces (Monte Carlo)
    # y nos quedamos con la que se acerque más al objetivo.
    
    # 1. Intentos deterministas basicos (orden ascendente y descendente)
    df_sorted = df_disponibles.sort_values(by=['D1', 'SUCURSAL', 'MODELO BASE', 'No de SERIE:'])
    items_sorted = df_sorted.to_dict('records')
    
    for i in range(min(50, len(items_sorted))):
        suma_actual = 0
        seleccion_actual = []
        for j in range(i, len(items_sorted)):
            item = items_sorted[j]
            if suma_actual + item['TOTAL'] <= monto_objetivo + 50:
                seleccion_actual.append(item)
                suma_actual += item['TOTAL']
        diferencia = abs(monto_objetivo - suma_actual)
        if diferencia < mejor_diferencia or (diferencia == mejor_diferencia and len(seleccion_actual) > len(mejor_combinacion)):
            mejor_diferencia = diferencia
            mejor_combinacion = seleccion_actual
            
    # 2. Intentos puramente aleatorios (Monte Carlo) - Iterar 500 veces mezclando el inventario
    # Esto asegura que "pique" de diferentes modelos en lugar de acabarse un solo producto primero
    for _ in range(500):
        random.shuffle(items)
        
        suma_actual = 0
        seleccion_actual = []
        
        for item in items:
            # Tomamos un articulo al azar, si cabe lo metemos
            if suma_actual + item['TOTAL'] <= monto_objetivo + 50: # Permitir 50 de tolerancia por arriba
                seleccion_actual.append(item)
                suma_actual += item['TOTAL']
                
            # Si ya nos pasamos de una tolerancia muy chica, paramos esta iteracion para ahorrar tiempo
            if suma_actual > monto_objetivo + 50:
                break
                
        diferencia = abs(monto_objetivo - suma_actual)
        
        # Guardar si es una aproximacion mas exacta (o igual pero con MAS renglones)
        # Esto fomenta combinar artículos baratos y caros aleatoriamente
        if diferencia < mejor_diferencia:
            mejor_diferencia = diferencia
            mejor_combinacion = seleccion_actual
        elif diferencia == mejor_diferencia and len(seleccion_actual) > len(mejor_combinacion):
            mejor_combinacion = seleccion_actual
            
        # Si encuentra el exacto, podemos dejar de iterar
        if mejor_diferencia == 0:
            break
            
    # Finalmente, para mantener el desempate por modelo/serie como dice la regla H, 
    # ordenamos la combinacion ganadora antes de devolverla
    import pandas as pd
    df_resultado = pd.DataFrame(mejor_combinacion)
    if not df_resultado.empty:
        df_resultado = df_resultado.sort_values(by=['SUCURSAL', 'MODELO BASE', 'No de SERIE:'])
        
    return df_resultado

def generar_machote(df_seleccion, monto_objetivo, empresa, rfc, cuenta_mp):
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    fecha_str = datetime.now().strftime("%d %b %Y").upper()
    total_real = df_seleccion['TOTAL'].sum()
    nombre_archivo = f"{fecha_str} ${total_real:,.2f} MACHOTE {empresa} {cuenta_mp}.xlsx"
    ruta_salida = os.path.join(OUTPUT_DIR, nombre_archivo)
    
    # Manejar caso donde el machote no exista
    if not os.path.exists(PATH_MACHOTE):
        print(f"ADVERTENCIA: No se encontró {PATH_MACHOTE}. Se generará uno vacío.")
        wb = openpyxl.Workbook()
        ws = wb.active
        # Basic headers just in case
        for i, header in enumerate(['CANTIDAD', 'UNIDAD', 'CLAVE SAT', 'DESCRIPCION', 'P. UNITARIO', 'SUBTOTAL', 'IVA', 'TOTAL']):
            ws.cell(row=7, column=i+2).value = header
    else:
        wb = openpyxl.load_workbook(PATH_MACHOTE)
        ws = wb.active
    
    for row in range(1, 10):
        cell_val = ws.cell(row=row, column=2).value
        if cell_val == 'EMPRESA':
            ws.cell(row=row, column=3).value = empresa
        elif cell_val == 'RFC':
            ws.cell(row=row, column=3).value = rfc
            
    fila_inicio = 8
    
    estilos_cols = {}
    for col in range(2, 11):
        cell = ws.cell(row=8, column=col)
        estilos_cols[col] = {
            'font': copy(cell.font),
            'border': copy(cell.border),
            'fill': copy(cell.fill),
            'number_format': cell.number_format,
            'alignment': copy(cell.alignment)
        }
        
    for r in range(8, ws.max_row + 1):
        for c in range(1, ws.max_column + 1):
            ws.cell(row=r, column=c).value = None
            
    for idx, row in df_seleccion.iterrows():
        ws.cell(row=fila_inicio, column=2).value = row['CANTIDAD']
        ws.cell(row=fila_inicio, column=3).value = "PIEZA"
        ws.cell(row=fila_inicio, column=4).value = row['CLAVE SAT']
        ws.cell(row=fila_inicio, column=5).value = row['DESCRIPCION']
        ws.cell(row=fila_inicio, column=6).value = row['P. UNITARIO']
        ws.cell(row=fila_inicio, column=7).value = row['SUBTOTAL']
        ws.cell(row=fila_inicio, column=8).value = row['IVA']
        ws.cell(row=fila_inicio, column=9).value = row['TOTAL']
        
        for col in range(2, 11):
            cell = ws.cell(row=fila_inicio, column=col)
            estilo = estilos_cols.get(col)
            if estilo:
                cell.font = copy(estilo['font'])
                cell.border = copy(estilo['border'])
                cell.fill = copy(estilo['fill'])
                cell.number_format = estilo['number_format']
                cell.alignment = copy(estilo['alignment'])
        fila_inicio += 1
        
    fila_inicio += 1
    
    ws.cell(row=fila_inicio, column=5).value = "TOTALES"
    ws.cell(row=fila_inicio, column=5).font = Font(bold=True)
    ws.cell(row=fila_inicio, column=6).value = df_seleccion['P. UNITARIO'].sum()
    ws.cell(row=fila_inicio, column=7).value = df_seleccion['SUBTOTAL'].sum()
    ws.cell(row=fila_inicio, column=8).value = df_seleccion['IVA'].sum()
    ws.cell(row=fila_inicio, column=9).value = df_seleccion['TOTAL'].sum()
    
    for col in range(6, 10):
        cell = ws.cell(row=fila_inicio, column=col)
        cell.number_format = estilos_cols[col]['number_format'] if col in estilos_cols else '0.00'
        cell.font = Font(bold=True)
        cell.border = copy(estilos_cols[col]['border']) if col in estilos_cols else None
        
    wb.save(ruta_salida)
    return ruta_salida, nombre_archivo


def _guardar_warnings_pdf(ruta_pdf, warnings):
    if not warnings:
        return
    os.makedirs(APP_DATA_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PDF_WARNINGS_LOG, "a", encoding="utf-8") as fh:
        fh.write(f"\n[{timestamp}] {ruta_pdf}\n")
        for warning in warnings:
            fh.write(f"- {warning}\n")


def extraer_nuevos_articulos(ruta_pdf, with_report=False):
    import pdfplumber
    import re
    import os
    
    match = re.search(r"reporte-productos (.+)\.pdf", os.path.basename(ruta_pdf), re.IGNORECASE)
    sucursal = match.group(1).strip() if match else "ALMACEN"
    
    articulos_encontrados = []
    warnings = []
    bloques_detectados = 0
    
    with pdfplumber.open(ruta_pdf) as pdf:
        text = ""
        for p in pdf.pages:
            page_text = p.extract_text(layout=True) or ""
            if not page_text.strip():
                warnings.append(f"Página {p.page_number} sin texto extraíble.")
            text += page_text + "\n"
            
    lineas = text.split("\n")
    modelo_actual = ""
    color_actual = ""
    
    for i in range(len(lineas)):
        linea = lineas[i].strip()
        if not linea or "Nombre" in linea or "Total de productos" in linea:
            continue
            
        match_bloque = re.match(r"^(.+?)\s+(\d+)\s+\(\d+\)\s+([A-Z0-9, ]+)\s+\$([\d,]+\.\d{2})", linea)
        
        if match_bloque:
            bloques_detectados += 1
            nombre_completo = match_bloque.group(1).strip()
            partes_nombre = nombre_completo.split(" ")
            
            if len(partes_nombre) > 1 and partes_nombre[-1].upper() in ['VERDE', 'ROJO', 'AZUL', 'ROSA', 'BLANCO', 'NEGRO', 'AMARILLO', 'CAFE', 'GRIS', 'CAYENNE', 'PURPURA', 'PÚRPURA']:
                modelo_actual = " ".join(partes_nombre[:-1])
                color_actual = partes_nombre[-1].upper()
            else:
                modelo_actual = nombre_completo
                color_actual = ""
                if i + 1 < len(lineas):
                    tokens = lineas[i + 1].strip().split()
                    if tokens:
                        siguiente = tokens[0]
                        if re.match(r"^[A-ZÚ]+", siguiente) and siguiente not in ["L1LTWT", "HWM7MTEZA", "LU5RMC"]:
                            color_actual = siguiente
                    else:
                        warnings.append(f"Línea {i + 2} vacía al intentar detectar color para '{nombre_completo}'.")
            
            series_str = match_bloque.group(3).strip()
            series = [s.strip() for s in series_str.split(',')]
            
            for s in series:
                if len(s) > 5:
                    articulos_encontrados.append({'SUCURSAL': sucursal, 'MODELO BASE': modelo_actual, 'COLOR': color_actual, 'No de SERIE:': s, 'CANTIDAD': 1})
            
            j = i + 1
            while j < len(lineas):
                lin_j = lineas[j].strip()
                match_series_extra = re.findall(r"([A-Z0-9]{10,25})(?:,|$)", lin_j)
                if match_series_extra:
                    for s in match_series_extra:
                        if len(s) > 5 and s not in [a['No de SERIE:'] for a in articulos_encontrados]:
                            articulos_encontrados.append({'SUCURSAL': sucursal, 'MODELO BASE': modelo_actual, 'COLOR': color_actual, 'No de SERIE:': s, 'CANTIDAD': 1})
                if "$" in lin_j or re.match(r"^(.+?)\s+(\d+)\s+\(\d+\)", lin_j):
                    break
                j += 1

    _guardar_warnings_pdf(ruta_pdf, warnings)
    report = {
        "lineas_analizadas": len(lineas),
        "bloques_detectados": bloques_detectados,
        "articulos_detectados": len(articulos_encontrados),
        "warnings": len(warnings),
        "warnings_log": PDF_WARNINGS_LOG,
    }
    if with_report:
        return articulos_encontrados, warnings, report
    return articulos_encontrados


def cargar_inventario(ruta_pdf, path_inventario, lista_articulos=None):
    import openpyxl
    from openpyxl.styles import Font
    from copy import copy
    import pandas as pd
    
    print(f"Leyendo PDF de carga: {ruta_pdf}")
    if lista_articulos is not None:
        nuevos = lista_articulos
    else:
        nuevos = extraer_nuevos_articulos(ruta_pdf)
    print(f"Se encontraron {len(nuevos)} articulos en el PDF.")
    
    # Cargar lista de precios
    _, _, _, df_precios = load_data()
    df_precios_dict = df_precios.drop_duplicates(subset=['MODELO'], keep='last').set_index('MODELO').to_dict('index')
    
    wb = openpyxl.load_workbook(path_inventario)
    ws_reporte = wb['REPORTE']
    
    existentes = set()
    for sheet_name in ['REPORTE', 'USADOS', 'XML_ENCONTRADOS']:
        if sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            col_serie = 6
            for c in range(1, 20):
                if ws.cell(row=4, column=c).value == 'No de SERIE:':
                    col_serie = c
                    break
            for r in range(5, ws.max_row + 1):
                val = ws.cell(row=r, column=col_serie).value
                if val: existentes.add(str(val).strip())
                
    a_insertar = []
    for art in nuevos:
        if art['No de SERIE:'] in existentes:
            print(f"ALERTA: Serie duplicada ignorada -> {art['No de SERIE:']}")
            continue
            
        # Calcular precios y descripciones cruzando con el catálogo
        modelo_busqueda = aplicar_mapeo(art['MODELO BASE'])
        
        d1_val = None
        clave_sat = None
        desc_base = ""
        
        if modelo_busqueda in df_precios_dict:
            datos_precio = df_precios_dict[modelo_busqueda]
            try:
                d1_val = float(datos_precio['D1'])
            except:
                d1_val = None
            clave_sat = str(datos_precio['CLAVE SAT'])
            desc_base = str(datos_precio['DESCRIPCION']).strip()
            
        color = art['COLOR'].strip()
        serie = art['No de SERIE:'].strip()
        
        if color:
            desc_final = f"{desc_base} {modelo_busqueda} {color} NO DE SERIE:{serie}"
        else:
            desc_final = f"{desc_base} {modelo_busqueda} NO DE SERIE:{serie}"
            
        art['D1'] = d1_val
        art['CLAVE SAT'] = clave_sat
        art['DESCRIPCION'] = desc_final.upper()
        
        if pd.notna(d1_val):
            art['P. UNITARIO'] = d1_val / 1.16
            art['SUBTOTAL'] = art['P. UNITARIO'] * 1 # Cantidad 1
            art['IVA'] = art['SUBTOTAL'] * 0.16
            art['TOTAL'] = art['SUBTOTAL'] + art['IVA']
        else:
            art['P. UNITARIO'] = None
            art['SUBTOTAL'] = None
            art['IVA'] = None
            art['TOTAL'] = None
            print(f"ADVERTENCIA: Modelo {modelo_busqueda} no tiene precio D1 en catálogo. Se cargará sin precio.")
            
        a_insertar.append(art)
            
    if not a_insertar:
        print("No hay articulos nuevos validos para insertar.")
        return
        
    print(f"Insertando {len(a_insertar)} articulos nuevos...")
    # 1. Update SQLite
    db_manager.insert_new_items(a_insertar)
    
    # 2. Update Excel
    fila_inicio = ws_reporte.max_row + 1
    
    for art in a_insertar:
        ws_reporte.cell(row=fila_inicio, column=1).value = art['SUCURSAL']
        ws_reporte.cell(row=fila_inicio, column=2).value = art['MODELO BASE'] 
        ws_reporte.cell(row=fila_inicio, column=3).value = art['MODELO BASE']
        ws_reporte.cell(row=fila_inicio, column=4).value = art['COLOR']
        ws_reporte.cell(row=fila_inicio, column=5).value = 1
        ws_reporte.cell(row=fila_inicio, column=6).value = art['No de SERIE:']
        
        # Columnas de precio
        ws_reporte.cell(row=fila_inicio, column=7).value = art['D1']
        ws_reporte.cell(row=fila_inicio, column=8).value = art['P. UNITARIO']
        ws_reporte.cell(row=fila_inicio, column=9).value = art['SUBTOTAL']
        ws_reporte.cell(row=fila_inicio, column=10).value = art['IVA']
        ws_reporte.cell(row=fila_inicio, column=11).value = art['TOTAL']
        ws_reporte.cell(row=fila_inicio, column=12).value = art['CLAVE SAT']
        ws_reporte.cell(row=fila_inicio, column=13).value = art['DESCRIPCION']
        
        for c in range(1, 15):
            origen = ws_reporte.cell(row=5, column=c)
            destino = ws_reporte.cell(row=fila_inicio, column=c)
            destino.font = copy(origen.font)
            destino.border = copy(origen.border)
            destino.fill = copy(origen.fill)
            destino.number_format = origen.number_format
            destino.alignment = copy(origen.alignment)
            
        fila_inicio += 1
        
    max_row = ws_reporte.max_row
    ws_reporte.cell(row=2, column=2).value = f"=SUM(E5:E{max_row})"
    ws_reporte.cell(row=2, column=5).value = f"=SUM(I5:I{max_row})"
    ws_reporte.cell(row=2, column=8).value = f"=SUM(J5:J{max_row})"
    ws_reporte.cell(row=2, column=11).value = f"=SUM(K5:K{max_row})"
    
    path_salida = path_inventario.replace(".xlsx", "_CARGADO.xlsx")
    wb.save(path_salida)
    print(f"Inventario actualizado guardado en {path_salida}")

def procesar_xmls(xml_dir):
    import glob
    import xml.etree.ElementTree as ET
    
    archivos_xml = glob.glob(os.path.join(xml_dir, "*.xml"))
    if not archivos_xml:
        print(f"No se encontraron archivos XML en la carpeta {xml_dir}")
        return {}
        
    series_uuid = {}
    
    for archivo in archivos_xml:
        try:
            tree = ET.parse(archivo)
            root = tree.getroot()
            
            # Buscar el UUID (Esta en el Complemento TimbreFiscalDigital)
            uuid = None
            for elem in root.iter():
                # El tag suele ser {http://www.sat.gob.mx/TimbreFiscalDigital}TimbreFiscalDigital
                if 'UUID' in elem.attrib:
                    uuid = elem.attrib['UUID']
                    break
                    
            if not uuid:
                # Si el namespace es complejo, busqueda por expresion regular pura al archivo de texto
                with open(archivo, 'r', encoding='utf-8', errors='ignore') as f_xml:
                    contenido_xml = f_xml.read()
                    match_uuid = re.search(r'UUID="([a-fA-F0-9\-]+)"', contenido_xml)
                    if match_uuid:
                        uuid = match_uuid.group(1)
            
            if not uuid:
                print(f"No se encontró UUID en el archivo {archivo}")
                continue
                
            # Extraer todas las series del XML (Buscamos la palabra NO DE SERIE: o similar)
            # Analizando por expresion regular el contenido del archivo suele ser mas seguro y robusto en CFDI
            with open(archivo, 'r', encoding='utf-8', errors='ignore') as f_xml:
                contenido_xml = f_xml.read()
                
                # Buscar "NO DE SERIE:XXXXXX"
                matches_series = re.findall(r'NO DE SERIE:([A-Z0-9]+)', contenido_xml.upper())
                
                if matches_series:
                    for s in matches_series:
                        series_uuid[s.strip()] = uuid
                        
        except Exception as e:
            print(f"Error procesando el archivo XML {archivo}: {e}")
            
    print(f"Se encontraron {len(series_uuid)} series a buscar en los XMLs proporcionados.")
    return series_uuid
    
def actualizar_inventario_uuid(xml_dir, path_inventario):
    import openpyxl
    from openpyxl.styles import Font
    from copy import copy
    
    series_a_buscar = procesar_xmls(xml_dir)
    if not series_a_buscar:
        print("No hay UUIDs/series para actualizar.")
        return
        
    print("Actualizando Inventario con UUIDs...")
    db_manager.mark_items_as_xml(series_a_buscar)

    wb = openpyxl.load_workbook(path_inventario)
    
    if 'XML_ENCONTRADOS' not in wb.sheetnames:
        print("Error: No existe la pestaña XML_ENCONTRADOS en el inventario.")
        return
        
    ws_xml = wb['XML_ENCONTRADOS']
    
    fila_xml = ws_xml.max_row + 1
    for r in range(ws_xml.max_row, 4, -1):
        if ws_xml.cell(row=r, column=1).value is not None or ws_xml.cell(row=r, column=2).value is not None:
            fila_xml = r + 1
            break
    else:
        fila_xml = 5
        
    encontrados_total = 0
    
    for nombre_hoja in ['USADOS', 'REPORTE']:
        if nombre_hoja not in wb.sheetnames: continue
        ws = wb[nombre_hoja]
        
        col_serie = 6
        for c in range(1, 20):
            if ws.cell(row=4, column=c).value == 'No de SERIE:':
                col_serie = c
                break
                
        col_uuid_dest = 14
        for c in range(1, 20):
            if ws_xml.cell(row=4, column=c).value == 'UUID':
                col_uuid_dest = c
                break
                
        filas_a_borrar = []
        
        for r in range(5, ws.max_row + 1):
            serie_val = ws.cell(row=r, column=col_serie).value
            if serie_val:
                serie_val = str(serie_val).strip()
                if serie_val in series_a_buscar:
                    uuid_val = series_a_buscar[serie_val]
                    
                    c_origen_idx = 1
                    c_destino_idx = 1
                    
                    while c_origen_idx <= ws.max_column + 2 and c_destino_idx <= 20:
                        cabecera_origen = ws.cell(row=4, column=c_origen_idx).value
                        if cabecera_origen == 'MACHOTE':
                            c_origen_idx += 1
                            continue
                            
                        if c_destino_idx == col_uuid_dest:
                            ws_xml.cell(row=fila_xml, column=col_uuid_dest).value = uuid_val
                            ws_xml.cell(row=fila_xml, column=col_uuid_dest).font = Font(bold=True)
                            c_destino_idx += 1
                            if cabecera_origen == 'UUID': c_origen_idx += 1
                            continue
                            ws_xml.cell(row=fila_xml, column=c_destino_idx).value = uuid_val
                            ws_xml.cell(row=fila_xml, column=c_destino_idx).font = Font(bold=True)
                            c_destino_idx += 1
                            continue
                            
                        origen = ws.cell(row=r, column=c_origen_idx)
                        destino = ws_xml.cell(row=fila_xml, column=c_destino_idx)
                        destino.value = origen.value
                        destino.font = copy(origen.font)
                        destino.border = copy(origen.border)
                        destino.fill = copy(origen.fill)
                        destino.number_format = origen.number_format
                        destino.alignment = copy(origen.alignment)
                            
                        c_origen_idx += 1
                        c_destino_idx += 1
                        
                    del series_a_buscar[serie_val]
                    encontrados_total += 1
                    fila_xml += 1
                    filas_a_borrar.append(r)
                    
        for r in reversed(filas_a_borrar):
            ws.delete_rows(r, 1)
            
    print(f"Se movieron exitosamente {encontrados_total} articulos a XML_ENCONTRADOS.")
    
    if series_a_buscar:
        print(f"Ignoradas {len(series_a_buscar)} series (no encontradas en USADOS ni en REPORTE).")
        
    for ws in [wb['REPORTE'], wb['USADOS'], ws_xml]:
        ultima_fila = ws.max_row
        rango_fin = ultima_fila if ultima_fila >= 5 else 5
        ws.cell(row=2, column=2).value = f"=SUM(E5:E{rango_fin})"
        ws.cell(row=2, column=5).value = f"=SUM(I5:I{rango_fin})"
        ws.cell(row=2, column=8).value = f"=SUM(J5:J{rango_fin})"
        ws.cell(row=2, column=11).value = f"=SUM(K5:K{rango_fin})"
        
    path_salida = path_inventario.replace(".xlsx", "_UUID_ACTUALIZADO.xlsx")
    wb.save(path_salida)
    print(f"Inventario actualizado con UUIDs guardado en {path_salida}")


def actualizar_inventario_base(df_seleccion, nombre_machote):
    print("Actualizando Inventario...")
    series_usadas = df_seleccion['No de SERIE:'].tolist()

    # 1. Update SQLite fast
    db_manager.mark_items_as_used(series_usadas, nombre_machote)

    # 2. Update Excel keeping format (this is slow but needed for backwards compatibility)
    wb_inv = openpyxl.load_workbook(PATH_INVENTARIO)
    ws_reporte = wb_inv['REPORTE']
    ws_usados = wb_inv['USADOS']
    
    col_serie = 6
    for c in range(1, 20):
        if ws_reporte.cell(row=4, column=c).value == 'No de SERIE:':
            col_serie = c
            break
            
    fila_usados = ws_usados.max_row + 1
    for r in range(ws_usados.max_row, 4, -1):
        if ws_usados.cell(row=r, column=1).value is not None or ws_usados.cell(row=r, column=2).value is not None:
            fila_usados = r + 1
            break
    else:
        fila_usados = 5
        
    filas_a_borrar = []
    
    for r in range(5, ws_reporte.max_row + 1):
        serie_val = ws_reporte.cell(row=r, column=col_serie).value
        if serie_val in series_usadas:
            for c in range(1, ws_reporte.max_column + 1):
                origen = ws_reporte.cell(row=r, column=c)
                destino = ws_usados.cell(row=fila_usados, column=c)
                destino.value = origen.value
                if origen.font: destino.font = copy(origen.font)
                if origen.border: destino.border = copy(origen.border)
                if origen.fill: destino.fill = copy(origen.fill)
                if origen.number_format: destino.number_format = origen.number_format
                if origen.alignment: destino.alignment = copy(origen.alignment)
            
            # Asignar MACHOTE en col 14
            ws_usados.cell(row=fila_usados, column=14).value = nombre_machote
            ws_usados.cell(row=fila_usados, column=14).font = Font(bold=True)
            
            fila_usados += 1
            filas_a_borrar.append(r)
            
    for r in reversed(filas_a_borrar):
        ws_reporte.delete_rows(r, 1)
        
    # --- RECALCULAR TOTALES DE LA FILA 2 PARA TODAS LAS PESTAÑAS ---
    ws_xml = wb_inv['XML_ENCONTRADOS'] if 'XML_ENCONTRADOS' in wb_inv.sheetnames else None
    
    hojas_a_recalcular = [ws_reporte, ws_usados]
    if ws_xml:
        hojas_a_recalcular.append(ws_xml)
        
    for ws in hojas_a_recalcular:
        ultima_fila = ws.max_row
        rango_fin = ultima_fila if ultima_fila >= 5 else 5
        
        ws.cell(row=2, column=2).value = f"=SUM(E5:E{rango_fin})"
        ws.cell(row=2, column=5).value = f"=SUM(I5:I{rango_fin})"
        ws.cell(row=2, column=8).value = f"=SUM(J5:J{rango_fin})"
        ws.cell(row=2, column=11).value = f"=SUM(K5:K{rango_fin})"
    
    nuevo_inventario_path = PATH_INVENTARIO.replace(".xlsx", "_NUEVO.xlsx")
    wb_inv.save(nuevo_inventario_path)
    return nuevo_inventario_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--monto", type=float, required=False)
    parser.add_argument("--empresa", type=str, default="MOVILIDAD ELECTRICA DE JALISCO")
    parser.add_argument("--rfc", type=str, default="MEJ123456789")
    parser.add_argument("--cuenta", type=str, default="MP")
    parser.add_argument("--cargar", type=str, help="Ruta de un PDF de reporte de productos para ingresar al inventario")
    parser.add_argument("--xml_dir", type=str, help="Carpeta que contiene los archivos XML para validar UUIDs")
    args = parser.parse_args()
    
    if args.xml_dir:
        print(f"Modo Validacion XML activado para carpeta: {args.xml_dir}")
        actualizar_inventario_uuid(args.xml_dir, PATH_INVENTARIO)
        sys.exit(0)

    
    if args.cargar:
        print(f"Modo Carga activado para: {args.cargar}")
        cargar_inventario(args.cargar, PATH_INVENTARIO)
        sys.exit(0)

    # Intentar extraer datos del PDF de la Constancia de Situación Fiscal
    rfc_pdf, empresa_pdf = extraer_datos_empresa(args.empresa)
    
    rfc_final = rfc_pdf if rfc_pdf else args.rfc
    empresa_final = empresa_pdf if empresa_pdf else args.empresa
    
    print(f"Datos a utilizar para Machote -> Empresa: '{empresa_final}' | RFC: '{rfc_final}'")

    df_reporte, df_usados, df_xml, df_precios = load_data()
    df_disponibles = procesar_inventario(df_reporte, df_precios)
    df_seleccion = seleccionar_articulos(df_disponibles, args.monto)
    ruta_machote, nombre_machote = generar_machote(df_seleccion, args.monto, empresa_final, rfc_final, args.cuenta)
    
    actualizar_inventario_base(df_seleccion, nombre_machote)
    
if __name__ == '__main__':
    main()


def _replace_inventory_file(nuevo_path, path_inventario=PATH_INVENTARIO):
    shutil = __import__("shutil")
    if not os.path.exists(nuevo_path):
        raise FileNotFoundError(f"No se encontró el archivo actualizado: {nuevo_path}")
    shutil.move(nuevo_path, path_inventario)
    return path_inventario


def generar_machote_y_actualizar(df_seleccion, monto_objetivo, empresa, rfc, cuenta_mp):
    ruta_machote, nombre_machote = generar_machote(df_seleccion, monto_objetivo, empresa, rfc, cuenta_mp)
    nuevo_inventario_path = actualizar_inventario_base(df_seleccion, nombre_machote)
    inventario_final = _replace_inventory_file(nuevo_inventario_path, PATH_INVENTARIO)
    return ruta_machote, nombre_machote, inventario_final


def cargar_inventario_y_reemplazar(ruta_pdf, path_inventario=PATH_INVENTARIO, lista_articulos=None):
    cargar_inventario(ruta_pdf, path_inventario, lista_articulos=lista_articulos)
    path_salida = path_inventario.replace(".xlsx", "_CARGADO.xlsx")
    return _replace_inventory_file(path_salida, path_inventario)


def validar_xml_y_reemplazar(xml_dir, path_inventario=PATH_INVENTARIO):
    actualizar_inventario_uuid(xml_dir, path_inventario)
    path_salida = path_inventario.replace(".xlsx", "_UUID_ACTUALIZADO.xlsx")
    return _replace_inventory_file(path_salida, path_inventario)
