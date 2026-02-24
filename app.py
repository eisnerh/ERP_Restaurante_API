"""Aplicación principal: ERP Restaurant - API REST e interfaz web."""
from flask import Flask, jsonify
from config import Config
from extensions import db, ma
from routes import menu_bp, orders_bp, tables_bp, inventory_bp, payroll_bp, web_bp
from routes.clients import clients_bp
from routes.purchases import purchases_bp
from routes.settings import settings_bp
from routes.franchisees import franchisees_bp


def create_app(config_class=Config):
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    db.init_app(app)
    ma.init_app(app)

    app.register_blueprint(web_bp)
    app.register_blueprint(menu_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(tables_bp)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(clients_bp)
    app.register_blueprint(purchases_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(franchisees_bp)

    @app.context_processor
    def inject_settings():
        """Inyecta la configuración y franquiciado actual en todas las plantillas."""
        from utils.franchisee import get_or_default_franchisee_id
        from models import AppSettings, Franchisee
        try:
            fid = get_or_default_franchisee_id()
            s = AppSettings.get(franchisee_id=fid)
            franchisees = Franchisee.query.filter_by(active=True).order_by(Franchisee.name).all()
            current = Franchisee.query.get(fid) if fid else None
            return {
                "app_name": s.app_name or "ERP Raul Castaño",
                "app_logo_url": s.logo_url or "",
                "app_favicon_url": s.favicon_url or "",
                "app_nav_icon": s.nav_icon or "",
                "current_franchisee_id": fid,
                "current_franchisee": current,
                "franchisees_list": franchisees,
            }
        except Exception:
            return {
                "app_name": "ERP Raul Castaño", "app_logo_url": "", "app_favicon_url": "", "app_nav_icon": "",
                "current_franchisee_id": None, "current_franchisee": None, "franchisees_list": [],
            }

    @app.route("/api")
    def api_index():
        """Información de la API en JSON (para clientes que consumen la API)."""
        return jsonify({
            "api": "Restaurant ERP API",
            "version": "2.0",
            "endpoints": {
                "menu": "/api/menu/",
                "categories": "/api/menu/categories",
                "dishes": "/api/menu/dishes",
                "tables": "/api/tables",
                "orders": "/api/orders",
                "inventory": "/api/inventory",
                "suppliers": "/api/inventory/suppliers",
                "clients": "/api/clients",
                "purchases": "/api/purchases",
                "payroll_locations": "/api/payroll/locations",
                "payroll_entries": "/api/payroll/entries",
                "payroll_payslips": "/api/payroll/payslips",
            },
        })

    with app.app_context():
        db.create_all()
        from models import Franchisee
        if Franchisee.query.count() == 0:
            default = Franchisee(code="001", name="Franquiciado Principal", active=True)
            db.session.add(default)
            db.session.commit()

    return app


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
