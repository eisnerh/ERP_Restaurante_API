"""API de reportes de ventas y análisis."""
import csv
import io
from datetime import date, timedelta
from decimal import Decimal

from flask import Blueprint, Response, jsonify, request
from sqlalchemy import func

from extensions import db
from models import Category, Dish, Order, OrderItem, OperationalExpense, Invoice, InvoiceItem, Table

reports_bp = Blueprint("reports", __name__, url_prefix="/api/reports")


def _parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(str(s).strip()[:10])
    except ValueError:
        return None


def _get_franchisee_filter():
    from utils.franchisee import get_or_default_franchisee_id
    return get_or_default_franchisee_id()


@reports_bp.route("/sales", methods=["GET"])
def sales_report():
    """Ventas por período para gráficos (desde Orders cobrados)."""
    fid = _get_franchisee_filter()
    if not fid:
        return jsonify({"data": []})

    hasta = _parse_date(request.args.get("hasta")) or date.today()
    desde = _parse_date(request.args.get("desde")) or hasta - timedelta(days=30)

    date_col = func.coalesce(Order.updated_at, Order.created_at)
    rows = (
        db.session.query(
            func.date(date_col).label("fecha"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("total"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Table, Order.table_id == Table.id)
        .filter(
            Table.franchisee_id == fid,
            Order.status == "paid",
            func.date(date_col) >= desde,
            func.date(date_col) <= hasta,
        )
        .group_by(func.date(date_col))
        .order_by("fecha")
        .all()
    )
    return jsonify({"data": [{"date": str(r.fecha), "total": float(r.total or 0)} for r in rows]})


@reports_bp.route("/top-products", methods=["GET"])
def top_products():
    """Platos más vendidos (desde Orders)."""
    fid = _get_franchisee_filter()
    if not fid:
        return jsonify({"data": []})

    hasta = _parse_date(request.args.get("hasta")) or date.today()
    desde = _parse_date(request.args.get("desde")) or hasta - timedelta(days=30)
    limit = min(request.args.get("limit", 10, type=int), 50)

    rows = (
        db.session.query(
            Dish.name.label("nombre"),
            func.sum(OrderItem.quantity).label("cantidad"),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label("monto"),
        )
        .join(OrderItem, OrderItem.dish_id == Dish.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(Table, Order.table_id == Table.id)
        .filter(
            Table.franchisee_id == fid,
            Order.status == "paid",
            func.date(func.coalesce(Order.updated_at, Order.created_at)) >= desde,
            func.date(func.coalesce(Order.updated_at, Order.created_at)) <= hasta,
        )
        .group_by(Dish.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return jsonify({
        "data": [
            {"producto": r.nombre or "Desconocido", "cantidad": float(r.cantidad or 0), "monto": float(r.monto or 0)}
            for r in rows
        ]
    })


@reports_bp.route("/income-vs-expenses", methods=["GET"])
def income_vs_expenses():
    """Ingresos (ventas cobradas) vs gastos operacionales para rentabilidad."""
    fid = _get_franchisee_filter()
    if not fid:
        return jsonify({"ingresos": 0, "gastos": 0, "utilidad_bruta": 0})

    hasta = _parse_date(request.args.get("hasta")) or date.today()
    desde = _parse_date(request.args.get("desde")) or hasta - timedelta(days=30)

    ingresos = (
        db.session.query(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0))
        .join(Order, OrderItem.order_id == Order.id)
        .join(Table, Order.table_id == Table.id)
        .filter(
            Table.franchisee_id == fid,
            Order.status == "paid",
            func.date(func.coalesce(Order.updated_at, Order.created_at)) >= desde,
            func.date(func.coalesce(Order.updated_at, Order.created_at)) <= hasta,
        )
        .scalar() or Decimal("0")
    )
    gastos = (
        db.session.query(func.coalesce(func.sum(OperationalExpense.amount), 0))
        .filter(
            OperationalExpense.franchisee_id == fid,
            func.date(OperationalExpense.created_at) >= desde,
            func.date(OperationalExpense.created_at) <= hasta,
        )
        .scalar() or Decimal("0")
    )
    return jsonify({
        "ingresos": float(ingresos),
        "gastos": float(gastos),
        "utilidad_bruta": float(ingresos - gastos),
    })


@reports_bp.route("/sales-by-payment-type", methods=["GET"])
def sales_by_payment_type():
    """Ventas cobradas por tipo de pago."""
    fid = _get_franchisee_filter()
    if not fid:
        return jsonify({"data": []})

    hasta = _parse_date(request.args.get("hasta")) or date.today()
    desde = _parse_date(request.args.get("desde")) or hasta - timedelta(days=30)

    rows = (
        db.session.query(
            Order.payment_type,
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("total"),
            func.count(Order.id).label("cantidad"),
        )
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Table, Order.table_id == Table.id)
        .filter(
            Table.franchisee_id == fid,
            Order.status == "paid",
            func.date(func.coalesce(Order.updated_at, Order.created_at)) >= desde,
            func.date(func.coalesce(Order.updated_at, Order.created_at)) <= hasta,
        )
        .group_by(Order.payment_type)
        .all()
    )
    labels = {"efectivo": "Efectivo", "sinpe": "Sinpe", "tarjeta_credito": "Tarjeta crédito", "tarjeta_debito": "Tarjeta débito"}
    return jsonify({
        "data": [
            {"tipo": labels.get(r.payment_type or "efectivo", r.payment_type or "Efectivo"), "total": float(r.total or 0), "cantidad": r.cantidad}
            for r in rows
        ]
    })


@reports_bp.route("/sales-by-category", methods=["GET"])
def sales_by_category():
    """
    Ventas cobradas agrupadas por categoría de menú (unidades, monto, % del total).
    Query: ?desde=&hasta=&format=json|csv
    """
    fid = _get_franchisee_filter()
    if not fid:
        return jsonify({"data": [], "total_monto": 0})

    hasta = _parse_date(request.args.get("hasta")) or date.today()
    desde = _parse_date(request.args.get("desde")) or hasta - timedelta(days=30)
    fmt = (request.args.get("format") or "json").lower()
    date_col = func.date(func.coalesce(Order.updated_at, Order.created_at))

    rows = (
        db.session.query(
            Category.id.label("category_id"),
            Category.name.label("categoria"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("unidades"),
            func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).label("monto"),
        )
        .select_from(Category)
        .join(Dish, Dish.category_id == Category.id)
        .join(OrderItem, OrderItem.dish_id == Dish.id)
        .join(Order, OrderItem.order_id == Order.id)
        .join(Table, Order.table_id == Table.id)
        .filter(
            Table.franchisee_id == fid,
            Category.franchisee_id == fid,
            Order.status == "paid",
            date_col >= desde,
            date_col <= hasta,
        )
        .group_by(Category.id, Category.name)
        .order_by(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0).desc())
        .all()
    )

    total_monto = sum(float(r.monto or 0) for r in rows)
    data = []
    for r in rows:
        m = float(r.monto or 0)
        pct = (m / total_monto * 100) if total_monto > 0 else 0.0
        data.append({
            "categoria": r.categoria or "Sin nombre",
            "categoria_id": r.category_id,
            "unidades": int(r.unidades or 0),
            "monto": round(m, 2),
            "porcentaje": round(pct, 2),
        })

    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["Categoría", "Unidades", "Monto", "% del total"])
        for row in data:
            w.writerow([row["categoria"], row["unidades"], row["monto"], row["porcentaje"]])
        w.writerow([])
        total_u = sum(row["unidades"] for row in data)
        w.writerow(["TOTAL", total_u, round(total_monto, 2), 100.0 if total_monto else 0])
        body = "\ufeff" + buf.getvalue()
        return Response(
            body,
            mimetype="text/csv; charset=utf-8",
            headers={"Content-Disposition": "attachment; filename=ventas_por_categoria.csv"},
        )

    return jsonify({
        "data": data,
        "total_monto": round(total_monto, 2),
        "desde": str(desde),
        "hasta": str(hasta),
    })
