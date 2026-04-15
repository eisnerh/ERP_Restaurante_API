"""
Servicio de facturación electrónica - Integración Hacienda Costa Rica.
Modo simulación: genera documentos sin enviar a Hacienda.

Llave .p12: ver utils.hacienda_crypto (resolve_hacienda_p12_path, HACIENDA_P12_PATH).
"""
from decimal import Decimal
from typing import List, Dict, Any
from datetime import datetime
import os

# Re-export para quien importe desde hacienda
from utils.hacienda_crypto import (  # noqa: F401
    resolve_hacienda_p12_path,
    list_p12_files,
    get_p12_password,
    get_llave_directory,
)


def is_hacienda_simulation() -> bool:
    """Indica si se usa modo simulación (sin envío a Hacienda)."""
    return os.environ.get("HACIENDA_SIMULATION", "1").lower() in ("1", "true", "yes")


def generar_clave_electronica(
    pais: str = "506",
    dia: str = None,
    mes: str = None,
    anno: str = None,
    cedula: str = "00000000000",
    situacion: str = "1",
    consecutivo: str = "000000000001",
    codigo_seguridad: str = "1",
) -> str:
    """
    Genera clave electrónica para documento fiscal CR.
    Formato: país(3) + día(2) + mes(2) + año(2) + cédula(12) + situación(1) + consecutivo(20) + código(8)
    """
    now = datetime.utcnow()
    dia = dia or f"{now.day:02d}"
    mes = mes or f"{now.month:02d}"
    anno = anno or str(now.year)[-2:]
    return f"{pais}{dia}{mes}{anno}{cedula[:12].zfill(12)}{situacion}{consecutivo.zfill(20)}{codigo_seguridad.zfill(8)}"


def emitir_documento_simulado(
    tipo: str,
    cliente: Dict,
    items: List[Dict],
    total: float,
    subtotal: float,
    consecutivo_num: int = None,
) -> Dict[str, Any]:
    """
    Emite documento en modo simulación.
    Retorna clave, consecutivo, estado sin enviar a Hacienda.
    """
    impuesto = total - subtotal
    if consecutivo_num is None:
        import time
        consecutivo_num = int(time.time() * 1_000_000) % (10 ** 20)
    consecutivo_str = str(consecutivo_num).zfill(20)
    clave = generar_clave_electronica(consecutivo=consecutivo_str)
    now = datetime.utcnow()
    consecutivo = f"001-001-{now.strftime('%y%m%d')}-{consecutivo_num % 10000:04d}"
    return {
        "clave": clave,
        "consecutivo": consecutivo,
        "estado": "aceptado" if is_hacienda_simulation() else "pendiente",
        "simulado": True,
        "total": total,
        "subtotal": subtotal,
        "impuesto": impuesto,
    }


class HaciendaService:
    """Servicio para emisión de documentos electrónicos (simulación o Hacienda real)."""

    def emitir_documento(
        self,
        tipo: str,
        cliente: Any,
        items: List[Dict],
        total: float,
        subtotal: float,
        consecutivo_num: int = None,
    ) -> Dict[str, Any]:
        """Emite documento. En modo simulación no envía a Hacienda."""
        client_dict = {}
        if cliente:
            client_dict = {
                "nombre": getattr(cliente, "name", "Cliente General"),
                "nit": getattr(cliente, "tax_id", None) or "0000000000",
            }
        return emitir_documento_simulado(tipo, client_dict, items, total, subtotal, consecutivo_num)
