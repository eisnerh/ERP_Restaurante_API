"""Rutas de la interfaz web (aplicación gráfica)."""
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, request

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


@web_bp.route("/control-gastos")
def control_gastos():
    return render_template("control_gastos.html")


@web_bp.route("/clientes")
def clientes():
    return render_template("clientes.html")


@web_bp.route("/compras")
def compras():
    return render_template("compras.html")


@web_bp.route("/compras/reporte")
def compras_reporte():
    """Reporte imprimible de pedidos (cuándo y cuánto se ordenó)."""
    from utils.franchisee import get_or_default_franchisee_id
    from models import PurchaseOrder, Supplier

    fid = get_or_default_franchisee_id()
    if not fid:
        return render_template("compras_reporte.html", orders=[], date_from="", date_to="", supplier_id=None, suppliers=[], supplier_name="")

    date_from = request.args.get("from", "")
    date_to = request.args.get("to", "")
    supplier_id = request.args.get("supplier_id", type=int)
    suppliers = Supplier.query.filter_by(franchisee_id=fid).order_by(Supplier.name).all()

    query = PurchaseOrder.query.filter_by(franchisee_id=fid).filter(
        PurchaseOrder.status.in_(["received", "sent"])
    ).order_by(PurchaseOrder.order_date.desc())
    if supplier_id:
        query = query.filter_by(supplier_id=supplier_id)
    if date_from:
        try:
            d = datetime.strptime(date_from, "%Y-%m-%d")
            query = query.filter(PurchaseOrder.order_date >= d)
        except ValueError:
            pass
    if date_to:
        try:
            d = datetime.strptime(date_to, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(PurchaseOrder.order_date < d)
        except ValueError:
            pass
    orders = query.all()
    supplier_name = ""
    if supplier_id:
        s = next((x for x in suppliers if x.id == supplier_id), None)
        supplier_name = s.name if s else ""
    return render_template(
        "compras_reporte.html",
        orders=orders,
        date_from=date_from,
        date_to=date_to,
        supplier_id=supplier_id,
        suppliers=suppliers,
        supplier_name=supplier_name,
    )


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
