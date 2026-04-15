"""
Resolución dinámica de la llave criptográfica (.p12) para Hacienda.

Prioridad:
1. Variable de entorno HACIENDA_P12_PATH (ruta absoluta al archivo)
2. app_settings.hacienda_p12_filename dentro de data/Llave/
3. Primer archivo *.p12 encontrado en data/Llave/

Contraseña del .p12: use HACIENDA_P12_PASSWORD en .env (no se guarda en BD).
"""
import os
from pathlib import Path
from typing import List, Optional

# Raíz del proyecto (carpeta que contiene app.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LLAVE_DIR = PROJECT_ROOT / "data" / "Llave"


def get_llave_directory() -> Path:
    return LLAVE_DIR


def list_p12_files() -> List[str]:
    """Lista nombres de archivos .p12 en data/Llave (ordenados)."""
    if not LLAVE_DIR.is_dir():
        return []
    return sorted({p.name for p in LLAVE_DIR.glob("*.p12")})


def _safe_p12_path(filename: str) -> Optional[Path]:
    """Devuelve Path solo si el archivo está dentro de data/Llave."""
    if not filename or not filename.strip():
        return None
    name = filename.strip()
    if ".." in name or "/" in name or "\\" in name:
        return None
    base = LLAVE_DIR.resolve()
    candidate = (LLAVE_DIR / name).resolve()
    try:
        candidate.relative_to(base)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def resolve_hacienda_p12_path(franchisee_id: Optional[int] = None) -> Optional[Path]:
    """
    Ruta absoluta al .p12 activo, o None si no hay ninguno.
    franchisee_id: si se pasa, usa AppSettings de ese franquiciado.
    """
    env = os.environ.get("HACIENDA_P12_PATH", "").strip()
    if env:
        p = Path(env)
        if p.is_file():
            return p.resolve()

    fname = None
    try:
        from models import AppSettings
        s = AppSettings.get(franchisee_id=franchisee_id)
        fname = getattr(s, "hacienda_p12_filename", None)
    except Exception:
        pass

    if fname:
        safe = _safe_p12_path(fname)
        if safe:
            return safe

    available = list_p12_files()
    if available:
        return _safe_p12_path(available[0])
    return None


def get_p12_password() -> str:
    """Contraseña del .p12 (solo entorno; nunca en BD)."""
    return os.environ.get("HACIENDA_P12_PASSWORD", "").strip()
