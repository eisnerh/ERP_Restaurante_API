"""Configuración de la aplicación ERP."""
import os
from pathlib import Path

# Cargar .env si existe (python-dotenv)
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        try:
            load_dotenv(env_path, encoding="utf-8")
        except (UnicodeDecodeError, UnicodeError):
            load_dotenv(env_path, encoding="latin-1")
except ImportError:
    pass


def _get_default_db_uri():
    """URI por defecto: PostgreSQL (PG* vars o DATABASE_URL obligatorio)."""
    if os.environ.get("DATABASE_URL"):
        return os.environ.get("DATABASE_URL")
    if os.environ.get("PGUSER") or os.environ.get("PGPASSWORD") or os.environ.get("PGHOST"):
        user = os.environ.get("PGUSER", "postgres")
        pwd = os.environ.get("PGPASSWORD", "1234")
        host = os.environ.get("PGHOST", "localhost")
        port = os.environ.get("PGPORT", "5432")
        dbname = os.environ.get("PGDATABASE", "restaurant_erp")
        return f"postgresql://{user}:{pwd}@{host}:{port}/{dbname}"
    return "postgresql://postgres:1234@localhost:5432/restaurant_erp"


class Config:
    """Configuración base para ERP con base de datos SQL."""
    SECRET_KEY = os.environ.get("SECRET_KEY") or "clave-secreta-erp-cambiar-en-produccion"

    # Base de datos SQL: PostgreSQL (por defecto), MySQL o SQL Server via DATABASE_URL
    # Ver .env.example para ejemplos de conexión
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or _get_default_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}  # PostgreSQL
