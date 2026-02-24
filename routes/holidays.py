"""API de feriados (días festivos)."""
from datetime import date, datetime
from flask import Blueprint, request, jsonify

from extensions import db
from models import Holiday
from utils.holidays_sync import sync_holidays

holidays_bp = Blueprint("holidays", __name__, url_prefix="/api/holidays")


def _parse_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(str(s).strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


@holidays_bp.route("", methods=["GET"])
def list_holidays():
    """
    Lista feriados.
    Query: year=2025, from=YYYY-MM-DD, to=YYYY-MM-DD, country=CR
    """
    year = request.args.get("year", type=int)
    date_from = _parse_date(request.args.get("from"))
    date_to = _parse_date(request.args.get("to"))
    country = request.args.get("country", "CR").strip() or "CR"

    query = Holiday.query.filter_by(country_code=country)
    if year:
        query = query.filter_by(year=year)
    if date_from:
        query = query.filter(Holiday.date >= date_from)
    if date_to:
        query = query.filter(Holiday.date <= date_to)
    items = query.order_by(Holiday.date).all()
    return jsonify([{
        "id": h.id,
        "date": h.date.isoformat() if h.date else None,
        "name": h.name,
        "country_code": h.country_code,
    } for h in items])


@holidays_bp.route("/sync", methods=["POST"])
def sync():
    """
    Sincroniza feriados desde la fuente oficial (librería holidays).
    Body: years=[2024,2025,2026], country=CR
    """
    data = request.get_json() or {}
    years = data.get("years")
    if years is None:
        today = date.today()
        years = [today.year, today.year + 1]
    country = data.get("country", "CR")
    added, err = sync_holidays(db.session, country_code=country, years=years)
    if err:
        return jsonify({"error": err}), 400
    return jsonify({"message": f"Sincronizados {added} feriados", "added": added})


@holidays_bp.route("/is-holiday", methods=["GET"])
def is_holiday():
    """Comprueba si una fecha es feriado. Query: date=YYYY-MM-DD, country=CR"""
    d = _parse_date(request.args.get("date"))
    country = request.args.get("country", "CR")
    if not d:
        return jsonify({"is_holiday": False, "holiday": None})
    h = Holiday.query.filter_by(date=d, country_code=country).first()
    return jsonify({
        "is_holiday": h is not None,
        "holiday": {"date": h.date.isoformat(), "name": h.name} if h else None,
    })
