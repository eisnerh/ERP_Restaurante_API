# Tutorial para el usuario final — ERP Raul Castaño

Este documento explica cómo usar el programa ERP Raul Castaño paso a paso. Está pensado para usuarios finales que administran uno o varios restaurantes (Casas de Don Raul).

---

## 1. ¿Qué hace el programa?

El **ERP Raul Castaño** es un sistema para gestionar restaurantes. Permite:

- **Frontdesk**: Menú, mesas, pedidos y clientes.
- **Inventario**: Productos de salón y cocina, stock y alertas de faltantes.
- **Proveedores**: Lista de proveedores e importación desde Excel.
- **Compras**: Órdenes de compra a proveedores con seguimiento de gastos.
- **Planilla**: Empleados, registros de horas, vacaciones y desgloses de pago (PDF).
- **Control de gastos**: Resumen de compras + planilla por período.
- **Casas de Don Raul**: Múltiples sucursales con datos separados (Plaza San Carlos, Mirador, Brunch, etc.).
- **Configuración**: Nombre del ERP, logo, favicon y feriados.

Todo se maneja desde un navegador web (Chrome, Edge, Firefox, etc.).

---

## 2. Cómo entrar al programa

1. Asegúrate de que el programa esté en ejecución (ejecutable o `python app.py`).
2. Abre el navegador y ve a: **http://localhost:5000** (o la dirección que te indiquen).
3. En la esquina superior verás el nombre de la casa activa. Si hay varias casas, puedes cambiar la activa desde el menú.

### Menú lateral

Haz clic en el ícono de menú (☰) en la esquina superior derecha para ver todas las opciones.

---

## 3. Inicio (Dashboard)

En la pantalla principal verás:

- Un gráfico de **ítems más comprados por semana**.
- Botones de acceso rápido a cada módulo (Frontdesk, Inventario, Proveedores, Compras, Planilla, Control de gastos).

Puedes ir de un módulo a otro desde aquí o desde el menú lateral.

---

## 4. Menú

Aquí defines las categorías y platos que se venden.

### Categorías

1. Haz clic en **Nueva** (junto a Categorías).
2. Escribe el **Nombre** (ej. "Bebidas", "Postres").
3. Opcional: Descripción.
4. Guardar.

Puedes editar o eliminar categorías desde el listado.

### Platos

1. Haz clic en **Nuevo** (junto a Platos).
2. Completa: Nombre, Descripción, Precio (₡), Categoría.
3. Marca **Disponible** si el plato está a la venta.
4. Guardar.

Doble clic en un plato para editarlo.

---

## 5. Mesas

Sirve para controlar las mesas del salón.

1. Haz clic en **Nueva**.
2. Indica el **Número** de mesa.
3. Indica la **Capacidad** (personas).
4. Opcional: posición X e Y para un diagrama.
5. Marca **Ocupada** si ya hay clientes.
6. Guardar.

Al crear un pedido, podrás elegir la mesa desde un desplegable.

---

## 6. Pedidos

Aquí registras las órdenes de los clientes.

### Crear un pedido

1. Selecciona la **Mesa**.
2. Opcional: notas (ej. "sin cebolla").
3. En **Platos**: elige plato, cantidad y haz clic en **Agregar**. Repite para todos los platos.
4. Haz clic en **Crear pedido**.

### Cambiar estado del pedido

1. Localiza el pedido en el listado.
2. Haz clic para abrir el modal de cambio de estado.
3. Elige el estado:
   - **Pendiente**: Recién tomado.
   - **En preparación**: En cocina.
   - **Servido**: Ya llevado a la mesa.
   - **Pagado**: Cobrado.

---

## 7. Clientes

Base de datos de clientes (nombre, cédula/RUC, email, teléfono, dirección, notas).

1. Haz clic en **Nuevo**.
2. Completa los campos que necesites (nombre es obligatorio).
3. Guardar.

Puedes buscar clientes con el cuadro de búsqueda.

---

## 8. Inventario

Catálogo de productos de salón y cocina, con existencias y stock por casa.

### Crear ítems

1. Haz clic en **Nuevo ítem**.
2. Completa: Código, Nombre, Área (Salón / Cocina), Unidad, Existencia, Stock, Proveedor (opcional).
3. Guardar.

**Existencia**: Cantidad actual.  
**Stock**: Mínimo deseado. Si Existencia &lt; Stock, se genera alerta y pedido sugerido.

### Unidades

En la sección **Unidades** defines las unidades de medida (UND, kg, L, etc.).

### Alertas

- Se muestran los ítems donde Existencia &lt; Stock.
- **Pedido sugerido** = Stock − Existencia.
- Puedes exportar a CSV o ir a **Compras** para generar órdenes.

### Otras funciones

- **Importar Excel**: Para cargar inventario masivamente.
- **Copiar desde**: Copiar inventario de otra casa.
- **Exportar pedidos CSV**: Lista de faltantes para compras.

---

## 9. Proveedores

Gestionas los proveedores de cada casa.

1. Haz clic en **Nuevo**.
2. Completa: Nombre, Teléfono, Contacto, Día de visita, etc.
3. Guardar.

**Desde Excel**: Para cargar o actualizar proveedores masivamente.  
**Copiar desde**: Copiar proveedores de otra casa.  
**Duplicados**: Herramienta para buscar y fusionar proveedores repetidos.

---

## 10. Compras

Órdenes de compra a proveedores.

### Gastos en compras

En la parte superior puedes ver el historial de gastos filtrando por fechas y proveedor.

### Crear una orden

1. Haz clic en **Nueva orden**.
2. Indica **Fecha de compra** y **Proveedor**.
3. Opcional: **Usar ítems con stock bajo** para cargar productos faltantes de ese proveedor.
4. Añade los ítems: producto, cantidad, unidad, precio unitario.
5. Cambia el estado según el progreso:
   - **Borrador**: En edición.
   - **Enviada**: Enviada al proveedor.
   - **Recibida**: Recibida (cuando llegue el pedido).
   - **Cancelada**: No se usó.

### Reporte / Imprimir

El botón **Reporte / Imprimir** abre una página con el resumen de pedidos por período para imprimir.

---

## 11. Planilla

Sección para empleados, registros de horas, vacaciones y desgloses de pago.

**Importante**: Primero selecciona la casa activa (franquiciado/ubicación).

### Configuración

- **Ubicaciones**: Lugares de trabajo (sucursales/tiendas).
- **Puestos**: Cargos (cajero, mesero, cocinero, etc.).
- **Tipos de deducción**: Vale efectivo, facturas a crédito, CCSS, otros.

### Empleados

1. Haz clic en **Nuevo empleado**.
2. Completa: Nombre, Cédula, Ubicación, Puesto, Salario base, etc.
3. Guardar.

### Registros

Los registros son las horas trabajadas (por quincena). Puedes:

- Crear registros manualmente.
- Importar desde Excel.

### Desgloses

- **Generar desgloses**: Cálculo de salarios según registros.
- **Ver desgloses**: Listado de desgloses generados.
- **PDF**: Para imprimir y entregar a cada empleado.

### Reportes

- Reporte por empleado (horas, asignaciones, deducciones).
- Reporte de vacaciones disfrutadas.
- PDF de desglose individual para firma.

### Vacaciones

- Registrar días de vacaciones disfrutados por empleado.
- Ver el saldo restante después del disfrute.

---

## 12. Control de gastos

Resumen de gastos por período de planilla.

1. Selecciona el **Año**.
2. Elige una **Quincena** o define rango manual (Desde / Hasta).
3. Haz clic en **Consultar**.

Verás:

- Total de **Compras** (inventario).
- Total de **Planilla** (desgloses).
- **Total gastos** (suma).

Desde ahí puedes ir a ver el detalle de compras o planilla.

---

## 13. Casas de Don Raul (Franquiciados)

Administración de las sucursales/casas.

1. Haz clic en **Nueva casa**.
2. Completa: Código, Nombre, Dirección, Teléfono, Email.
3. Opcional: Lugares de trabajo (ubicaciones para planilla).
4. Guardar.

Cada casa tiene su propio inventario, clientes, compras y planilla.

**Cambiar de casa**: En el menú lateral o en la barra superior hay un selector para cambiar la casa activa.

---

## 14. Configuración

### Apariencia

- **Nombre de la aplicación**: Título que se muestra.
- **Icono en la barra**: Ícono del menú.
- **Logo**: Imagen del encabezado (ruta o subir archivo).
- **Favicon**: Ícono de la pestaña del navegador.

### Feriados

Lista de feriados de Costa Rica. Puedes usar **Sincronizar ahora** para actualizar la lista.

---

## 15. Consejos rápidos

- **Doble clic** en muchas tablas abre el formulario de edición.
- **Buscar** en clientes, inventario y proveedores filtra mientras escribes.
- Las **alertas de inventario** te ayudan a saber qué pedir. Usa "Ir a Compras" para crear la orden rápidamente.
- En **Compras**, el botón **Usar ítems con stock bajo** rellena la orden con productos faltantes del proveedor elegido.
- Los **desgloses PDF** de planilla se pueden imprimir para que los empleados firmen.
- Siempre revisa que la **casa activa** sea la correcta antes de crear registros o desgloses.

---

## 16. Solución rápida de problemas

| Problema | Qué hacer |
|----------|-----------|
| No se abre la página | Comprueba que el programa esté en ejecución y que uses http://localhost:5000 |
| No aparecen datos | Verifica que tengas seleccionada la casa correcta. |
| Error al guardar | Revisa que los campos obligatorios estén llenos. |
| No carga el inventario | Confirma que la base de datos esté configurada (PostgreSQL). |
| Los desgloses no cuadran | Revisa registros, deducciones y salarios base de los empleados. |

Si el problema persiste, contacta al administrador o soporte técnico con los detalles del mensaje de error.

---

*Documento creado para usuarios del ERP Raul Castaño.*
