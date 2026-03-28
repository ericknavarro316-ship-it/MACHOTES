import os
from collections import Counter
from PIL import Image

def get_dominant_colors(image_path, num_colors=2):
    """
    Extrae los colores dominantes de una imagen ignorando el blanco, negro puro, grises y transparencias.
    Devuelve una lista de tuplas RGB y su formato Hexadecimal.
    """
    try:
        # Abrir la imagen y convertirla a RGBA para procesar transparencias
        img = Image.open(image_path)
        img = img.convert('RGBA')

        # Redimensionar para hacer el proceso más rápido
        img.thumbnail((150, 150))

        pixels = list(img.getdata())

        valid_pixels = []
        for r, g, b, a in pixels:
            # Ignorar pixeles transparentes (Alpha < 200)
            if a < 200:
                continue

            # Ignorar blancos o casi blancos (R, G, B muy altos)
            if r > 240 and g > 240 and b > 240:
                continue

            # Ignorar negros puros o grises muy oscuros (R, G, B muy bajos)
            if r < 30 and g < 30 and b < 30:
                continue

            # Ignorar grises (donde r, g y b son casi iguales)
            if max(r, g, b) - min(r, g, b) < 15:
                continue

            # Agrupar colores similares redondeando a multiplos de 10
            # Esto ayuda a que tonos muy similares cuenten como el mismo color
            valid_pixels.append((r // 10 * 10, g // 10 * 10, b // 10 * 10))

        if not valid_pixels:
            return None

        # Contar los colores más comunes
        counts = Counter(valid_pixels)
        most_common = counts.most_common(num_colors)

        colors_hex = []
        for (r, g, b), count in most_common:
            hex_color = "#{:02x}{:02x}{:02x}".format(r, g, b).upper()
            colors_hex.append(hex_color)

        # Si solo encontró 1 color, devolverlo dos veces
        while len(colors_hex) < num_colors:
            colors_hex.append(colors_hex[0] if colors_hex else "#3498DB")

        return colors_hex

    except Exception as e:
        print(f"Error procesando imagen para colores: {e}")
        return None
