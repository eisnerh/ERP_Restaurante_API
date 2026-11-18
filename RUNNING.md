

<!-- local-development:start -->
# Desarrollo local

Puedes abrir este repositorio en VS Code, Antigravity o Sublime Text. El compilador y los servicios necesarios dependen del componente indicado abajo.

## Python

Crea un entorno por aplicación desde PyCharm o la CLI. Python 3.12 es el punto inicial de compatibilidad; no se presume que todo el código o sus paquetes antiguos ya lo soporten.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r 'requirements.txt'
```

## Bases de datos

Revisa los scripts de esquema y crea una base de datos de prueba separada. SSMS 20 y pgAdmin 4 son clientes; SQL Server y PostgreSQL son motores distintos. Los scripts SQL Server no se ejecutan directamente en PostgreSQL. Las restauraciones deben hacerse sobre una base de prueba nueva. PostgreSQL 17 y 18 requieren comprobarse por separado.

## Componentes y validación

Inventario y compilaciones locales del 2026-11-15. Una compilación correcta no acredita todavía interacción, compatibilidad de base de datos, instalador ni despliegue.

| Componente | Tipo / destino | Validación |
| --- | --- | --- |
| [requirements.txt](<requirements.txt>) | python | Dependencias instaladas; pruebas de clientes e interfaz descritas abajo |

## Archivos ignorados

`.gitignore` excluye credenciales locales, estado del editor y salidas de las herramientas detectadas. No deja de versionar archivos que ya estaban en Git. Los manifiestos, archivos de bloqueo, recursos fuente y scripts de esquema forman parte del código.
<!-- local-development:end -->

## Pruebas del CRUD de clientes y de su interfaz

La factoría `application.create_app` puede importarse sin inicializar una base de datos. Las entradas `app.py` y `run.py` conservan su arranque normal. Las pruebas usan una configuración explícita con `INITIALIZE_DATABASE=False` y tablas de prueba en SQLite en memoria; no ejecutan migraciones ni semillas sobre la base PostgreSQL configurada.

```powershell
python -m unittest discover -s tests -v
# Comprobaciones opcionales de la interfaz, con Node instalado:
npm ci --ignore-scripts
npm test
```

Se validan alta, consulta, actualización, desactivación, filtros, tipos y longitudes, además de aislamiento entre franquiciados. La búsqueda de clientes agrupa pulsaciones y descarta respuestas antiguas; el guardado evita solicitudes duplicadas. Los valores del cliente se insertan como texto en la tabla. PostgreSQL utiliza explícitamente el controlador psycopg2 incluido en requirements.txt; las contraseñas construidas mediante variables PG se codifican correctamente en la URL.

Estas pruebas no certifican todavía todos los procesos de pedidos, facturación, inventario y planilla ni la migración completa en PostgreSQL.
