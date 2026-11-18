"""Entradas WSGI y CLI de la aplicación ERP."""
from application import create_app

app = create_app()


if __name__ == "__main__":
    import os
    from pathlib import Path

    cert_dir = Path(__file__).parent / "certs"
    cert_file = cert_dir / "localhost.pem"
    key_file = cert_dir / "localhost-key.pem"

    use_https_cert = os.environ.get("USE_HTTPS_CERT", "").lower() in ("1", "true", "yes")
    use_https_adhoc = os.environ.get("USE_HTTPS", "").lower() in ("1", "true", "yes")

    if use_https_cert and cert_file.exists() and key_file.exists():
        ssl_ctx = (str(cert_file), str(key_file))
        print("Iniciando con HTTPS (certificados locales): https://localhost:5000")
        app.run(debug=True, host="0.0.0.0", port=5000, ssl_context=ssl_ctx)
    elif use_https_adhoc:
        print("Iniciando con HTTPS (adhoc): https://localhost:5000")
        print("Acepta el aviso del navegador la primera vez.")
        app.run(debug=True, host="0.0.0.0", port=5000, ssl_context="adhoc")
    else:
        app.run(debug=True, host="0.0.0.0", port=5000)
