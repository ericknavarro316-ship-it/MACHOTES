# MACHOTES OF TIME

Panel administrativo de escritorio para generar machotes, controlar inventario, cargar mercancía desde PDF, validar XMLs y consultar un historial operativo.

## Módulos principales
- Dashboard analítico con KPIs y distribución por sucursal.
- Inventario con pestañas para disponibles, usados y facturados.
- Generador inteligente de machotes con vista previa.
- Carga de mercancía desde PDF.
- Validación de XML y conciliación de UUIDs.
- Historial local de acciones y ajustes persistentes.

## Estilo visual
La aplicación usa una interfaz inspirada en **The Legend of Zelda: Ocarina of Time**, con tonos bosque, dorados y paneles tipo santuario.

## Ejecutar
```bash
cd Mis_Machotes
python start_app.py
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
