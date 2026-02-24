"""Sincronización de feriados desde la librería holidays (Costa Rica y otros)."""
from datetime import date

try:
    import holidays as hl
except ImportError:
    hl = None


def sync_holidays(db_session, country_code="CR", years=None):
    """
    Sincroniza feriados en la base de datos.
    Usa la librería 'holidays' que incluye datos oficiales.
    years: lista de años a sincronizar, ej. [2024, 2025, 2026]
    """
    from models import Holiday

    if not hl:
        return 0, "Instala la librería: pip install holidays"

    if years is None:
        today = date.today()
        years = [today.year, today.year + 1]

    try:
        country_holidays = hl.country_holidays(country_code, years=years, language="es")
    except Exception as e:
        return 0, str(e)

    added = 0
    for d, name in sorted(country_holidays.items()):
        existing = Holiday.query.filter_by(date=d, country_code=country_code).first()
        if not existing:
            h = Holiday(date=d, name=name or "Feriado", country_code=country_code, year=d.year)
            db_session.add(h)
            added += 1
        else:
            existing.name = name or existing.name

    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        return 0, str(e)

    return added, None
