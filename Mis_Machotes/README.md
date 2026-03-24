# MACHOTES OF TIME

Panel administrativo de escritorio para generar machotes, controlar inventario, cargar mercancía desde PDF, validar XMLs y consultar un historial operativo.

## Módulos principales
- Dashboard analítico con KPIs y distribución por sucursal.
- Inventario con pestañas para disponibles, usados y facturados.
- Generador inteligente de machotes con vista previa.
- Carga de mercancía desde PDF.
- Validación de XML y conciliación de UUIDs.
- Historial local de acciones y ajustes persistentes.
- Carga PDF con modo simulación, limpieza rápida de selección y reporte post-carga.

## Resumen rápido (en palabras simples)
Si no te quedó claro el último cambio, esto es lo importante:

1. **Dashboard más útil:** ahora puedes ver datos por periodos rápidos (hoy, 7d, 30d, 90d), usar rango manual y comparar contra el periodo anterior.
2. **Exportación fácil:** botón **Exportar Dashboard** para sacar un Excel con KPIs y resumen por sucursal.
3. **Más espacio visual:** el menú lateral se puede colapsar para que el contenido principal se vea más grande.
4. **Carga de PDF más segura:** puedes simular importación, ver warnings y deshacer la última carga si algo salió mal.
5. **Empresa/RFC automático:** en Generador, la app puede leer datos desde PDFs CSF y autocompletar campos.

### Mini guía (30 segundos)
- Si quieres ver **solo lo reciente**, usa el selector de periodo en Dashboard (por ejemplo **7d**).
- Si quieres revisar un lapso exacto, elige **Rango**, define **Desde/Hasta** y pulsa **Aplicar**.
- Si te sirve compartir resultados, pulsa **Exportar Dashboard**.
- Si el menú te estorba, colápsalo con el botón de la barra lateral.

### Ajustes recientes del Dashboard
- KPI **Participación Rubro** = productos del rubro seleccionado / total global.
- KPI **Ticket Promedio** para monitorear valor unitario promedio visible.
- **Resumen por sucursal** ahora incluye porcentaje de participación por cantidad.
- Gráfico de sucursales muestra **Top 5 + Otros** para mantener lectura clara.
- Selector de periodo en dashboard: **Todo / Hoy / 7d / 30d / 90d / Rango**.
- Rango personalizado con fechas **Desde/Hasta** en formato `YYYY-MM-DD`.
- Al elegir **Hoy/7d/30d/90d**, la app prellena automáticamente los campos **Desde/Hasta** para mostrar el rango aplicado.
- Comparativo automático vs periodo anterior (variación de piezas y total).
- Botón **Exportar Dashboard** para guardar KPIs y resumen por sucursal en Excel.

### Sidebar dinámica (UI)
- El panel lateral ahora se puede colapsar/expandir con botón de icono (estilo Trifuerza/Sheikah).
- Al colapsar, se prioriza espacio para el contenido principal (se ocultan subtítulo y atajos, y quedan iconos de navegación).

## Estilo visual
La aplicación usa una interfaz inspirada en **The Legend of Zelda: Ocarina of Time**, con tonos bosque, dorados y paneles tipo santuario.

## Ejecutar
```bash
cd Mis_Machotes
python start_app.py
```

## Validar instalación (sin abrir ventana)
Si quieres revisar que todo está correcto antes de abrir la interfaz, ejecuta:

```bash
cd Mis_Machotes
python start_app.py --check-only
```

Este modo valida dependencias, archivos base y que `dashboard_app.py` tenga las secciones críticas.

## Respaldar base de datos (SQLite)
Puedes crear un respaldo rápido de `app_data/inventory.db` desde terminal:

```bash
cd Mis_Machotes
python start_app.py --backup-db
```

Para listar respaldos disponibles:

```bash
cd Mis_Machotes
python start_app.py --list-backups
```

Para restaurar uno específico:

```bash
cd Mis_Machotes
python start_app.py --restore-backup inventory_20260324_120000.db
```

Para restaurar automáticamente el respaldo más reciente:

```bash
cd Mis_Machotes
python start_app.py --restore-latest
```

Para conservar solo los últimos `N` respaldos y limpiar los demás:

```bash
cd Mis_Machotes
python start_app.py --prune-backups 20
```

## Descargar el proyecto actualizado
Si quieres generar un ZIP local con la versión actual del proyecto, desde la raíz del repositorio ejecuta:

```bash
python scripts/create_project_zip.py
```

Eso crea el archivo `Mis_Machotes_descarga.zip` en la raíz del repositorio. Después puedes compartir o subir ese ZIP manualmente donde lo necesites.

## Instalación rápida para Windows
Si no sabes programación, copia y pega estos comandos **uno por uno** en PowerShell dentro de la carpeta del proyecto:

```powershell
cd RUTA\A\MACHOTES\Mis_Machotes
python -m pip install -r requirements.txt
python start_app.py
```

Si no tienes Python instalado, primero descárgalo desde https://www.python.org/downloads/ y durante la instalación marca la opción **Add Python to PATH**.

> **Nota:** la primera vez que ejecutes `python -m pip install -r requirements.txt` puede tardar varios minutos, porque `pandas`, `matplotlib` y otras librerías pesan bastante. Es normal ver mucho texto mientras se instalan.

## Si quieres copiar y pegar solo los archivos importantes
Los archivos principales de la app son:
- `Mis_Machotes/dashboard_app.py`
- `Mis_Machotes/machote_generator.py`
- `requirements.txt`
- `README.md`

Pero lo recomendable es descargar o copiar **todo el proyecto completo**, porque la app también necesita los archivos Excel/PDF dentro de `Mis_Machotes/machotes/`. Si solo copiaste la carpeta `Mis_Machotes`, ahora también puedes instalar dependencias desde `Mis_Machotes/requirements.txt`.

## Si la app no abre
Si `dashboard_app.py` no abre, usa mejor este comando:

```bash
cd Mis_Machotes
python start_app.py
```

Ese archivo revisa primero si te faltan librerías y, si hace falta algo, te dice exactamente qué instalar antes de intentar abrir la ventana.

## Carga de PDF (nuevo flujo recomendado)
En la vista **Puerto Mercante** ahora tienes:
- Selección de **uno o varios PDFs** en una sola operación.
- **Limpiar selección**: borra el PDF cargado y limpia la tabla previa.
- **Simular importación**: te dice cuántos artículos seleccionados serían nuevos y cuántos parecen duplicados.
- **Ver warnings**: abre detalle de advertencias detectadas al parsear el PDF.
- **Reporte post-carga**: al importar, deja resumen en el log interno.
- **Deshacer última carga**: restaura el inventario previo a la importación más reciente.

Si el PDF trae muchos warnings (umbral por defecto: `3`), la app pide una confirmación extra antes de importar.
Ese umbral ahora se puede cambiar desde **Cámara del Sabio (Ajustes)** en el campo: **Umbral warnings (importación PDF)**.

Además, si el parser detecta rarezas del PDF (por ejemplo páginas sin texto), guarda advertencias en:
`Mis_Machotes/app_data/pdf_parse_warnings.log`.

## Filtros dinámicos (Inventario)
- Los filtros de **Sucursal** y **Modelo** están correlacionados: si eliges una sucursal, la lista de modelos se ajusta a los que sí existen para esa sucursal (y viceversa).
- Botón **X Filtros** limpia búsqueda y regresa ambos filtros a “todos”.
- En el dropdown de filtros ahora existe **Solo visibles** para seleccionar rápidamente solo lo que coincide con tu texto de búsqueda dentro del filtro.
- En el **Generador** se aplica la misma correlación entre **Sucursal** y **Modelo**, con botón **X Filtros** para restaurar ambos.
- En Inventario y Generador se muestra el indicador **Filtros activos: N** para saber de inmediato si estás viendo subconjuntos.

## Autocompletar empresa desde CSF (Generador)
- En **Forja del Machote** ahora aparece un desplegable **Elegir empresa CSF...**.
- Al seleccionar una opción, la app intenta autocompletar **Empresa** y **RFC** con los datos detectados en el PDF CSF correspondiente.
- Las opciones salen de los archivos `*CSF*.pdf` dentro de la carpeta `machotes/`.
- Botón **Recargar** actualiza el desplegable al instante si agregas nuevos CSF sin reiniciar la app.

## Si `python start_app.py` regresa directo a la consola
Eso significa que la app se cerró al arrancar. Con la versión nueva del lanzador ya debe mostrar el error completo en la misma terminal para que puedas copiarlo y pegarlo.

Si ves `Abriendo la aplicación...` y luego regresa al prompt sin abrir ventana, es probable que `dashboard_app.py` no se haya copiado completo. Vuelve a pegar ese archivo completo y prueba otra vez.
Si además **no** aparece el mensaje `La ejecución terminó sin error...`, entonces también necesitas reemplazar `Mis_Machotes/start_app.py` por la versión más nueva.

## Si pegaste `dashboard_app.py` por partes
1. Borra todo el contenido anterior de `Mis_Machotes/dashboard_app.py`.
2. Pega la parte 1.
3. Justo debajo, pega la parte 2.
4. Luego pega la parte 3.
5. Al final pega la parte 4.
6. Guarda el archivo.
7. Desde `Mis_Machotes`, ejecuta:

```powershell
python start_app.py
```

Si algo falla, copia el mensaje completo de la terminal.
