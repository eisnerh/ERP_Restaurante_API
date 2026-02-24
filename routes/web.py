"""Rutas de la interfaz web (aplicación gráfica)."""
from flask import Blueprint, render_template, redirect, url_for

web_bp = Blueprint("web", __name__, template_folder="../templates")


@web_bp.route("/")
def index():
    return render_template("dashboard.html")


@web_bp.route("/menu")
def menu():
    return render_template("menu.html")


@web_bp.route("/mesas")
def mesas():
    return render_template("mesas.html")


@web_bp.route("/pedidos")
def pedidos():
    return render_template("pedidos.html")


@web_bp.route("/inventario")
def inventario():
    return render_template("inventario.html")


@web_bp.route("/proveedores")
def proveedores():
    return render_template("proveedores.html")


@web_bp.route("/planilla")
def planilla():
    return render_template("planilla.html")


@web_bp.route("/clientes")
def clientes():
    return render_template("clientes.html")


@web_bp.route("/compras")
def compras():
    return render_template("compras.html")


@web_bp.route("/franquiciados")
def franquiciados():
    return render_template("franquiciados.html")


@web_bp.route("/configuracion")
def configuracion():
    return render_template("configuracion.html")


@web_bp.route("/api")
def api_info():
    """Redirige a la API JSON de información."""
    from flask import jsonify
    from flask import current_app
    # Devolver JSON de la API (misma info que antes en /)
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
            "clients": "/api/clients",
            "purchases": "/api/purchases",
            "payroll_locations": "/api/payroll/locations",
            "payroll_entries": "/api/payroll/entries",
            "payroll_payslips": "/api/payroll/payslips",
        },
    })
