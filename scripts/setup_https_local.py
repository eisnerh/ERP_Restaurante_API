"""
Genera certificados HTTPS para localhost sin aviso de "conexion no segura".
Requiere mkcert: https://github.com/FiloSottile/mkcert

1. Instalar mkcert (Windows con Chocolatey: choco install mkcert)
   O descargar desde: https://github.com/FiloSottile/mkcert/releases

2. Ejecutar una vez: mkcert -install

3. Ejecutar este script para generar los certificados:
   python scripts/setup_https_local.py

4. Iniciar la app con HTTPS:
   set USE_HTTPS_CERT=1
   python app.py
"""
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CERT_DIR = PROJECT_ROOT / "certs"
CERT_FILE = CERT_DIR / "localhost.pem"
KEY_FILE = CERT_DIR / "localhost-key.pem"


def main():
    CERT_DIR.mkdir(exist_ok=True)
    if CERT_FILE.exists() and KEY_FILE.exists():
        print(f"Certificados ya existen en {CERT_DIR}")
        print("Para usarlos, inicia con: set USE_HTTPS_CERT=1 && python app.py")
        return

    try:
        result = subprocess.run(
            ["mkcert", "-install"],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print("mkcert -install fallo. Ejecuta manualmente: mkcert -install")
            sys.exit(1)
    except FileNotFoundError:
        print("mkcert no esta instalado.")
        print("Instalacion (Windows): choco install mkcert")
        print("O descarga: https://github.com/FiloSottile/mkcert/releases")
        sys.exit(1)

    subprocess.run(
        ["mkcert", "-key-file", str(KEY_FILE), "-cert-file", str(CERT_FILE), "localhost", "127.0.0.1"],
        check=True,
        cwd=str(PROJECT_ROOT),
    )
    print(f"Certificados creados en {CERT_DIR}")
    print("Inicia con: set USE_HTTPS_CERT=1 && python app.py")
    print("Accede a: https://localhost:5000")


if __name__ == "__main__":
    main()
