"""Aplicación principal: ERP Restaurant - API REST e interfaz web."""
from flask import Flask, jsonify, request
from config import Config
from extensions import db, ma
from routes import menu_bp, orders_bp, tables_bp, inventory_bp, payroll_bp, web_bp
from routes.clients import clients_bp
from routes.purchases import purchases_bp
from routes.settings import settings_bp
from routes.franchisees import franchisees_bp
from routes.expenses import expenses_bp
from routes.holidays import holidays_bp


def create_app(config_class=Config):
    from pathlib import Path
    import sys
    # PyInstaller: sys._MEIPASS = carpeta donde se extraen los archivos del bundle
    if getattr(sys, "frozen", False):
        base = Path(sys._MEIPASS)
    else:
        base = Path(__file__).parent
    app = Flask(__name__, static_folder=str(base / "static"), template_folder=str(base / "templates"))
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
    app.register_blueprint(expenses_bp)
    app.register_blueprint(holidays_bp)

    @app.before_request
    def ensure_default_franchisee():
        """Asegura que al inicio de cada petición haya un franquiciado por defecto en sesión."""
        from flask import request, session, redirect
        from urllib.parse import urlencode
        from utils.franchisee import get_or_default_franchisee_id, set_current_franchisee_id
        # Permitir cambiar franquiciado por query ?franchisee_id=1 (más fiable que fetch)
        q_fid = request.args.get("franchisee_id", type=int)
        if q_fid is not None:
            from models import Franchisee
            f = Franchisee.query.filter_by(id=q_fid, active=True).first()
            if f:
                set_current_franchisee_id(f.id)
                session.permanent = True
                # Redirigir a la misma ruta sin franchisee_id para limpiar la URL
                args = {k: v for k, v in request.args.items() if k != "franchisee_id"}
                target = request.path + ("?" + urlencode(args) if args else "")
                return redirect(target)
        get_or_default_franchisee_id()

    @app.context_processor
    def inject_settings():
        """Inyecta la configuración y franquiciado actual en todas las plantillas."""
        from utils.franchisee import get_or_default_franchisee_id
        from models import AppSettings, Franchisee
        fid = None
        current = None
        franchisees = []
        try:
            fid = get_or_default_franchisee_id()
            current = db.session.get(Franchisee, fid) if fid else None
        except Exception:
            pass
        try:
            franchisees = Franchisee.query.filter_by(active=True).order_by(Franchisee.name).all()
        except Exception:
            pass
        try:
            s = AppSettings.get(franchisee_id=fid) if fid else AppSettings.get(franchisee_id=None)
            app_name = s.app_name or "ERP Raul Castaño"
            app_logo_url = s.logo_url or ""
            app_favicon_url = s.favicon_url or ""
            app_nav_icon = s.nav_icon or ""
        except Exception:
            app_name = "ERP Raul Castaño"
            app_logo_url = app_favicon_url = app_nav_icon = ""
        return {
            "app_name": app_name,
            "app_logo_url": app_logo_url,
            "app_favicon_url": app_favicon_url,
            "app_nav_icon": app_nav_icon,
            "current_franchisee_id": fid,
            "current_franchisee": current,
            "franchisees_list": franchisees,
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

    @app.errorhandler(Exception)
    def handle_exception(err):
        """En rutas /api/ devuelve JSON con el error para facilitar depuración."""
        import traceback
        tb = traceback.format_exc()
        app.logger.exception("Error 500: %s", err)
        if request.path.startswith("/api/"):
            return jsonify({"error": str(err), "traceback": tb if app.debug else None}), 500
        from flask import render_template_string
        return render_template_string(
            "<h1>Error interno</h1><p>{{ err }}</p>{% if debug %}<pre>{{ tb }}</pre>{% endif %}",
            err=str(err), tb=tb, debug=app.debug
        ), 500

    with app.app_context():
        db.create_all()
        from models import Franchisee, Holiday
        if Franchisee.query.count() == 0:
            default = Franchisee(code="001", name="Franquiciado Principal", active=True)
            db.session.add(default)
            db.session.commit()
        # Sincronizar feriados al iniciar (año actual y siguiente)
        try:
            from utils.holidays_sync import sync_holidays
            from datetime import date
            years = [date.today().year, date.today().year + 1]
            sync_holidays(db.session, years=years)
        except Exception:
            pass
        # Tipos de deducción CR por defecto (si no existen) - estándar global
        try:
            from models import DeductionType
            defaults = [
                ("CCSS Trabajador", "Seguro social - aporte trabajador", False, False, 1),
                ("CCSS Patrono", "Seguro social - aporte patrono", False, False, 2),
                ("Día libre intercambiado", "Horas negativas = negociables", True, True, 3),
                ("Incapacidad", "Deducción por incapacidad", False, False, 4),
            ]
            for name, desc, can_neg, is_hrs, order in defaults:
                if not DeductionType.query.filter_by(name=name).first():
                    db.session.add(DeductionType(
                        name=name, description=desc,
                        can_be_negative=can_neg, is_hours_based=is_hrs, display_order=order
                    ))
            db.session.commit()
        except Exception:
            db.session.rollback()

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
