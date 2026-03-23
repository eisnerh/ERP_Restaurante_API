"""API de control de gastos: compras (inventario), planilla y caja chica por período."""
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from models import PurchaseOrder, Payslip, OperationalExpense
from utils.franchisee import get_or_default_franchisee_id

expenses_bp = Blueprint("expenses", __name__, url_prefix="/api/expenses")


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(str(s).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


@expenses_bp.route("/summary", methods=["GET"])
def expenses_summary():
    """
    Resumen de gastos por período (fecha planilla).
    Query: from=YYYY-MM-DD&to=YYYY-MM-DD
    Devuelve: compras (inventario), planilla, total.
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({
            "purchases_total": 0,
            "payroll_total": 0,
            "operational_total": 0,
            "total": 0,
            "period_from": None,
            "period_to": None,
            "purchases_count": 0,
            "payroll_count": 0,
            "operational_count": 0,
        })

    date_from = _parse_date(request.args.get("from"))
    date_to = _parse_date(request.args.get("to"))

    if not date_from:
        date_from = datetime.utcnow().date().replace(day=1)
    if not date_to:
        date_to = datetime.utcnow().date()

    if date_from > date_to:
        date_from, date_to = date_to, date_from

    # Compras: órdenes recibidas/enviadas con order_date en el rango
    purchases_query = PurchaseOrder.query.filter_by(franchisee_id=fid).filter(
        PurchaseOrder.status.in_(["received", "sent"]),
        PurchaseOrder.order_date >= datetime.combine(date_from, datetime.min.time()),
        PurchaseOrder.order_date < datetime.combine(date_to, datetime.min.time()) + timedelta(days=1),
    )
    purchases = purchases_query.all()
    purchases_total = sum(o.total or 0 for o in purchases)

    # Planilla: payslips cuyo período se solapa con el rango
    # (period_start <= date_to AND period_end >= date_from)
    payroll_query = Payslip.query.filter_by(franchisee_id=fid).filter(
        Payslip.period_end >= date_from,
        Payslip.period_start <= date_to,
    )
    payslips = payroll_query.all()
    payroll_total = sum(p.total_depositado or 0 for p in payslips)

    # Gastos de caja chica (operational expenses): created_at en el rango
    operational_query = OperationalExpense.query.filter_by(franchisee_id=fid).filter(
        OperationalExpense.created_at >= datetime.combine(date_from, datetime.min.time()),
        OperationalExpense.created_at < datetime.combine(date_to, datetime.min.time()) + timedelta(days=1),
    )
    operational = operational_query.all()
    operational_total = sum(float(e.amount or 0) for e in operational)

    return jsonify({
        "purchases_total": round(purchases_total, 2),
        "payroll_total": round(payroll_total, 2),
        "operational_total": round(operational_total, 2),
        "total": round(purchases_total + payroll_total + operational_total, 2),
        "period_from": date_from.isoformat(),
        "period_to": date_to.isoformat(),
        "purchases_count": len(purchases),
        "payroll_count": len(payslips),
        "operational_count": len(operational),
    })


@expenses_bp.route("/periods", methods=["GET"])
def list_periods():
    """
    Lista períodos sugeridos (quincenas) de inicio a fin de año.
    Query: year=2025 (año, default: actual)
    """
    import calendar
    today = datetime.utcnow().date()
    year = request.args.get("year", today.year, type=int)
    year = max(2020, min(2030, year))
    periods = []
    _meses = ("Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic")
    for month in range(1, 13):
        ref = today.replace(year=year, month=month, day=1)
        last_day = calendar.monthrange(ref.year, ref.month)[1]
        p1_start = ref.replace(day=1)
        p1_end = ref.replace(day=15)
        p2_start = ref.replace(day=16)
        p2_end = ref.replace(day=last_day)
        mes = _meses[ref.month - 1] if ref.month <= 12 else str(ref.month)
        periods.append({
            "label": f"Quincena 1 ({p1_start.day:02d}-{p1_end.day:02d} {mes} {ref.year})",
            "from": p1_start.isoformat(),
            "to": p1_end.isoformat(),
        })
        periods.append({
            "label": f"Quincena 2 ({p2_start.day:02d}-{p2_end.day:02d} {mes} {ref.year})",
            "from": p2_start.isoformat(),
            "to": p2_end.isoformat(),
        })
    return jsonify({"periods": periods, "year": year})
