"""
Genera icon.ico para la aplicación ERP Restaurant.
Requiere: pip install Pillow
Ejecutar: python scripts/crear_icono.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def crear_icono():
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        import subprocess
        print("Instalando Pillow...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
        from PIL import Image, ImageDraw

    # Colores: verde azulado oscuro (estilo ERP Raul Castaño)
    DARK_TEAL = (27, 94, 90)   # #1B5E5A
    WHITE = (255, 255, 255)

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fondo circular verde
    margin = size // 16
    draw.ellipse([margin, margin, size - margin, size - margin], fill=DARK_TEAL, outline=WHITE, width=2)

    # Símbolo: tenedor y cuchillo simplificado
    cx, cy = size // 2, size // 2
    w, h = size // 8, size // 4

    # Tenedor (izquierda)
    fx = cx - size // 5
    draw.rectangle([fx - w//2, cy - h, fx + w//2, cy + h], fill=WHITE)
    for i in range(-1, 2):
        draw.rectangle([fx - w, cy - h + i*(h//3) - 4, fx - w//2, cy - h + i*(h//3) + 4], fill=WHITE)

    # Cuchillo (derecha)
    kx = cx + size // 5
    draw.rectangle([kx - w//2, cy - h, kx + w//2, cy + h], fill=WHITE)
    draw.polygon([(kx + w//2, cy - h), (kx + w, cy), (kx + w//2, cy + h)], fill=WHITE)

    out_path = PROJECT_ROOT / "icon.ico"
    img.save(out_path, format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print(f"Icono creado: {out_path}")
    return out_path


if __name__ == "__main__":
    crear_icono()
