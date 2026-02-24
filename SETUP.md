# Setup - ERP Restaurant

Guía paso a paso para dejar el proyecto listo para ejecutar.

---

## 1. Requisitos previos

- **Python 3.8 o superior**  
  Comprueba: `python --version` o `py -3 --version`.

- **PostgreSQL** (recomendado para ERP) o MySQL / SQL Server  
  La base de datos inicia **en blanco** (sin datos de prueba).

---

## 2. Clonar o abrir el proyecto

Abre la carpeta del proyecto en la terminal:

```powershell
cd "g:\Mi unidad\proyectos\DJANGO\restaurant_api"
```

---

## 3. Entorno virtual y dependencias

### Opción A: Script automático (Windows PowerShell)

```powershell
.\setup.ps1
```

### Opción B: Manual

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## 4. Base de datos SQL

### Crear BD y tablas (todo en uno)

```powershell
python scripts/init_db.py
```

Este script crea la base de datos (PostgreSQL) y todas las tablas.

### Configuración

1. Copia `.env.example` a `.env` y configura:
   ```
   DATABASE_URL=postgresql://usuario:password@localhost:5432/restaurant_erp
   ```

   O usa variables separadas:
   ```
   PGHOST=localhost
   PGPORT=5432
   PGUSER=postgres
   PGPASSWORD=tu_password
   PGDATABASE=restaurant_erp
   ```

2. Ejecuta `python scripts/init_db.py` para crear la BD y tablas.

### Probar la conexión

```powershell
python scripts/connect_db.py
```

---

## 5. Ejecutar la aplicación

```powershell
python app.py
```

- **Interfaz web:** [http://127.0.0.1:5000/](http://127.0.0.1:5000/)
- **API (JSON):** [http://127.0.0.1:5000/api](http://127.0.0.1:5000/api)

La base de datos se crea vacía. Las tablas se generan automáticamente al iniciar.

---

## 6. Datos de ejemplo (opcional)

Para cargar categorías, platos y mesas de prueba:

```powershell
python seed.py
```

---

## Resumen rápido

```powershell
cd "g:\Mi unidad\proyectos\DJANGO\restaurant_api"
.\venv\Scripts\Activate.ps1
python app.py
```

---

## Solución de problemas

| Problema | Qué revisar |
|----------|-------------|
| `ModuleNotFoundError` | ¿Activaste el venv? ¿Ejecutaste `pip install -r requirements.txt`? |
| Error de conexión a PostgreSQL | ¿PostgreSQL está corriendo? ¿La BD existe? ¿Usuario y contraseña correctos en `.env`? |
| Puerto 5000 en uso | Cambiar en `app.py` la línea `app.run(..., port=5001)`. |
