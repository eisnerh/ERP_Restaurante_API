# ERP Raul Castaño

Sistema de gestión integral para **franquicias de restaurantes**. Permite administrar múltiples sucursales (franquiciados) desde una sola aplicación, cada una con su propio inventario, clientes, compras y planilla.

---

## ¿Qué hace este programa?

**ERP Raul Castaño** es un ERP (Enterprise Resource Planning) desarrollado en Flask que cubre las operaciones diarias de un restaurante o cadena de restaurantes:

| Módulo | Descripción |
|--------|-------------|
| **Menú** | Categorías y platos con precios |
| **Mesas** | Control de mesas y ocupación |
| **Pedidos** | Órdenes por mesa, estados, medio de pago, asociación a caja |
| **Caja** | Apertura/cierre de sesión, gastos operacionales, conciliación |
| **Facturas** | Facturación electrónica (FE/TE) con simulación Hacienda CR |
| **Reportes** | Ventas por período, top platos, ingresos vs gastos, por tipo de pago |
| **Inventario** | Productos de salón y cocina, existencias, stock, alertas de faltantes |
| **Proveedores** | Gestión de proveedores e importación desde Excel |
| **Clientes** | Base de datos de clientes |
| **Compras** | Órdenes de compra a proveedores |
| **Planilla** | Ubicaciones, empleados, desgloses de pago, vacaciones, PDF para firma |
| **Franquiciados** | Múltiples sucursales con datos separados por franquiciado |
| **Configuración** | Nombre del ERP, logo, favicon (por franquiciado) |

---

## Características principales

- **Multi-franquiciado**: Cada sucursal tiene su inventario, clientes, compras y planilla independientes.
- **Interfaz web**: CRUD completo para todas las secciones.
- **API REST**: Endpoints JSON para integración con otros sistemas.
- **Importación Excel**: Inventario y planilla desde archivos Excel.
- **Reportes PDF**: Desgloses de pago para imprimir y firmar.
- **Franquicias** (semilla): Mi casa Donde todo Empezo, Mi casa del Mirador, Mi Casa del Brunch, Mi Casa del Pan Artesanal, Mi Casa de las Plantas Coronado.
- **Vacaciones**: Registro de días disfrutados y reporte por empleado.
- **Alertas de inventario**: Notificaciones cuando el stock está bajo.

---

## Tecnologías

- **Backend**: Python, Flask, SQLAlchemy
- **Base de datos**: PostgreSQL
- **Frontend**: HTML, Bootstrap, JavaScript

---

## Inicio rápido

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
# Copiar .env.example a .env y configurar DATABASE_URL (PostgreSQL)
python scripts/init_db.py
python scripts/migrate_hrs_negativas.py   # Si actualizas desde versión anterior
python scripts/migrate_caja_facturas.py   # Caja, facturas y reportes (opcional)
python scripts/import_inventory_excel.py --franchisee-id 1   # Opcional
python app.py
```

**Interfaz:** http://127.0.0.1:5000

### Crear ejecutable (.exe)

Con Python y dependencias instaladas en la carpeta del proyecto:

```bash
python build_exe.py
```

O doble clic en `build.bat`. Se genera `dist/ERP_Restaurant.exe`.

**Para usar el .exe:** Copia el .exe a una carpeta, añade `.env` (desde `.env.example`) con la configuración de PostgreSQL, y ejecútalo. Abre http://localhost:5000

---

## Documentación

- **[INSTALACION.md](INSTALACION.md)** — Guía completa de instalación, actualización y solución de problemas
- **[TUTORIAL_USUARIO.md](TUTORIAL_USUARIO.md)** — Manual para el usuario final
- **[FORMATOS_EXCEL.md](FORMATOS_EXCEL.md)** — Formatos Excel para importar datos (inventario, planilla, etc.)
- **[README_API.md](README_API.md)** — Documentación técnica de la API (endpoints, ejemplos)

### Generar plantillas Excel

```bash
python scripts/generar_plantillas_excel.py
```

Crea archivos en `excel_docs/plantillas/` con el formato correcto para inventario, planilla, casas, menú, clientes, etc.
