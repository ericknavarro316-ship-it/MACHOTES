import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APP_DATA_DIR = BASE_DIR / "app_data"
PDF_WARNINGS_LOG = APP_DATA_DIR / "pdf_parse_warnings.log"

PATH_INVENTARIO = os.path.join(BASE_DIR, "machotes", "Inventario_Final.xlsx")
PATH_MACHOTE = os.path.join(BASE_DIR, "machotes", "EJEMPLO MACHOTE.xlsx")
PATH_PRECIOS = os.path.join(BASE_DIR, "machotes", "Lista de precios ok.xlsx")
OUTPUT_DIR = os.path.join(BASE_DIR, "machotes_generados")

MAPEOS_MODELOS = {
    "S2 AIR V2": "S2",
    "HN-C80": "HN-C80 PRO",
    "M2MAX": "M2MAX 8.5",
    "M2MAXB": "M2MAXB10"
}
COLORES_VALIDOS = {
    "VERDE", "ROJO", "AZUL", "ROSA", "BLANCO", "NEGRO",
    "AMARILLO", "CAFE", "GRIS", "CAYENNE", "PURPURA", "PÚRPURA",
    "NARANJA", "GRIS XUAN", "GRIS/XUAN", "DORADO"
}
