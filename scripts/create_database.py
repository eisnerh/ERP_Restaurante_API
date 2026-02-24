"""
Crea la base de datos PostgreSQL si no existe.
Uso: python scripts/create_database.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        try:
            load_dotenv(env_path, encoding="utf-8")
        except (UnicodeDecodeError, UnicodeError):
            load_dotenv(env_path, encoding="latin-1")
except ImportError:
    pass


def get_db_config():
    """Extrae host, port, user, password, dbname de DATABASE_URL o PG*."""
    url = os.environ.get("DATABASE_URL")
    if url and isinstance(url, str) and url.startswith("postgresql://"):
        try:
            from urllib.parse import urlparse
            p = urlparse(url)
            return {
                "host": p.hostname or "localhost",
                "port": p.port or 5432,
                "user": p.username or "postgres",
                "password": p.password or "",
                "dbname": (p.path or "/restaurant_erp").lstrip("/").split("?")[0] or "restaurant_erp",
            }
        except Exception:
            pass
    return {
        "host": os.environ.get("PGHOST", "localhost"),
        "port": int(os.environ.get("PGPORT", "5432")),
        "user": os.environ.get("PGUSER", "postgres"),
        "password": os.environ.get("PGPASSWORD", "postgres"),
        "dbname": os.environ.get("PGDATABASE", "restaurant_erp"),
    }


def create_postgres_db():
    """Crea la base de datos en PostgreSQL si no existe."""
    cfg = get_db_config()
    if not cfg.get("dbname"):
        print("Error: No se pudo obtener el nombre de la base de datos.")
        return False

    try:
        import psycopg2
        from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    except ImportError:
        print("Error: Instala psycopg2: pip install psycopg2-binary")
        return False

    conn = None
    try:
        conn = psycopg2.connect(
            host=cfg["host"],
            port=cfg["port"],
            user=cfg["user"],
            password=cfg["password"],
            dbname="postgres",
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (cfg["dbname"],),
        )
        if cur.fetchone():
            print(f"La base de datos '{cfg['dbname']}' ya existe.")
        else:
            cur.execute(f'CREATE DATABASE "{cfg["dbname"]}"')
            print(f"Base de datos '{cfg["dbname"]}' creada correctamente.")
        cur.close()
        return True
    except Exception as e:
        print(f"Error al crear la base de datos: {e}")
        return False
    finally:
        if conn:
            conn.close()


def main():
    url = os.environ.get("DATABASE_URL") or ""
    if "postgresql" in url or os.environ.get("PGHOST"):
        create_postgres_db()
    else:
        print("No se detectó PostgreSQL. Define DATABASE_URL o PGHOST para crear la BD.")


if __name__ == "__main__":
    main()
