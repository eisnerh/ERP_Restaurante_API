# Tutorial de instalación desde cero

Guía para instalar el ERP Restaurant en el equipo del cliente, paso a paso.

---

## Requisitos del equipo

- **Windows 10/11** (o Linux/Mac con comandos equivalentes)
- **Python 3.8 o superior**
- Conexión a internet (solo para la primera instalación)

---

## Paso 1: Instalar Python (si no está instalado)

1. Descarga Python desde [python.org/downloads](https://www.python.org/downloads/)
2. Ejecuta el instalador
3. **Importante:** Marca la casilla **"Add Python to PATH"**
4. Haz clic en "Install Now"
5. Cierra y abre una nueva terminal (PowerShell o CMD) para verificar:

```powershell
python --version
```

Debe mostrar algo como `Python 3.11.x` o superior.

---

## Paso 2: Copiar el proyecto (define dónde se instala)

**La aplicación se instala donde copies la carpeta del proyecto.** No hay un "Program Files" ni ubicación fija: tú eliges.

Copia toda la carpeta del proyecto al equipo, por ejemplo:

| Ubicación | Uso típico |
|-----------|------------|
| `C:\ERP\restaurant_api` | Instalación local en el servidor |
| `D:\Aplicaciones\ERP` | Si prefieres otro disco |
| `\\Servidor\ERP` | Carpeta de red compartida |

**Importante:** Ejecuta `instalar.bat` desde esa misma carpeta. El instalador mostrará la ruta al inicio.

Abre la terminal en esa carpeta:

```powershell
cd C:\ERP\restaurant_api
```

*(Ajusta la ruta según donde hayas copiado el proyecto)*

---

## Paso 3: Crear el entorno virtual e instalar dependencias

### Opción A: Script automático (recomendado)

En PowerShell, desde la carpeta del proyecto:

```powershell
.\setup.ps1
```

Si aparece un error de permisos para ejecutar scripts:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Luego vuelve a ejecutar `.\setup.ps1`

### Opción B: Manual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Cuando el entorno está activo, verás `(venv)` al inicio de la línea de comandos.

---

## Paso 4: Configurar la base de datos (PostgreSQL)

1. Instala PostgreSQL desde [postgresql.org/download](https://www.postgresql.org/download/)
2. Durante la instalación, anota la contraseña del usuario `postgres`
3. Copia `.env.example` a `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
4. Edita `.env` y configura:
   ```
   DATABASE_URL=postgresql://postgres:TU_PASSWORD@localhost:5432/restaurant_erp
   ```
   *(Reemplaza TU_PASSWORD por la contraseña que definiste)*

---

## Paso 5: Crear la base de datos y las tablas

Con el entorno virtual activado:

```powershell
python scripts/init_db.py
```

Debe mostrar algo como:
```
1. Creando base de datos (si aplica)...
2. Creando tablas...
   Tablas creadas: categories, clients, dishes, ...
Listo. Puedes ejecutar: python app.py
```

Para verificar la conexión:

```powershell
python scripts/connect_db.py
```

---

## Paso 6: Ejecutar la aplicación

```powershell
python app.py
```

Verás:
```
 * Running on http://0.0.0.0:5000
```

Abre el navegador en: **http://127.0.0.1:5000/**

---

## Paso 7: Importar inventario desde Excel (opcional)

Si tienes el archivo `excel_docs/DATOS INVENTARIO.xlsx`:

1. En otra terminal (o detén la app con Ctrl+C, ejecuta el import y vuelve a iniciar):
   ```powershell
   cd C:\ERP\restaurant_api
   .\venv\Scripts\Activate.ps1
   python scripts/import_inventory_excel.py --franchisee-id 1
   ```

2. Se crearán proveedores e ítems de inventario automáticamente.

---

## Ejecutar al iniciar Windows (opcional)

Para que la aplicación se inicie automáticamente cuando el cliente encienda el equipo:

1. El proyecto incluye el archivo `iniciar_erp.bat`. Haz doble clic para iniciar la aplicación.

2. Para que se ejecute al iniciar Windows: clic derecho en `iniciar_erp.bat` → Crear acceso directo → Mover el acceso directo a la carpeta de inicio (escribe `shell:startup` en Ejecutar para abrirla).

---

## Resumen de comandos

| Acción | Comando |
|--------|---------|
| Activar entorno | `.\venv\Scripts\Activate.ps1` |
| Crear BD y tablas | `python scripts/init_db.py` |
| Verificar conexión | `python scripts/connect_db.py` |
| Ejecutar app | `python app.py` |
| Importar inventario | `python scripts/import_inventory_excel.py --franchisee-id 1` |
| Añadir columna purchase_price (BD existente) | `python scripts/migrate_add_purchase_price.py` |
| Tabla empleados y vínculo desgloses (BD existente) | `python scripts/migrate_add_employees.py` |
| Puestos y deducciones estándar global (BD existente) | `python scripts/migrate_standard_positions_deductions.py` |
| Campos HR empleados (cédula, salario, vacaciones) | `python scripts/migrate_hr_employee_fields.py` |
| Columna hrs_negativas en planilla | `python scripts/migrate_hrs_negativas.py` |
| Caja, facturas y gastos operacionales | `python scripts/migrate_caja_facturas.py` |
| Arqueo Z (desglose cierre caja) | `python scripts/migrate_arqueo_z.py` |
| Llave .p12 Hacienda en configuración | `python scripts/migrate_app_settings_hacienda_p12.py` |
| Datos de menú (opcional) | `python seed.py` |

---

## Instalador automático (recomendado para clientes)

Para instalar todo en un equipo nuevo (Python, dependencias, base de datos, acceso directo):

1. Copia la carpeta del proyecto donde quieras (ej. `C:\ERP\restaurant_api`)
2. Entra en esa carpeta y doble clic en `instalar.bat`
3. O en PowerShell: `cd C:\ERP\restaurant_api` y luego `.\instalar.bat`

**Dónde se instala:** En la misma carpeta donde está el proyecto. El instalador lo muestra al inicio.

El instalador:
- Descarga e instala Python si no está (vía winget)
- Detecta PostgreSQL y abre la descarga si falta
- Crea el entorno virtual e instala dependencias
- Crea `.env` y **solicita la contraseña de PostgreSQL** para guardarla
- **Crea la base de datos** `restaurant_erp` y todas las tablas automáticamente
- Ejecuta migraciones
- Genera el icono y crea acceso directo en el escritorio

Realiza los mismos pasos que la guía manual (ver abajo).

---

## Paso a paso manual (mismo resultado que el instalador)

Si prefieres instalar manualmente, sigue estos pasos en orden. El resultado será idéntico al del instalador.

| Paso | Acción | Comando o acción |
|------|--------|------------------|
| 1 | Instalar Python 3.8+ | Descargar de [python.org](https://www.python.org/downloads/), marcar "Add to PATH" |
| 2 | Instalar PostgreSQL | Descargar de [postgresql.org](https://www.postgresql.org/download/), anotar contraseña de `postgres` |
| 3 | Copiar proyecto | Ej. `C:\ERP\restaurant_api` |
| 4 | Crear entorno virtual | `python -m venv venv` |
| 5 | Activar venv | `.\venv\Scripts\Activate.ps1` |
| 6 | Instalar dependencias | `pip install -r requirements.txt` |
| 7 | Crear .env | `Copy-Item .env.example .env` |
| 8 | Configurar contraseña | Editar `.env`, cambiar `PGPASSWORD=1234` por tu contraseña de PostgreSQL |
| 9 | **Crear base de datos** | `python scripts/init_db.py` — crea la BD `restaurant_erp` y todas las tablas |
| 10 | Migraciones | `python scripts/migrate_hrs_negativas.py` |
| 11 | Crear icono (opcional) | `python scripts/crear_icono.py` |
| 12 | Ejecutar app | `python app.py` o doble clic en `iniciar_erp.bat` |

### Detalle del paso 9: Creación de la base de datos

El script `init_db.py` hace dos cosas automáticamente:

1. **Crea la base de datos** `restaurant_erp` en PostgreSQL (si no existe). Se conecta al servidor PostgreSQL con las credenciales de `.env` y ejecuta `CREATE DATABASE`.

2. **Crea todas las tablas** (categories, clients, dishes, employees, payroll_entries, etc.) y las "Casas de Don Raul" por defecto.

No necesitas crear la base de datos manualmente en pgAdmin ni en la consola de PostgreSQL. El script lo hace por ti.

---

## Crear ejecutable (.exe)

Para generar un ejecutable que no requiere Python instalado:

```powershell
python build_exe.py
```

O doble clic en `build.bat`.

El archivo `dist/ERP_Restaurant.exe` se creará. Para usarlo:

1. Copia la carpeta `dist` (o solo el .exe) al equipo destino
2. Copia `.env` o `.env.example` junto al ejecutable y renómbralo a `.env`
3. Configura PostgreSQL en el `.env`
4. Ejecuta `ERP_Restaurant.exe`
5. Abre http://localhost:5000 en el navegador

**Nota:** PostgreSQL debe estar instalado y corriendo en el equipo. El ejecutable solo incluye la aplicación web, no la base de datos.

---

## Actualizar desde versión anterior

Si ya tienes el proyecto instalado y actualizas el código:

1. **Actualizar dependencias:**
   ```powershell
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Migraciones de base de datos** (ejecuta solo las que apliquen):

   | Script | Cuándo ejecutar |
   |--------|-----------------|
   | `python scripts/migrate_entry_types.py` | Tipos de registro (Empleado, Mermas, Por contrato) |
   | `python scripts/migrate_hrs_negativas.py` | Errores con hrs_negativas en planilla |
   | `python scripts/migrate_hr_employee_fields.py` | Campos vacaciones, cédula en empleados |
   | `python scripts/migrate_add_purchase_price.py` | Falta columna purchase_price en inventario |

3. **Reiniciar la aplicación:** `python app.py`

---

## Solución de problemas

| Problema | Solución |
|---------|----------|
| "python no se reconoce" | Instala Python y marca "Add to PATH". Reinicia la terminal. |
| Error al ejecutar setup.ps1 | Ejecuta: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
| Error de conexión a PostgreSQL | Verifica que PostgreSQL esté corriendo. Revisa usuario y contraseña en `.env` |
| Puerto 5000 en uso | Edita `app.py` y cambia `port=5000` por `port=5001` |
| No se ven los datos | Ejecuta `python scripts/import_inventory_excel.py --franchisee-id 1` para cargar inventario |
| Error "no existe la columna purchase_price" | Ejecuta: `python scripts/migrate_add_purchase_price.py` |
| Error en planilla (hrs_negativas) | Ejecuta: `python scripts/migrate_hrs_negativas.py` |
| ¿Dónde está instalado? | Donde copiaste la carpeta del proyecto. El instalador muestra la ruta al inicio y al final. |

---

## Acceso desde otros equipos de la red

Por defecto la app escucha en `0.0.0.0:5000`, así que otros equipos en la misma red pueden acceder usando la IP del servidor:

```
http://192.168.1.100:5000/
```

*(Reemplaza por la IP real del equipo donde está instalado)*

Si el firewall de Windows bloquea, permite Python en el firewall o abre el puerto 5000.

---

## Quitar el aviso "Conexión no segura" (HTTPS local)

El navegador muestra "No seguro" en `http://localhost` porque usa HTTP. Para usar HTTPS sin avisos:

### Opción A: Certificados con mkcert (recomendado, sin aviso)

1. Instala mkcert: [https://github.com/FiloSottile/mkcert](https://github.com/FiloSottile/mkcert)  
   - Con Chocolatey: `choco install mkcert`
2. Ejecuta una vez: `mkcert -install`
3. Genera certificados: `python scripts/setup_https_local.py`
4. Inicia con HTTPS: `set USE_HTTPS_CERT=1 && python app.py`
5. Accede a **https://localhost:5000**

### Opción B: Certificado temporal (adhoc)

```powershell
set USE_HTTPS=1
python app.py
```

Accede a **https://localhost:5000**. La primera vez el navegador pedirá aceptar el certificado (clic en "Avanzado" → "Continuar a localhost").
