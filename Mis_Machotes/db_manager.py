import sqlite3
import pandas as pd
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "app_data", "inventory.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estado TEXT NOT NULL,
        sucursal TEXT,
        modelo TEXT,
        modelo_base TEXT,
        color TEXT,
        cantidad INTEGER,
        no_serie TEXT UNIQUE,
        d1 REAL,
        p_unitario REAL,
        subtotal REAL,
        iva REAL,
        total REAL,
        clave_sat TEXT,
        descripcion TEXT,
        machote TEXT,
        uuid TEXT,
        fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_estado ON inventario(estado)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sucursal ON inventario(sucursal)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_modelo_base ON inventario(modelo_base)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_no_serie ON inventario(no_serie)')

    conn.commit()
    conn.close()

def migrate_excel_to_sqlite(path_inventario):
    print("Iniciando migración de Excel a SQLite...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()

    try:
        df_reporte = pd.read_excel(path_inventario, sheet_name='REPORTE', header=3)
        df_usados = pd.read_excel(path_inventario, sheet_name='USADOS', header=3)
        try:
            df_xml = pd.read_excel(path_inventario, sheet_name='XML_ENCONTRADOS', header=3)
        except Exception:
            df_xml = pd.DataFrame()

        conn = get_connection()
        conn.execute("DELETE FROM inventario")

        col_mapping = {
            'SUCURSAL': 'sucursal',
            'MODELO': 'modelo',
            'MODELO BASE': 'modelo_base',
            'COLOR': 'color',
            'CANTIDAD': 'cantidad',
            'No de SERIE:': 'no_serie',
            'D1': 'd1',
            'P. UNITARIO': 'p_unitario',
            'SUBTOTAL': 'subtotal',
            'IVA': 'iva',
            'TOTAL': 'total',
            'CLAVE SAT': 'clave_sat',
            'DESCRIPCION': 'descripcion',
            'MACHOTE': 'machote',
            'UUID': 'uuid'
        }

        def prepare_df_for_sql(df, estado_val):
            if df.empty: return pd.DataFrame()

            # Keep only exact matches for columns
            df_clean = df.rename(columns=col_mapping)
            available_cols = [c for c in df_clean.columns if c in col_mapping.values()]
            df_clean = df_clean[available_cols].copy()

            if 'no_serie' in df_clean.columns:
                df_clean = df_clean.dropna(subset=['no_serie'])
                df_clean['no_serie'] = df_clean['no_serie'].astype(str).str.strip()
            else:
                return pd.DataFrame()

            df_clean['estado'] = estado_val
            return df_clean

        df_rep_sql = prepare_df_for_sql(df_reporte, 'DISPONIBLE')
        df_us_sql = prepare_df_for_sql(df_usados, 'USADO')
        df_xml_sql = prepare_df_for_sql(df_xml, 'XML')

        dfs_to_concat = [df for df in [df_rep_sql, df_us_sql, df_xml_sql] if not df.empty]
        if not dfs_to_concat:
            print("Migración abortada: DataFrames vacíos.")
            return False

        df_final = pd.concat(dfs_to_concat, ignore_index=True)

        if 'cantidad' in df_final.columns:
            df_final['cantidad'] = pd.to_numeric(df_final['cantidad'], errors='coerce').fillna(1)

        for col in ['d1', 'p_unitario', 'subtotal', 'iva', 'total']:
            if col in df_final.columns:
                df_final[col] = pd.to_numeric(df_final[col], errors='coerce')

        if not df_final.empty:
            df_final = df_final.drop_duplicates(subset=['no_serie'], keep='last')
            df_final.to_sql('inventario', conn, if_exists='append', index=False)

        conn.commit()
        conn.close()
        print(f"Migración completa. Se insertaron {len(df_final)} artículos en SQLite.")
        return True

    except Exception as e:
        print(f"Error en migración: {e}")
        return False

def is_db_initialized():
    if not os.path.exists(DB_PATH):
        return False

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='inventario'")
    if cursor.fetchone()[0] == 0:
        conn.close()
        return False

    cursor.execute("SELECT COUNT(*) FROM inventario")
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# --- Funciones para reemplazar pandas en machote_generator.py ---

def get_inventory_dataframes():
    """Devuelve los dataframes que espera dashboard_app.py pero desde SQLite (rápido)"""
    conn = get_connection()

    # Mapeo inverso de SQLite a Pandas (para compatibilidad de UI)
    reverse_mapping = {
        'sucursal': 'SUCURSAL',
        'modelo': 'MODELO',
        'modelo_base': 'MODELO BASE',
        'color': 'COLOR',
        'cantidad': 'CANTIDAD',
        'no_serie': 'No de SERIE:',
        'd1': 'D1',
        'p_unitario': 'P. UNITARIO',
        'subtotal': 'SUBTOTAL',
        'iva': 'IVA',
        'total': 'TOTAL',
        'clave_sat': 'CLAVE SAT',
        'descripcion': 'DESCRIPCION',
        'machote': 'MACHOTE',
        'uuid': 'UUID',
        'fecha_actualizacion': 'FECHA ACTUALIZACION',
    }

    try:
        df_rep = pd.read_sql_query("SELECT * FROM inventario WHERE estado='DISPONIBLE'", conn)
        df_us = pd.read_sql_query("SELECT * FROM inventario WHERE estado='USADO'", conn)
        df_xml = pd.read_sql_query("SELECT * FROM inventario WHERE estado='XML'", conn)
    except Exception as e:
        print(f"Error leyendo de SQLite: {e}")
        return None, None, None
    finally:
        conn.close()

    df_rep = df_rep.rename(columns=reverse_mapping)
    df_us = df_us.rename(columns=reverse_mapping)
    df_xml = df_xml.rename(columns=reverse_mapping)

    return df_rep, df_us, df_xml

def get_precios_dataframe(path_precios):
    """Mantiene la carga de precios desde Excel porque es pequeño y manejable"""
    try:
        df_precios = pd.read_excel(path_precios, sheet_name='Para imprimir', header=2)
        df_precios = df_precios[['CLAVE SAT', 'DESCRIPCION', 'MODELO', 'D1']]
        df_precios.dropna(subset=['MODELO'], inplace=True)
        df_precios['MODELO'] = df_precios['MODELO'].astype(str).str.strip().str.upper()
        df_precios['CLAVE SAT'] = df_precios['CLAVE SAT'].fillna(0).astype(int).astype(str)
        return df_precios
    except Exception as e:
        print(f"Error cargando archivo de precios: {e}")
        return pd.DataFrame()

def insert_new_items(articulos):
    """Inserta nuevos artículos en la base de datos"""
    if not articulos:
        return

    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    try:
        conn.execute("BEGIN TRANSACTION")
        for art in articulos:
            try:
                cursor.execute('''
                INSERT INTO inventario
                (estado, sucursal, modelo, modelo_base, color, cantidad, no_serie,
                 d1, p_unitario, subtotal, iva, total, clave_sat, descripcion)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    'DISPONIBLE',
                    art.get('SUCURSAL', ''),
                    art.get('MODELO BASE', ''), # modelo = modelo_base por defecto
                    art.get('MODELO BASE', ''),
                    art.get('COLOR', ''),
                    1,
                    str(art.get('No de SERIE:', '')).strip(),
                    art.get('D1', None),
                    art.get('P. UNITARIO', None),
                    art.get('SUBTOTAL', None),
                    art.get('IVA', None),
                    art.get('TOTAL', None),
                    art.get('CLAVE SAT', None),
                    art.get('DESCRIPCION', '')
                ))
                inserted += 1
            except sqlite3.IntegrityError:
                print(f"Serie duplicada ignorada: {art.get('No de SERIE:')}")
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error insertando articulos, haciendo rollback: {e}")
        raise
    finally:
        conn.close()

    print(f"Insertados {inserted} registros en SQLite.")

def mark_items_as_used(series_list, machote_name):
    """Mueve artículos de DISPONIBLE a USADO"""
    if not series_list:
        return

    conn = get_connection()
    cursor = conn.cursor()

    placeholders = ','.join('?' * len(series_list))
    query = f'''
    UPDATE inventario
    SET estado = 'USADO', machote = ?
    WHERE no_serie IN ({placeholders}) AND estado = 'DISPONIBLE'
    '''

    params = [machote_name] + list(series_list)

    try:
        conn.execute("BEGIN TRANSACTION")
        cursor.execute(query, params)
        updated = cursor.rowcount
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error marcando articulos como usados: {e}")
        raise
    finally:
        conn.close()

    return updated

def mark_items_as_xml(series_uuid_dict):
    """Mueve artículos a XML asignando su UUID"""
    if not series_uuid_dict:
        return

    conn = get_connection()
    cursor = conn.cursor()

    updated_total = 0
    try:
        conn.execute("BEGIN TRANSACTION")
        for serie, uuid in series_uuid_dict.items():
            cursor.execute('''
            UPDATE inventario
            SET estado = 'XML', uuid = ?
            WHERE no_serie = ? AND (estado = 'USADO' OR estado = 'DISPONIBLE')
            ''', (uuid, serie))
            updated_total += cursor.rowcount
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Error cruzando XMLs, haciendo rollback: {e}")
        raise
    finally:
        conn.close()

    return updated_total
