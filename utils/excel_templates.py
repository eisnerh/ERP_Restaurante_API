"""Generación de plantillas Excel para importar datos. Usado por script y API de descarga."""
import io
from openpyxl import Workbook
from openpyxl.styles import Font


def _wb_inventario():
    wb = Workbook()
    ws = wb.active
    ws.title = "INVENTARIO"
    headers = ["ID", "Producto", "UM", "Existencia", "Stock", "Pedido", "Provedor", "Proveedor 2", "TIPO INVENTARIO", "Teléfono", "Día Visita", "Responsable"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=3, column=c, value=h).font = Font(bold=True)
    samples = [
        ["001", "Arroz", "KG", 50, 100, 50, "Distribuidora XYZ", "", "COCINA", "2222-3333", "Lunes", "Juan"],
        ["002", "Coca Cola 500ml", "UND", 24, 48, 24, "Bebidas SA", "", "SALON", "2444-5555", "Martes", ""],
        ["003", "Aceite vegetal", "L", 5, 10, 5, "Abarrotes", "", "COCINA", "", "Miércoles", "María"],
    ]
    for r, row in enumerate(samples, 4):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_planilla_ubicaciones():
    wb = Workbook()
    ws = wb.active
    ws.title = "Ubicaciones y Empleados"
    header = ["CODIGO", "PLAZA SAN CARLOS", "HRS EXTRA", "CREDITOS COMIDA", "VALE EFECTIVO", "CCSS REBAJOS", "DIA PSG", "INCAPACIDADES", "NUMEROS DE CUENTA", "FECHA INGRESO"]
    for c, h in enumerate(header, 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    rows = [
        ["001", "Juan Pérez", 4, 0, 5000, 15000, "", "", "CR123456789", "2024-01-15"],
        ["002", "María López", 2, 5000, 0, 12000, "1", "", "CR987654321", "2023-06-01"],
        ["003", "Pedro García", 0, 0, 0, 8000, "", "", "", "2024-03-01"],
    ]
    for r, row in enumerate(rows, 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_casas():
    wb = Workbook()
    ws = wb.active
    ws.title = "Casas"
    headers = ["Codigo", "Nombre", "Direccion", "Telefono", "Email", "Activo"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, row in enumerate([["001", "Plaza San Carlos", "San Carlos centro", "2460-1234", "plaza@donraul.com", "SI"], ["002", "Mirador", "Calle principal", "2460-5678", "mirador@donraul.com", "SI"]], 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_menu():
    wb = Workbook()
    ws_cat = wb.active
    ws_cat.title = "Categorias"
    ws_cat.cell(1, 1, "Nombre").font = Font(bold=True)
    ws_cat.cell(1, 2, "Descripcion").font = Font(bold=True)
    for r, (n, d) in enumerate([("Bebidas", "Refrescos y bebidas"), ("Platos principales", "Comidas del día"), ("Postres", "")], 2):
        ws_cat.cell(r, 1, n)
        ws_cat.cell(r, 2, d)
    ws_pla = wb.create_sheet("Platos")
    ws_pla.cell(1, 1, "Nombre").font = Font(bold=True)
    ws_pla.cell(1, 2, "Descripcion").font = Font(bold=True)
    ws_pla.cell(1, 3, "Precio").font = Font(bold=True)
    ws_pla.cell(1, 4, "Categoria").font = Font(bold=True)
    ws_pla.cell(1, 5, "Disponible").font = Font(bold=True)
    for r, row in enumerate([("Coca Cola", "500ml", 1500, "Bebidas", "SI"), ("Casado", "Carne, arroz, frijoles", 4500, "Platos principales", "SI"), ("Tres leches", "", 2500, "Postres", "SI")], 2):
        for c, val in enumerate(row, 1):
            ws_pla.cell(r, c, val)
    return wb


def _wb_mesas():
    wb = Workbook()
    ws = wb.active
    ws.title = "Mesas"
    for c, h in enumerate(["Numero", "Capacidad", "Posicion_X", "Posicion_Y", "Ocupada"], 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, row in enumerate([(1, 4, 0, 0, "NO"), (2, 6, 1, 0, "NO"), (3, 2, 2, 0, "NO")], 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_clientes():
    wb = Workbook()
    ws = wb.active
    ws.title = "Clientes"
    for c, h in enumerate(["Nombre", "Cedula_RUC", "Email", "Telefono", "Direccion", "Notas", "Activo"], 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, row in enumerate([("Juan Mora", "1-2345-6789", "juan@email.com", "8888-9999", "San José", "", "SI"), ("Empresa ABC", "3-101-234567", "contabilidad@abc.com", "2222-3333", "", "Cliente corporativo", "SI")], 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_proveedores():
    wb = Workbook()
    ws = wb.active
    ws.title = "Proveedores"
    for c, h in enumerate(["Nombre", "Telefono", "Contacto", "Dia_Visita", "Visita_Programada"], 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, row in enumerate([("Distribuidora XYZ", "2222-3333", "Carlos López", "Lunes", "semanal"), ("Bebidas SA", "2444-5555", "Ana", "Martes", "bisemanal")], 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_unidades():
    wb = Workbook()
    ws = wb.active
    ws.title = "Unidades"
    for c, h in enumerate(["Simbolo", "Nombre"], 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, row in enumerate([("UND", "Unidad"), ("KG", "Kilogramo"), ("GR", "Gramo"), ("CJ", "Caja"), ("L", "Litro")], 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_puestos():
    wb = Workbook()
    ws = wb.active
    ws.title = "Puestos"
    for c, h in enumerate(["Nombre", "Tipo", "Salario_Base", "Horas_Por_Dia", "Aplicar_CCSS"], 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, row in enumerate([("Cajero", "empleado", 350000, 8, "SI"), ("Mesero", "empleado", 320000, 8, "SI"), ("Líder de Cocina", "empleado", 450000, 8, "SI")], 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_tipos_registro():
    wb = Workbook()
    ws = wb.active
    ws.title = "Tipos_Registro"
    for c, h in enumerate(["Nombre", "Codigo", "Descripcion", "Ocultar_Puesto"], 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, row in enumerate([
        ("Empleado", "empleado", "Empleado en planilla", "NO"),
        ("Mermas", "mermas", "Gasto por mermas", "SI"),
        ("Por contrato", "por_contrato", "Servicios por contrato", "NO"),
        ("Servicios profesionales", "servicios_profesionales", "Honorarios profesionales", "NO"),
    ], 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_tipos_deduccion():
    wb = Workbook()
    ws = wb.active
    ws.title = "Tipos_Deduccion"
    for c, h in enumerate(["Nombre", "Descripcion", "Puede_Negativo", "Basado_Horas", "Tasa_Porcentaje"], 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, row in enumerate([("CCSS", "CCSS trabajador", "NO", "NO", 0.1083), ("Vale efectivo", "Adelanto en efectivo", "NO", "NO", ""), ("Día libre intercambiado", "Horas negociables", "SI", "SI", "")], 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_empleados():
    wb = Workbook()
    ws = wb.active
    ws.title = "Empleados"
    headers = ["Nombre", "Codigo", "Cedula", "Numero_Cuenta", "Ubicacion", "Puesto", "Fecha_Ingreso", "Salario_Base", "Periodo_Pago", "Activo"]
    for c, h in enumerate(headers, 1):
        ws.cell(row=1, column=c, value=h).font = Font(bold=True)
    for r, row in enumerate([("Juan Pérez", "001", "1-2345-6789", "CR123456789", "Plaza San Carlos", "Cajero", "2024-01-15", 350000, "mensual", "SI"), ("María López", "002", "2-3456-7890", "CR987654321", "Plaza San Carlos", "Mesero", "2023-06-01", 320000, "mensual", "SI")], 2):
        for c, val in enumerate(row, 1):
            ws.cell(row=r, column=c, value=val)
    return wb


def _wb_desgloses():
    wb = Workbook()
    ws = wb.active
    ws.title = "Juan Pérez"
    ws.cell(1, 3, "1 de FEBRERO 2026")
    ws.cell(2, 3, "15 de FEBRERO 2026")
    ws.cell(5, 1, "Líder de Cocina")
    ws.cell(5, 2, "Juan Pérez")
    ws.cell(7, 1, "ASIGNACIONES")
    ws.cell(8, 1, "Salario Base")
    ws.cell(8, 2, 175000)
    ws.cell(8, 3, 175000)
    ws.cell(9, 1, "Horas Extras")
    ws.cell(9, 2, 4)
    ws.cell(9, 3, 26250)
    ws.cell(10, 1, "TOTAL ASIGNACIONES")
    ws.cell(10, 3, 201250)
    ws.cell(11, 1, "DEDUCCIONES")
    ws.cell(12, 1, "CCSS")
    ws.cell(12, 3, 21750)
    ws.cell(13, 1, "TOTAL DEDUCCIONES")
    ws.cell(13, 3, 21750)
    ws.cell(14, 1, "TOTAL DEPOSITADO")
    ws.cell(14, 3, 179500)
    ws.cell(15, 9, "CR123456789")
    ws.cell(3, 7, "MES")
    ws.cell(3, 8, 350000)
    ws.cell(4, 7, "QUINCENA")
    ws.cell(4, 8, 175000)
    return wb


TEMPLATES = [
    ("01_INVENTARIO.xlsx", _wb_inventario),
    ("01b_TIPOS_REGISTRO.xlsx", _wb_tipos_registro),
    ("02_PLANILLA_UBICACIONES_Y_REGISTROS.xlsx", _wb_planilla_ubicaciones),
    ("03_CASAS.xlsx", _wb_casas),
    ("04_MENU_CATEGORIAS_PLATOS.xlsx", _wb_menu),
    ("05_MESAS.xlsx", _wb_mesas),
    ("06_CLIENTES.xlsx", _wb_clientes),
    ("07_PROVEEDORES.xlsx", _wb_proveedores),
    ("08_UNIDADES.xlsx", _wb_unidades),
    ("09_PUESTOS.xlsx", _wb_puestos),
    ("10_TIPOS_DEDUCCION.xlsx", _wb_tipos_deduccion),
    ("11_EMPLEADOS.xlsx", _wb_empleados),
    ("12_DESGLOSES_EJEMPLO.xlsx", _wb_desgloses),
]


def generate_all_as_zip():
    """Genera todos los Excel y los empaqueta en un ZIP. Retorna (bytes, filename)."""
    import zipfile
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, gen_fn in TEMPLATES:
            wb = gen_fn()
            xl_buf = io.BytesIO()
            wb.save(xl_buf)
            zf.writestr(filename, xl_buf.getvalue())
    return buf.getvalue(), "plantillas_excel_erp.zip"
