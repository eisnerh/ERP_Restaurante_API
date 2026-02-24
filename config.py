"""Configuración de la aplicación ERP."""
import os
import sys
from pathlib import Path

# Directorio base: PyInstaller extrae a _MEIPASS; .env debe estar junto al .exe
def _base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent  # .env junto al ejecutable
    return Path(__file__).resolve().parent

BASE_DIR = _base_dir()

# Cargar .env si existe (python-dotenv)
try:
    from dotenv import load_dotenv
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        try:
            load_dotenv(env_path, encoding="utf-8", override=True)
        except (UnicodeDecodeError, UnicodeError):
            load_dotenv(env_path, encoding="latin-1", override=True)
except ImportError:
    pass


def _get_default_db_uri():
    """URI por defecto: solo PostgreSQL. Ignora SQLite si está configurado."""
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if url and "sqlite" in url.lower():
        url = ""  # No usar SQLite
    if url:
        return url
    if os.environ.get("PGUSER") or os.environ.get("PGPASSWORD") or os.environ.get("PGHOST"):
        user = os.environ.get("PGUSER", "postgres")
        pwd = os.environ.get("PGPASSWORD", "1234")
        host = os.environ.get("PGHOST", "localhost")
        port = os.environ.get("PGPORT", "5432")
        dbname = os.environ.get("PGDATABASE", "restaurant_erp")
        return f"postgresql://{user}:{pwd}@{host}:{port}/{dbname}"
    return "postgresql://postgres:1234@localhost:5432/restaurant_erp"


def _get_db_uri():
    """Solo PostgreSQL. Ignora SQLite."""
    return _get_default_db_uri()


class Config:
    """Configuración base para ERP. Solo PostgreSQL."""
    SECRET_KEY = os.environ.get("SECRET_KEY") or "clave-secreta-erp-cambiar-en-produccion"

    # Base de datos: solo PostgreSQL (PGHOST, PGUSER, etc. en .env)
    SQLALCHEMY_DATABASE_URI = _get_db_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}  # PostgreSQL
