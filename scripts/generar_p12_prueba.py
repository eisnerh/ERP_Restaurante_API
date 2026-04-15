"""
Genera un certificado .p12 de PRUEBA local (autofirmado) en data/Llave/prueba-local.p12.

No sirve para enviar a Hacienda CR en producción; solo para probar que la app encuentra
un archivo .12 y que la contraseña encaja.

Requisito: OpenSSL en PATH (Git for Windows incluye openssl.exe).

Uso:
  python scripts/generar_p12_prueba.py
  python scripts/generar_p12_prueba.py --password miClave
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LLAVE = PROJECT_ROOT / "data" / "Llave"
DEFAULT_OUT = LLAVE / "prueba-local.p12"
DEFAULT_PASS = "prueba-local"


def main():
    parser = argparse.ArgumentParser(description="Genera .p12 de prueba (OpenSSL requerido)")
    parser.add_argument("--password", default=DEFAULT_PASS, help=f"Contraseña del p12 (default: {DEFAULT_PASS})")
    parser.add_argument("--output", type=Path, default=None, help="Ruta del .p12 de salida")
    args = parser.parse_args()
    out = Path(args.output) if args.output else DEFAULT_OUT

    openssl = shutil.which("openssl")
    if not openssl:
        print("No se encontró 'openssl' en PATH.", file=sys.stderr)
        print("Instala Git for Windows o OpenSSL y vuelve a intentar.", file=sys.stderr)
        sys.exit(1)

    LLAVE.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        key_pem = t / "key.pem"
        cert_pem = t / "cert.pem"
        # Certificado autofirmado de prueba
        subprocess.run(
            [
                openssl, "req", "-x509", "-newkey", "rsa:2048",
                "-keyout", str(key_pem), "-out", str(cert_pem),
                "-days", "3650", "-nodes",
                "-subj", "/CN=Prueba local ERP/O=Desarrollo/C=CR",
            ],
            check=True,
            capture_output=True,
        )
        # PKCS#12
        env = {**os.environ, "OPENSSL_CONF": ""}
        p = subprocess.run(
            [
                openssl, "pkcs12", "-export",
                "-out", str(out),
                "-inkey", str(key_pem),
                "-in", str(cert_pem),
                "-password", f"pass:{args.password}",
            ],
            env=env,
            capture_output=True,
            text=True,
        )
        if p.returncode != 0:
            print(p.stderr or p.stdout or "Error pkcs12", file=sys.stderr)
            sys.exit(1)

    print(f"Listo: {out}")
    print(f"Contraseña: {args.password}")
    print("En .env añade (sin commitear .env):")
    print(f"  HACIENDA_P12_PASSWORD={args.password}")
    if out.name:
        print("En Configuración elige el archivo o deja automático si es el único .p12.")


if __name__ == "__main__":
    main()
