"""
Punto de entrada para la aplicación (usado por PyInstaller al crear el ejecutable).
"""
import sys
import os

# PyInstaller: cuando está empaquetado, el directorio base es el del ejecutable
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Cargar .env desde el directorio del ejecutable (o del proyecto)
os.chdir(BASE_DIR)
env_path = os.path.join(BASE_DIR, ".env")
if os.path.exists(env_path):
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path, encoding="utf-8", override=True)
    except Exception:
        pass

# Importar y ejecutar la app
from app import app

if __name__ == "__main__":
    import os
    from pathlib import Path

    cert_dir = Path(BASE_DIR) / "certs"
    cert_file = cert_dir / "localhost.pem"
    key_file = cert_dir / "localhost-key.pem"

    use_https_cert = os.environ.get("USE_HTTPS_CERT", "").lower() in ("1", "true", "yes")
    use_https_adhoc = os.environ.get("USE_HTTPS", "").lower() in ("1", "true", "yes")

    port = int(os.environ.get("PORT", "5000"))
    host = os.environ.get("HOST", "0.0.0.0")

    print(f"ERP Restaurant - http://localhost:{port}")
    print("Presiona Ctrl+C para detener.\n")

    if use_https_cert and cert_file.exists() and key_file.exists():
        app.run(debug=False, host=host, port=port, ssl_context=(str(cert_file), str(key_file)))
    elif use_https_adhoc:
        app.run(debug=False, host=host, port=port, ssl_context="adhoc")
    else:
        app.run(debug=False, host=host, port=port)
