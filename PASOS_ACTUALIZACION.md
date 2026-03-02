# Pasos para actualizar el ERP (versión anterior → actual)

Si ya tienes el proyecto instalado y actualizas el código, ejecuta estos pasos en orden:

## 1. Actualizar dependencias

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 2. Migraciones de base de datos

Ejecuta solo las que apliquen a tu instalación (si el script indica "ya existe", está bien):

| Migración | Cuándo ejecutar |
|-----------|-----------------|
| `python scripts/migrate_entry_types.py` | Para tipos de registro (Empleado, Mermas, Por contrato, etc.) |
| `python scripts/migrate_hrs_negativas.py` | Si usas planilla y ves errores con hrs_negativas |
| `python scripts/migrate_hr_employee_fields.py` | Si no tienes vacaciones ni cédula en empleados |
| `python scripts/migrate_add_purchase_price.py` | Si falta columna purchase_price en inventario |

## 3. Reiniciar la aplicación

```powershell
python app.py
```

## Cambios recientes

- **Tipos de registro**: Empleado, Mermas, Por contrato, Servicios profesionales y personalizados (Planilla → Configuración → Tipos de registro)
- **Casas de Don Raul**: Plaza San Carlos, Mirador, Brunch, Pan artesanal, Coronado (en lugar de "franquicias")
- **Planilla**: Horas extra siempre positivas + campo horas negativas
- **Desglose PDF**: Sin tabla "Desglose del salario"; asignaciones (Salario quincenal, Horas Extras) y deducciones fijas (Vales, Días de permiso, etc.)
- **Vacaciones**: Registro de días disfrutados, saldo real, reporte de vacaciones disfrutadas
- **Inventario**: Pedido sugerido = Stock - Existencia cuando hay faltante
