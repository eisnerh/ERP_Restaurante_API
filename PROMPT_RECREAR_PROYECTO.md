# Prompt para recrear el proyecto ERP Restaurant desde cero

Usa este prompt con otra IA para que genere el proyecto completo. Copia y pega el contenido a continuación.

---

## INSTRUCCIONES PARA LA IA

Crea un **ERP para franquicias de restaurantes** en Python con Flask. El sistema debe permitir administrar múltiples sucursales (franquiciados) desde una sola aplicación, cada una con su propio inventario, clientes, compras y planilla.

### Stack tecnológico obligatorio

- **Backend**: Python 3.8+, Flask, SQLAlchemy, Marshmallow
- **Base de datos**: PostgreSQL (no SQLite)
- **Frontend**: HTML5, Bootstrap 5, JavaScript vanilla (sin frameworks)
- **Dependencias**: Flask, Flask-SQLAlchemy, Flask-Marshmallow, marshmallow, openpyxl, reportlab, psycopg2-binary, python-dotenv, holidays

### Arquitectura del proyecto

```
restaurant_api/
├── app.py                 # Aplicación principal, create_app(), blueprints
├── config.py              # Config desde .env, DATABASE_URL PostgreSQL
├── extensions.py           # db = SQLAlchemy(), ma = Marshmallow()
├── requirements.txt
├── .env.example            # DATABASE_URL=postgresql://user:pass@localhost:5432/restaurant_erp
├── models/                 # Modelos SQLAlchemy
├── schemas/                # Esquemas Marshmallow para serialización
├── routes/                 # Blueprints Flask (menu, orders, inventory, payroll, web, etc.)
├── utils/                  # Utilidades (franchisee, payslip_pdf, excel_inventory, holidays_sync)
├── templates/              # Jinja2 HTML
├── static/
│   ├── css/style.css
│   └── js/crud.js          # Funciones apiGet, apiPost, apiPut, apiDelete, showMsg
└── scripts/
    ├── init_db.py          # Crea BD y tablas con db.create_all()
    └── import_inventory_excel.py
```

### Modelos de base de datos (todos con franchisee_id excepto DeductionType, Unit, Holiday)

| Modelo | Tabla | Campos principales |
|--------|-------|-------------------|
| Franchisee | franchisees | id, code, name, active |
| Category | categories | id, franchisee_id, name, display_order |
| Dish | dishes | id, franchisee_id, category_id, name, price, active |
| Table | tables | id, franchisee_id, name, capacity, status |
| Order | orders | id, franchisee_id, table_id, client_id, status, total |
| OrderItem | order_items | id, order_id, dish_id, quantity, unit_price |
| InventoryItem | inventory_items | id, franchisee_id, name, quantity, unit_id, supplier_id, purchase_price |
| InventoryAlert | inventory_alerts | id, franchisee_id, item_id, threshold, created_at |
| Supplier | suppliers | id, franchisee_id, name, contact |
| Client | clients | id, franchisee_id, name, phone, email |
| PurchaseOrder | purchase_orders | id, franchisee_id, supplier_id, order_date, status |
| PurchaseOrderItem | purchase_order_items | id, purchase_order_id, item_id, quantity, unit_price |
| PayrollLocation | payroll_locations | id, franchisee_id, name |
| Position | positions | id, franchisee_id, name, position_type, salario_base, horas_dia, dias_semana |
| DeductionType | deduction_types | id, name, description, rate_pct, can_be_negative, is_hours_based |
| Employee | employees | id, franchisee_id, location_id, position_id, name, cedula, fecha_ingreso, fecha_salida, salario_base, salario_hora, horas_por_dia, periodo_pago, vacaciones_dias_tomados |
| VacationRecord | vacation_records | id, employee_id, fecha_desde, fecha_hasta, dias_tomados |
| PayrollEntry | payroll_entries | id, location_id, employee_id, position_id, period_date, employee_name, entry_type, hrs_extra, creditos_comida, vale_efectivo, notes |
| Payslip | payslips | id, franchisee_id, employee_id, location_name, employee_name, period_start, period_end, tipo_pago, total_asignaciones, total_deducciones, total_depositado |
| PayslipLine | payslip_lines | id, payslip_id, line_type, concept, amount |
| PaymentRecord | payment_records | id, franchisee_id, employee_id, payslip_id, amount, payment_date, period_start, period_end, periodo_tipo, created_at |
| Unit | units | id, name |
| AppSettings | app_settings | id, franchisee_id, app_name, logo_url, favicon_url |

### Multi-franquiciado

- Cada petición tiene un franquiciado activo en sesión (cookie).
- `franchisee_id` en query string: `?franchisee_id=1` cambia el franquiciado activo.
- Selector de franquiciado en la barra de navegación.
- Todas las consultas filtran por `franchisee_id` del franquiciado actual.

### Módulos y rutas web

| Ruta | Plantilla | Descripción |
|------|-----------|-------------|
| / | dashboard.html | Inicio |
| /menu | menu.html | Categorías y platos |
| /mesas | mesas.html | Mesas y ocupación |
| /pedidos | pedidos.html | Pedidos por mesa |
| /clientes | clientes.html | CRUD clientes |
| /inventario | inventario.html | Productos, stock, alertas |
| /proveedores | proveedores.html | Proveedores |
| /compras | compras.html | Órdenes de compra |
| /planilla | planilla.html | Planilla completa |
| /control-gastos | control_gastos.html | Gastos |
| /franquiciados | franquiciados.html | CRUD franquiciados |
| /configuracion | configuracion.html | Config por franquiciado |

### Módulo Planilla (detalle)

La planilla tiene 6 pestañas:

1. **Configuración** (acordeón): Ubicaciones, Puestos, Tipos de deducción
2. **Empleados**: CRUD con nombre, ubicación, puesto, fecha ingreso, salario base, vacaciones, aguinaldo
3. **Registros**: Registros de planilla (PayrollEntry) por ubicación, fecha, empleado; tipo empleado/mermas; hrs extra, créditos comida, vale. Al seleccionar empleado, auto-completar nombre, ubicación y puesto.
4. **Desgloses**: Payslips filtrados por ubicación y período. Botones: Registrar pago, Generar desde BD, Importar Excel, Imprimir desgloses. Tabla con: Colaborador, Cargo, Ubicación, Tipo pago (selector), Período, Total, PDF, Eliminar. Sección "Pagos registrados en este período" con botón Eliminar por pago.
5. **Reportes**: Pagos realizados filtrados por período (desde/hasta) y empleado opcional. Períodos rápidos: Último mes, Trimestre, 6 meses, Año. Tabla de pagos con PDF por fila.

**Registrar pago (modal simple)**: Empleado, tipo período (mensual/quincenal/semanal/diario), monto (opcional, se calcula del salario base), fecha. **Generar desde BD**: Modal con empleados, selector de tipo_pago por empleado, genera Payslips desde PayrollEntry y Employee.

### API REST

- Prefijo `/api/` para endpoints JSON.
- Estructura: `/api/menu/categories`, `/api/menu/dishes`, `/api/tables`, `/api/orders`, `/api/inventory`, `/api/inventory/suppliers`, `/api/clients`, `/api/purchases`, `/api/payroll/locations`, `/api/payroll/employees`, `/api/payroll/entries`, `/api/payroll/payslips`, `/api/payroll/payments`, `/api/payroll/generate-payslips`, etc.
- CRUD estándar: GET lista, GET /:id, POST, PUT /:id, DELETE /:id donde aplique.
- Payroll: `GET /payments?from_date=&to_date=&employee_id=`, `DELETE /payslips/:id`, `POST /generate-payslips` con body `period_start`, `period_end`, `employee_ids`, `tipo_por_empleado`.

### PDFs

- Desglose individual: `GET /payslips/:id/pdf`
- Batch desgloses: `GET /payslips/batch-pdf?location_name=&period_start=&period_end=`
- Resumen planilla: `GET /payslips/summary-pdf?location_name=&period_start=&period_end=`
- Reporte empleado: `GET /employees/:id/report?from_date=&to_date=`
- Comprobante pago sin desglose: `GET /payments/:id/payslip-pdf`

### Importación Excel

- Inventario desde `excel_docs/DATOS INVENTARIO.xlsx`
- Planilla/desgloses desde Excel con estructura específica (ubicación, empleado, período, líneas)

### Cálculos Costa Rica

- Vacaciones: 14 días por cada 50 semanas laboradas
- Aguinaldo: 1/12 del salario por mes en el año
- CCSS: 10.83% (deducción trabajador)
- Horas extras: 1.5x ordinarias, 2x festivos

### Inicialización

- `init_db.py`: crea BD PostgreSQL, tabla franchisees, franquiciado por defecto, DeductionType por defecto, sincroniza feriados (holidays).
- `.env`: `DATABASE_URL=postgresql://postgres:password@localhost:5432/restaurant_erp`

### Interfaz base

- `base.html`: navbar con logo, selector franquiciado, menú offcanvas.
- Menú: Inicio, Frontdesk (Menú, Mesas, Pedidos, Clientes), Inventario, Proveedores, Compras, Planilla, Control de gastos, Franquiciados, Configuración.
- Bootstrap 5, Bootstrap Icons.
- `crud.js`: `apiGet`, `apiPost`, `apiPut`, `apiDelete`, `showMsg`, `modalShow`, `modalHide`.

### Entregables

1. Código fuente completo y funcional
2. `requirements.txt` con versiones
3. `README.md` con descripción y inicio rápido
4. `INSTALACION.md` con guía paso a paso para el cliente
5. `.env.example` con variables necesarias

---

## Notas adicionales para la IA

- Usa SQLAlchemy con `db.ForeignKey` y `db.relationship`.
- Los esquemas Marshmallow deben tener `load_instance=True` para deserializar a objetos.
- Las rutas de planilla usan `get_or_default_franchisee_id()` de `utils.franchisee` para filtrar por franquiciado.
- Los PDFs se generan con ReportLab.
- Los empleados tienen `vacation_days()`, `aguinaldo_proporcional()`, `antiguedad_meses()` como métodos.
- La tabla `holidays` almacena feriados; se sincroniza con la librería `holidays` para Costa Rica.
