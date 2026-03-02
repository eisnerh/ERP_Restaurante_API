# Formatos Excel para importar datos al ERP Raul Castaño

Este documento describe el formato de cada archivo Excel para cargar información en las tablas del sistema.

## Cómo generar las plantillas

Ejecuta desde la raíz del proyecto:

```bash
python scripts/generar_plantillas_excel.py
```

Se crearán archivos en `excel_docs/plantillas/` con el formato correcto y datos de ejemplo.

---

## Tabla resumida

| Archivo | Tabla(s) | ¿Import disponible? | Dónde importar |
|---------|----------|--------------------|-----------------|
| 01_INVENTARIO.xlsx | Inventario + Proveedores | Sí | **Configuración → Importar Excel** o Inventario → Importar Excel |
| 02_PLANILLA_UBICACIONES_Y_REGISTROS.xlsx | Ubicaciones, Registros | Sí | **Configuración → Importar Excel** o Planilla → Importar Excel |
| 03_CASAS.xlsx | Franquiciados | Sí | **Configuración → Importar Excel** |
| 04_MENU_CATEGORIAS_PLATOS.xlsx | Categorías, Platos | Sí | **Configuración → Importar Excel** |
| 05_MESAS.xlsx | Mesas | Sí | **Configuración → Importar Excel** |
| 06_CLIENTES.xlsx | Clientes | Sí | **Configuración → Importar Excel** |
| 07_PROVEEDORES.xlsx | Proveedores | Sí | **Configuración → Importar Excel** |
| 08_UNIDADES.xlsx | Unidades | Sí | **Configuración → Importar Excel** |
| 09_PUESTOS.xlsx | Puestos | Sí | **Configuración → Importar Excel** |
| 10_TIPOS_DEDUCCION.xlsx | Tipos deducción | Sí | **Configuración → Importar Excel** |
| 11_EMPLEADOS.xlsx | Empleados | Sí | **Configuración → Importar Excel** |
| 12_DESGLOSES_EJEMPLO.xlsx | Desgloses (Payslips) | Sí | Planilla → Desgloses → Importar Excel |

---

## 1. Inventario (01_INVENTARIO.xlsx)

**Import:** Sí. En Inventario → Importar Excel.

**Archivo:** Debe estar en `excel_docs/DATOS INVENTARIO.xlsx` o subir vía API con la ruta.

**Hoja:** `INVENTARIO`  
**Fila de cabecera:** 3  
**Datos:** Desde fila 4

| Col | Campo | Tipo | Obligatorio | Descripción |
|-----|-------|------|-------------|-------------|
| A | ID | Texto | No | Código del producto |
| B | Producto | Texto | **Sí** | Nombre del ítem |
| C | UM | Texto | No | Unidad: UND, KG, GR, CJ, L (default: UND) |
| D | Existencia | Número | No | Cantidad actual en bodega |
| E | Stock | Número | No | Cantidad mínima deseada (umbral de alerta) |
| F | Pedido | Número | No | Pedido sugerido (opcional) |
| G | Provedor | Texto | No | Nombre proveedor principal |
| H | Proveedor 2 | Texto | No | Segundo proveedor |
| I | TIPO INVENTARIO | Texto | No | `COCINA` o `SALON` (default: salon) |
| J | Teléfono | Texto | No | Teléfono del proveedor |
| K | Día Visita | Texto | No | Día de visita del proveedor |
| L | Responsable | Texto | No | Persona responsable del ítem |

**Nota:** Al importar inventario, también se extraen y crean/actualizan los proveedores desde las columnas Provedor, Teléfono y Día Visita.

---

## 2. Planilla: Ubicaciones y Registros (02_PLANILLA_UBICACIONES_Y_REGISTROS.xlsx)

**Import:** Sí. En Planilla → Configuración → Ubicaciones → Importar Excel.

**Archivo:** `excel_docs/DATOS DE RABAJOS Y CARGOS ADICIONALES PARA PLANILLA.xlsx`

**Estructura:**
- Filas de **cabecera**: tienen en columna C algo como "HRS" o "VALE" y en D "CREDITOS" o "COMIDA".
- En cabecera, la columna B tiene el **nombre de la ubicación** (ej. PLAZA SAN CARLOS).
- Filas de **datos**: debajo de cada cabecera, columna B = nombre del empleado.

| Col | Cabecera | Dato |
|-----|----------|------|
| A | CODIGO | Código empleado |
| B | [Nombre ubicación] | Nombre empleado |
| C | HRS EXTRA | Horas extra |
| D | CREDITOS COMIDA | Créditos comida |
| E | VALE EFECTIVO | Vale efectivo (monto) |
| F | CCSS REBAJOS | Monto CCSS |
| G | DIA PSG | Día PSG |
| H | INCAPACIDADES | Incapacidades |
| I | NUMEROS DE CUENTA | Número cuenta (ej. CR123456789) |
| J | FECHA INGRESO | Fecha ingreso (YYYY-MM-DD) |

**Bloques:** Puedes tener varias ubicaciones. Cada bloque empieza con una fila cabecera donde B = nombre de la ubicación. Los empleados siguientes pertenecen a esa ubicación hasta la próxima cabecera.

**Tipos especiales:** Si el nombre en B es "MERMAS" o "MERMA", se trata como tipo mermas.

---

## 3. Desgloses (12_DESGLOSES_EJEMPLO.xlsx)

**Import:** Sí. En Planilla → Desgloses → Importar Excel.

**Archivo:** Debe estar en `excel_docs/` con nombre que contenga "PLANILLA" y "PLAZA" (ej. `PLANILLA RAUL CASTAÑO PLAZA SAN CARLOS.xlsx`).

**Estructura:** Una **hoja por empleado**. El nombre de la hoja = nombre del empleado.

El parser busca:
- **Período:** Fechas en español tipo "1 de FEBRERO 2026" en columna C.
- **Cargo y empleado:** Filas con "LIDER", "COLABORADOR" o "SUPERVISOR" en col A.
- **Salarios:** Col G = "MES", "QUINCENA", "SEMANA", "DIA", "HORA", "EXTRA" → Col H = valor.
- **ASIGNACIONES:** Lista de conceptos (col A) con montos (col B o C).
- **DEDUCCIONES:** Lista de conceptos con montos.
- **TOTAL ASIGNACIONES**, **TOTAL DEDUCCIONES**, **TOTAL DEPOSITADO**.
- **Número de cuenta:** CR + dígitos en columna I.

---

## 4. Casas / Franquiciados (03_CASAS.xlsx)

**Import:** Referencia. Se cargan manualmente desde Casas de Don Raul.

| Columna | Descripción |
|---------|-------------|
| Codigo | Código único (ej. 001, PLAZA-SC) |
| Nombre | Nombre de la casa * |
| Direccion | Dirección |
| Telefono | Teléfono |
| Email | Correo |
| Activo | SI / NO |

---

## 5. Menú: Categorías y Platos (04_MENU_CATEGORIAS_PLATOS.xlsx)

**Import:** Referencia. Se cargan desde Menú.

**Hoja Categorias:**
| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre categoría * |
| Descripcion | Descripción |

**Hoja Platos:**
| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre del plato * |
| Descripcion | Descripción |
| Precio | Precio en colones |
| Categoria | Nombre de categoría (debe existir) |
| Disponible | SI / NO |

---

## 6. Mesas (05_MESAS.xlsx)

| Columna | Descripción |
|---------|-------------|
| Numero | Número de mesa * |
| Capacidad | Personas * |
| Posicion_X | Columna (para diagrama) |
| Posicion_Y | Fila (para diagrama) |
| Ocupada | SI / NO |

---

## 7. Clientes (06_CLIENTES.xlsx)

| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre * |
| Cedula_RUC | Cédula o RUC |
| Email | Correo |
| Telefono | Teléfono |
| Direccion | Dirección |
| Notas | Notas |
| Activo | SI / NO |

---

## 8. Proveedores (07_PROVEEDORES.xlsx)

**Nota:** Los proveedores también se cargan desde el Excel de Inventario. Este formato es independiente.

| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre del proveedor * |
| Telefono | Teléfono |
| Contacto | Persona de contacto |
| Dia_Visita | Día de visita |
| Visita_Programada | semanal, bisemanal, diario |

---

## 9. Unidades (08_UNIDADES.xlsx)

Unidades son **globales** (no por casa).

| Columna | Descripción |
|---------|-------------|
| Simbolo | UND, KG, GR, CJ, L * |
| Nombre | Kilogramo, Unidad, etc. |

---

## 10. Puestos (09_PUESTOS.xlsx)

Puestos son **globales**.

| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre del puesto * |
| Tipo | empleado, administrador, administrativo, inventario, custom |
| Salario_Base | Salario mensual (₡) |
| Horas_Por_Dia | Default 8 |
| Aplicar_CCSS | SI / NO |

---

## 11. Tipos de deducción (10_TIPOS_DEDUCCION.xlsx)

**Globales.**

| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre * |
| Descripcion | Descripción |
| Puede_Negativo | SI / NO |
| Basado_Horas | SI / NO |
| Tasa_Porcentaje | Ej. 0.1083 para CCSS |

---

## 12. Empleados (11_EMPLEADOS.xlsx)

| Columna | Descripción |
|---------|-------------|
| Nombre | Nombre * |
| Codigo | Código interno |
| Cedula | Cédula |
| Numero_Cuenta | Cuenta bancaria |
| Ubicacion | Nombre de ubicación (debe existir) |
| Puesto | Nombre de puesto (debe existir) |
| Fecha_Ingreso | YYYY-MM-DD |
| Salario_Base | Salario mensual |
| Periodo_Pago | mensual, quincenal, semanal, diario, por_hora |
| Activo | SI / NO |

---

## Orden recomendado para cargar datos nuevos

1. **Casas** (Franquiciados) – primero, todo depende de la casa.
2. **Inventario** – crea ítems y proveedores.
3. **Unidades** – si faltan (UND, KG, etc. suelen existir por defecto).
4. **Menú** – categorías y platos.
5. **Mesas** – para pedidos.
6. **Clientes** – si los usas.
7. **Planilla:** Puestos → Tipos deducción → Ubicaciones → Empleados → Registros.
8. **Desgloses** – si importas desde Excel externo.

---

## Problemas comunes

- **Codificación:** Guarda los Excel en UTF-8 o evita caracteres especiales en nombres si hay errores.
- **Fechas:** Usa formato YYYY-MM-DD (ej. 2024-01-15) o el formato en español que reconoce el parser.
- **Casa activa:** Antes de importar, selecciona la casa correcta en el menú.
- **Referencias:** Al importar platos, empleados, etc., los nombres de categoría, ubicación o puesto deben coincidir exactamente con los ya creados.
