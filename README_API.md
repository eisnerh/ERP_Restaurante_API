# API REST — ERP Raul Castaño

Documentación técnica de los endpoints. La API devuelve JSON.

**Base:** `http://127.0.0.1:5000/api`

---

## Base de datos

- **PostgreSQL**: configura `DATABASE_URL` en `.env` (ver `.env.example`)

La base inicia **en blanco**. Para importar inventario:

```bash
python scripts/import_inventory_excel.py --franchisee-id 1
```

---

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/menu/` | Menú completo (categorías con platos) |
| GET/POST | `/api/menu/categories` | Listar / crear categorías |
| GET/POST | `/api/menu/dishes` | Listar / crear platos |
| GET/POST | `/api/tables` | Listar / crear mesas |
| GET/POST | `/api/orders` | Listar / crear pedidos |
| GET/POST | `/api/inventory` | Listar / crear ítems de inventario |
| GET/POST | `/api/inventory/suppliers` | Proveedores |
| GET/POST | `/api/clients` | Clientes |
| GET/POST | `/api/purchases` | Órdenes de compra |
| GET | `/api/purchases/spending` | Reporte de gastos (`?from=`, `?to=`, `?supplier_id=`, `?format=csv`) |
| GET/POST | `/api/franchisees` | Franquiciados |
| POST | `/api/franchisees/current` | Establecer franquiciado actual |

---

## Inventario

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/inventory/import-excel` | Importar desde Excel |
| GET | `/api/inventory/report` | Reporte de faltantes (`?threshold=0.1`, `?format=json\|csv`) |
| POST | `/api/inventory/check-low-stock` | Revisar inventario bajo y crear alerta |
| GET | `/api/inventory/alerts` | Lista de alertas |

---

## Planilla

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET/POST | `/api/payroll/locations` | Ubicaciones de planilla |
| GET/POST | `/api/payroll/employees` | Empleados de la franquicia (`?location_id=`, `?active=`) |
| GET/POST | `/api/payroll/entries` | Registros (`?period_date=`, `?location_id=`, `employee_id`) |
| POST | `/api/payroll/import-excel` | Importar desde Excel |
| GET | `/api/payroll/payslips` | Desgloses de pago |
| GET | `/api/payroll/payslips/<id>/pdf` | PDF del desglose para imprimir |
| GET | `/api/payroll/payslips/summary-pdf` | PDF resumen de la quincena |

---

## Estructura del proyecto

```
restaurant_api/
  app.py, config.py, extensions.py
  models/             # Categorías, platos, mesas, pedidos, inventario, etc.
  routes/             # API y web
  schemas/            # Serialización JSON
  templates/          # Interfaz web
  static/             # CSS, JS
  utils/              # Excel, PDF
  excel_docs/         # Excels de inventario y planilla
  scripts/            # init_db, import_inventory_excel, connect_db, etc.
```
