"""
Prueba la conexión a la base de datos y muestra información.
Uso: python scripts/connect_db.py
"""
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def main():
    from app import app
    from extensions import db

    with app.app_context():
        uri = app.config["SQLALCHEMY_DATABASE_URI"]
        # Ocultar contraseña en la salida
        if "@" in uri and ":" in uri:
            parts = uri.split("@")
            if len(parts) == 2:
                user_part = parts[0]
                if "://" in user_part:
                    prefix, rest = user_part.split("://", 1)
                    if ":" in rest:
                        user = rest.split(":")[0]
                        safe_uri = f"{prefix}://{user}:****@{parts[1]}"
                    else:
                        safe_uri = uri
                else:
                    safe_uri = uri
            else:
                safe_uri = uri
        else:
            safe_uri = uri

        print("Conexión a la base de datos")
        print("=" * 50)
        print(f"URI: {safe_uri}")
        print()

        try:
            db.engine.connect()
            print("Estado: Conectado correctamente.")
            from sqlalchemy import inspect
            insp = inspect(db.engine)
            tables = insp.get_table_names()
            if tables:
                print(f"Tablas: {len(tables)}")
                for t in sorted(tables):
                    cols = insp.get_columns(t)
                    print(f"  - {t} ({len(cols)} columnas)")
            else:
                print("Tablas: ninguna (ejecuta create_tables.py o init_db.py)")
        except Exception as e:
            print(f"Estado: Error - {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
