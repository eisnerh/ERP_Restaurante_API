"""
Rellena campos vacios del Excel de inventario con datos de prueba.
Crea items con stock bajo (existencia < 10% stock) para visualizar alertas.

Uso: python scripts/fill_inventory_excel_test_data.py
"""
import os
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EXCEL_PATH = PROJECT_ROOT / "excel_docs" / "DATOS INVENTARIO.xlsx"
BACKUP_PATH = PROJECT_ROOT / "excel_docs" / "DATOS INVENTARIO.backup.xlsx"


def main():
    try:
        import openpyxl
    except ImportError:
        print("Instala openpyxl: pip install openpyxl")
        return 1

    if not EXCEL_PATH.exists():
        print(f"Archivo no encontrado: {EXCEL_PATH}")
        return 1

    wb = openpyxl.load_workbook(EXCEL_PATH)
    ws = wb["INVENTARIO"] if "INVENTARIO" in wb.sheetnames else wb.active

    # Backup
    wb.save(BACKUP_PATH)
    print(f"Respaldo guardado en: {BACKUP_PATH}")

    dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado"]
    telefonos = ["2222-3333", "8888-9999", "7777-1234", "5555-6789", "3333-4444"]

    filled_pedido = filled_tel = filled_dia = set_low_stock = 0

    for row_idx in range(4, ws.max_row + 1):
        row = list(ws[row_idx])
        if len(row) < 12:
            continue

        product = row[1].value if row[1].value else ""
        if not str(product).strip():
            continue

        # Pedido (col 6, index 5)
        if row[5].value is None or str(row[5].value).strip() == "":
            stock_val = row[4].value
            try:
                stock = float(stock_val) if stock_val else 10
            except (ValueError, TypeError):
                stock = 10
            row[5].value = max(1, int(stock * 0.5))  # Pedido sugerido = 50% del stock
            filled_pedido += 1

        # Teléfono (col 10, index 9)
        if row[9].value is None or str(row[9].value).strip() == "":
            row[9].value = random.choice(telefonos)
            filled_tel += 1

        # Día Visita (col 11, index 10)
        if row[10].value is None or str(row[10].value).strip() == "":
            row[10].value = random.choice(dias)
            filled_dia += 1

        # Para alertas: asegurar que ~30 items tengan stock bajo (existencia < 10% stock)
        # Solo en las primeras 80 filas, modificar 1 de cada 3 para tener stock bajo
        if row_idx <= 90 and (row_idx - 4) % 3 == 0:
            try:
                ex = float(row[3].value) if row[3].value is not None else 0
                st = float(row[4].value) if row[4].value is not None else 0
                if st <= 0 or ex >= 0.1 * st:
                    # Poner stock=50, existencia=3 (6% -> alerta)
                    row[4].value = 50
                    row[3].value = 3
                    row[5].value = 25  # pedido sugerido
                    set_low_stock += 1
            except (ValueError, TypeError):
                pass

    wb.save(EXCEL_PATH)
    wb.close()

    print(f"Pedido: {filled_pedido} campos rellenados")
    print(f"Telefono: {filled_tel} campos rellenados")
    print(f"Dia Visita: {filled_dia} campos rellenados")
    print(f"Items con stock bajo (para alertas): {set_low_stock} modificados")
    print(f"\nArchivo actualizado: {EXCEL_PATH}")
    print("Importa con: python scripts/import_inventory_excel.py --franchisee-id 1 --replace")
    return 0


if __name__ == "__main__":
    exit(main())
