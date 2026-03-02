"""
Genera plantillas Excel con el formato correcto para importar datos a las tablas del ERP.

Ejecutar desde la raíz del proyecto:
  python scripts/generar_plantillas_excel.py

Genera archivos en: excel_docs/plantillas/
También disponible desde Configuración → Descargar plantillas Excel (ZIP).
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

OUTPUT_DIR = os.path.join(PROJECT_ROOT, "excel_docs", "plantillas")


def main():
    try:
        from utils.excel_templates import TEMPLATES
    except ImportError:
        print("Instala openpyxl: pip install openpyxl")
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("Generando plantillas Excel...\n")
    print(f"Plantillas en: {OUTPUT_DIR}")
    for filename, gen_fn in TEMPLATES:
        wb = gen_fn()
        path = os.path.join(OUTPUT_DIR, filename)
        wb.save(path)
        print(f"  [OK] {filename}")
    print("\nListo. Consulta FORMATOS_EXCEL.md para más detalles.")


if __name__ == "__main__":
    main()
