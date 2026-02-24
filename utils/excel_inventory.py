"""
Utilidades para leer el Excel DATOS INVENTARIO.xlsx.
Estructura: hoja "INVENTARIO", fila 3 cabecera, datos desde fila 4.
Columnas: ID, Producto, UM, Existencia, Stock, Pedido, Provedor, Proveedor 2, TIPO INVENTARIO, Teléfono, Día Visita, Responsable.
"""
import os
import re


def _to_float(val, default=None):
    """Convierte a float si es posible."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return default
    m = re.match(r"^([-+]?\d*\.?\d+)", s.replace(",", "."))
    return float(m.group(1)) if m else default


def _normalize_unit(val):
    """Normaliza unidad de medida a UND, KG, GR, CJ."""
    if not val:
        return "UND"
    s = str(val).strip().upper()
    mapping = {
        "KG": "KG", "KGS": "KG", "KILO": "KG", "KILOS": "KG", "KILOGRAMO": "KG", "KILOGRAMOS": "KG",
        "GR": "GR", "GRS": "GR", "GRAMO": "GR", "GRAMOS": "GR",
        "CJ": "CJ", "CAJA": "CJ", "CAJAS": "CJ", "CJAS": "CJ",
        "UND": "UND", "UN": "UND", "UNID": "UND", "UNIDAD": "UND", "UNIDADES": "UND", "U": "UND",
    }
    return mapping.get(s, "UND")


def parse_excel_inventory(path):
    """
    Lee la hoja "INVENTARIO" de DATOS INVENTARIO.xlsx.
    Retorna (items, error). items es lista de dicts; error es str o None.
    """
    try:
        import openpyxl
    except ImportError:
        return [], "Instala openpyxl: pip install openpyxl"

    if not os.path.isfile(path):
        return [], f"Archivo no encontrado: {path}"

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    items = []

    sheet_inv = None
    for name in wb.sheetnames:
        n = name.strip().upper()
        if n == "INVENTARIO" and "COCINA" not in n:
            sheet_inv = wb[name]
            break

    if sheet_inv:
        for row in sheet_inv.iter_rows(min_row=4, max_row=sheet_inv.max_row, values_only=True):
            product = row[1] if len(row) > 1 else None
            if not product or not str(product).strip():
                continue
            code_val = row[0] if len(row) > 0 else None
            unit_raw = row[2] if len(row) > 2 else None
            existence = _to_float(row[3] if len(row) > 3 else None, 0)
            stock = _to_float(row[4] if len(row) > 4 else None, 0)
            order_qty = _to_float(row[5] if len(row) > 5 else None)
            supplier = row[6] if len(row) > 6 else None
            supplier2 = row[7] if len(row) > 7 else None
            tipo = row[8] if len(row) > 8 else None
            phone = row[9] if len(row) > 9 else None
            visit_day = row[10] if len(row) > 10 else None
            responsible = row[11] if len(row) > 11 else None
            area = "cocina" if tipo and str(tipo).strip().upper() == "COCINA" else "salon"
            items.append({
                "code": str(code_val).strip() if code_val else None,
                "product_name": str(product).strip(),
                "unit": _normalize_unit(unit_raw),
                "existence": existence,
                "stock": stock,
                "order_quantity": order_qty,
                "supplier": str(supplier).strip() if supplier else None,
                "supplier2": str(supplier2).strip() if supplier2 else None,
                "supplier_phone": str(phone).strip() if phone else None,
                "supplier_visit_day": str(visit_day).strip() if visit_day else None,
                "area": area,
                "responsible": str(responsible).strip() if responsible else None,
            })

    wb.close()
    return items, None


def get_default_excel_path():
    """Ruta por defecto del Excel."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "excel_docs",
        "DATOS INVENTARIO.xlsx",
    )
