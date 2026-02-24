"""API de planilla: trabajos, cargos y importación desde Excel."""
import io
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, Response, send_file
from datetime import date as date_type
from extensions import db
from models import PayrollLocation, PayrollEntry, Payslip, PayslipLine
from schemas import PayrollLocationSchema, PayrollEntrySchema, PayslipSchema
from utils.franchisee import get_or_default_franchisee_id

payroll_bp = Blueprint("payroll", __name__, url_prefix="/api/payroll")

location_schema = PayrollLocationSchema()
locations_schema = PayrollLocationSchema(many=True)
entry_schema = PayrollEntrySchema()
entries_schema = PayrollEntrySchema(many=True)
payslip_schema = PayslipSchema()
payslips_schema = PayslipSchema(many=True)

# Rutas por defecto de Excels de planilla
DEFAULT_PAYROLL_EXCEL = "excel_docs/DATOS DE RABAJOS Y CARGOS ADICIONALES PARA PLANILLA.xlsx"
DEFAULT_PAYSLIP_EXCEL = "excel_docs/PLANILLA RAUL CASTAÑO PLAZA SAN CARLOS.xlsx"


def _to_float(val, default=None):
    if val is None:
        return default
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return default
    m = re.match(r"^([-+]?\d*\.?\d+)", s.replace(",", "."))
    return float(m.group(1)) if m else default


def _to_date(val):
    if val is None:
        return None
    if hasattr(val, "date"):
        return val.date() if hasattr(val, "date") else val
    return None


def _is_header_row(row):
    """Fila de cabecera: col C tipo 'HRS' o 'VALE EFECTIVO', y col D 'CREDITOS COMIDA' o similar."""
    if not row or len(row) < 4:
        return False
    c = str(row[2] or "").strip().upper()
    d = str(row[3] or "").strip().upper()
    return ("HRS" in c or "VALE" in c) and ("CREDITOS" in d or "COMIDA" in d)


def _valid_location_name(s):
    """Nombre de sucursal válido: largo y no es una etiqueta de columna."""
    if not s or len(s) < 4:
        return False
    u = s.upper()
    if u in ("HRS", "HRS EXTRA", "CREDITOS COMIDA", "VALE EFECTIVO", "CCSS", "REBAJOS", "DIA PSG", "INCAPACIDADES", "NUMEROS DE CUENTA", "FECHA INGRESO", "CODIGO"):
        return False
    return True


_MESES = {"ENERO": 1, "FEBRERO": 2, "MARZO": 3, "ABRIL": 4, "MAYO": 5, "JUNIO": 6,
          "JULIO": 7, "AGOSTO": 8, "SEPTIEMBRE": 9, "OCTUBRE": 10, "NOVIEMBRE": 11, "DICIEMBRE": 12}


def _parse_date_from_spanish_text(val):
    """Convierte '1 de FEBRERO 2026' a date."""
    if val is None:
        return None
    s = str(val).strip().upper()
    m = re.search(r"(\d{1,2})\s*DE\s+(ENERO|FEBRERO|MARZO|ABRIL|MAYO|JUNIO|JULIO|AGOSTO|SEPTIEMBRE|OCTUBRE|NOVIEMBRE|DICIEMBRE)\s*(\d{4})", s)
    if m:
        d, mes, y = int(m.group(1)), _MESES.get(m.group(2)), int(m.group(3))
        if mes:
            try:
                return date_type(y, mes, d)
            except ValueError:
                pass
    return None


def _parse_payslip_sheet(ws, location_name, sheet_name):
    """
    Parsea una hoja de desglose de un empleado.
    Devuelve dict con period_start, period_end, position, employee_name, salary_*, total_*, lines[], numero_cuenta.
    """
    rows = list(ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True))
    data = {
        "location_name": location_name,
        "employee_name": (sheet_name or "").strip(),
        "position": None,
        "period_start": None,
        "period_end": None,
        "salary_mes": None, "salary_quincena": None, "salary_semana": None,
        "salary_dia": None, "salary_hora_ordinaria": None, "salary_hora_extra": None,
        "total_asignaciones": None, "total_deducciones": None, "total_depositado": None,
        "numero_cuenta": None,
        "lines": [],
    }
    in_asignaciones = in_deducciones = False
    for i, row in enumerate(rows):
        row = list(row) if row else []
        a = str(row[0] or "").strip().upper()
        b = str(row[1] or "").strip() if len(row) > 1 else ""
        c = row[2] if len(row) > 2 else None
        g = str(row[6] or "").strip().upper() if len(row) > 6 else ""
        h = row[7] if len(row) > 7 else None
        if not data["period_start"] and c and ("FEBRERO" in str(c).upper() or "ENERO" in str(c).upper() or "MARZO" in str(c).upper()):
            data["period_start"] = _parse_date_from_spanish_text(c)
            if i + 1 < len(rows):
                next_c = rows[i + 1][2] if len(rows[i + 1]) > 2 else None
                data["period_end"] = _parse_date_from_spanish_text(next_c) or data["period_start"]
        if "MES" == g and h is not None:
            data["salary_mes"] = _to_float(h)
        if "QUINCENA" in g and h is not None:
            data["salary_quincena"] = _to_float(h)
        if "SEMANA" in g and h is not None:
            data["salary_semana"] = _to_float(h)
        if "DIA" == g and h is not None and "EXTRA" not in a:
            data["salary_dia"] = _to_float(h)
        if "HORA" == g and "EXTRA" not in (str(row[5] or "") + str(row[6] or "")):
            data["salary_hora_ordinaria"] = _to_float(h)
        if "EXTRA" == g and h is not None:
            data["salary_hora_extra"] = _to_float(h)
        if a and ("LIDER" in a or "COLABORADOR" in a or "SUPERVISOR" in a) and b and len(b) > 2:
            data["position"] = (row[0] or "").strip()
            data["employee_name"] = b
        if "ASIGNACIONES" in a:
            in_asignaciones = True
            in_deducciones = False
            continue
        if "DEDUCCIONES" in a:
            in_deducciones = True
            in_asignaciones = False
            continue
        if in_asignaciones and a and "TOTAL" not in a:
            amt = _to_float(c) or _to_float(b)
            qty = _to_float(b) if "HORAS" in a and _to_float(b) is not None else None
            if (row[0] or "").strip():
                data["lines"].append({"line_type": "asignacion", "concept": (row[0] or "").strip(), "amount": amt or 0, "quantity": qty})
        if "TOTAL ASIGNACIONES" in a:
            data["total_asignaciones"] = _to_float(c) or _to_float(b)
            in_asignaciones = False
        if in_deducciones and a and "TOTAL" not in a:
            amt = _to_float(c) or _to_float(b)
            pct = _to_float(b) if b and "CCSS" in a and 0 < (_to_float(b) or 0) < 1 else None
            if (row[0] or "").strip():
                data["lines"].append({"line_type": "deduccion", "concept": (row[0] or "").strip(), "amount": amt or 0, "rate_or_pct": pct})
        if "TOTAL DEDUCCIONES" in a:
            data["total_deducciones"] = _to_float(c) or _to_float(b)
        if "TOTAL DEPOSITADO" in a:
            data["total_depositado"] = _to_float(c) or _to_float(b)
        if len(row) > 8 and row[8] and re.match(r"^CR\d+", str(row[8]).strip().upper()):
            data["numero_cuenta"] = str(row[8]).strip()
    if not data["period_start"]:
        data["period_start"] = date_type(2026, 2, 1)
    if not data["period_end"]:
        data["period_end"] = data["period_start"]
    return data


def _parse_payroll_excel(path):
    """Lee el Excel y devuelve (locations_list, entries_list) o (None, None, error)."""
    try:
        import openpyxl
    except ImportError:
        return None, None, "Instala openpyxl: pip install openpyxl"
    try:
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as e:
        return None, None, str(e)
    ws = wb.active
    locations = []
    entries = []
    current_location_name = None
    rows = list(ws.iter_rows(min_row=1, max_row=ws.max_row, values_only=True))
    prev_row = []
    for i in range(len(rows)):
        row = list(rows[i]) if rows[i] else []
        if _is_header_row(row):
            name_in_header = (row[1] or "").strip()
            name_prev = (prev_row[1] or "").strip() if len(prev_row) > 1 else ""
            loc_name = name_in_header if _valid_location_name(name_in_header) else (name_prev if _valid_location_name(name_prev) else current_location_name)
            if loc_name and loc_name not in [loc.get("name") for loc in locations]:
                locations.append({"name": loc_name, "display_order": len(locations)})
            if loc_name:
                current_location_name = loc_name
            prev_row = row
            continue
        name_b = (row[1] or "").strip()
        if current_location_name and name_b and _valid_location_name(name_b):
            if name_b.upper() in ("MERMAS", "MERMA"):
                entry_type = "mermas"
            else:
                entry_type = "employee"
            hrs = _to_float(row[2] if len(row) > 2 else None)
            creditos = _to_float(row[3] if len(row) > 3 else None, 0)
            vale = _to_float(row[4] if len(row) > 4 else None)
            ccss = _to_float(row[5] if len(row) > 5 else None)
            dia_psg = str(row[6]).strip() if len(row) > 6 and row[6] else None
            incap = str(row[7]).strip() if len(row) > 7 and row[7] else None
            num_cuenta_raw = row[8] if len(row) > 8 else None
            num_cuenta = str(num_cuenta_raw).strip() if num_cuenta_raw is not None else None
            f_ing = _to_date(row[9] if len(row) > 9 else None)
            notes_parts = []
            if len(row) > 4 and row[4] is not None and not isinstance(row[4], (int, float)):
                try:
                    float(str(row[4]).replace(",", "."))
                except ValueError:
                    notes_parts.append(str(row[4]).strip())
            if num_cuenta and not re.match(r"^[A-Za-z0-9\s\-]+$", num_cuenta):
                notes_parts.append(num_cuenta)
                num_cuenta = None
            notes = "; ".join(notes_parts) if notes_parts else None
            entries.append({
                "location_name": current_location_name,
                "employee_name": name_b,
                "entry_type": entry_type,
                "code": str(row[0]).strip() if len(row) > 0 and row[0] else None,
                "hrs_extra": hrs,
                "creditos_comida": creditos,
                "vale_efectivo": vale,
                "ccss_rebajos": ccss,
                "dia_psg": dia_psg,
                "incapacidades": incap,
                "numero_cuenta": num_cuenta,
                "fecha_ingreso": f_ing,
                "notes": notes,
            })
        prev_row = row
    wb.close()
    return locations, entries, None


# ---------- Locations ----------
@payroll_bp.route("/locations", methods=["GET"])
def list_locations():
    fid = get_or_default_franchisee_id()
    query = PayrollLocation.query.filter_by(franchisee_id=fid) if fid else PayrollLocation.query.filter(False)
    locations = query.order_by(PayrollLocation.display_order, PayrollLocation.name).all()
    return jsonify(locations_schema.dump(locations))


@payroll_bp.route("/locations", methods=["POST"])
def create_location():
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    data["franchisee_id"] = fid
    loc = location_schema.load(data, session=db.session)
    db.session.add(loc)
    db.session.commit()
    return jsonify(location_schema.dump(loc)), 201


@payroll_bp.route("/locations/<int:loc_id>", methods=["GET", "PUT", "DELETE"])
def location_detail(loc_id):
    fid = get_or_default_franchisee_id()
    loc = PayrollLocation.query.filter_by(id=loc_id, franchisee_id=fid).first() if fid else None
    if not loc:
        return jsonify({"error": "Ubicación no encontrada"}), 404
    if request.method == "GET":
        return jsonify(location_schema.dump(loc))
    if request.method == "PUT":
        data = request.get_json() or {}
        location_schema.load(data, instance=loc, session=db.session, partial=True)
        db.session.commit()
        return jsonify(location_schema.dump(loc))
    db.session.delete(loc)
    db.session.commit()
    return "", 204


# ---------- Entries ----------
def _parse_date_param(s):
    """Convierte 'YYYY-MM-DD' a date o None."""
    if not s:
        return None
    try:
        return datetime.strptime(s.strip()[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


@payroll_bp.route("/entries", methods=["GET"])
def list_entries():
    """
    Lista registros de planilla.
    Query: location_id=, type=employee|mermas|other,
           period_date=YYYY-MM-DD (una fecha),
           period_date_from=YYYY-MM-DD, period_date_to=YYYY-MM-DD (rango).
    """
    fid = get_or_default_franchisee_id()
    location_id = request.args.get("location_id", type=int)
    entry_type = request.args.get("type")
    period_date = _parse_date_param(request.args.get("period_date"))
    period_date_from = _parse_date_param(request.args.get("period_date_from"))
    period_date_to = _parse_date_param(request.args.get("period_date_to"))
    if not fid:
        return jsonify([])
    loc_ids = [l.id for l in PayrollLocation.query.filter_by(franchisee_id=fid).all()]
    query = PayrollEntry.query.filter(PayrollEntry.location_id.in_(loc_ids)) if loc_ids else PayrollEntry.query.filter(False)
    if location_id is not None:
        if location_id in loc_ids:
            query = query.filter_by(location_id=location_id)
        else:
            query = query.filter(False)
    if entry_type in ("employee", "mermas", "other"):
        query = query.filter_by(entry_type=entry_type)
    if period_date is not None:
        query = query.filter(PayrollEntry.period_date == period_date)
    if period_date_from is not None:
        query = query.filter(PayrollEntry.period_date >= period_date_from)
    if period_date_to is not None:
        query = query.filter(PayrollEntry.period_date <= period_date_to)
    entries = query.order_by(PayrollEntry.period_date.desc(), PayrollEntry.location_id, PayrollEntry.employee_name).all()
    return jsonify(entries_schema.dump(entries))


@payroll_bp.route("/entries/<int:entry_id>", methods=["GET", "PUT", "DELETE"])
def entry_detail(entry_id):
    fid = get_or_default_franchisee_id()
    entry = PayrollEntry.query.get_or_404(entry_id)
    if fid:
        loc = PayrollLocation.query.filter_by(id=entry.location_id, franchisee_id=fid).first()
        if not loc:
            return jsonify({"error": "Registro no encontrado"}), 404
    if request.method == "GET":
        return jsonify(entry_schema.dump(entry))
    if request.method == "PUT":
        data = request.get_json() or {}
        entry_schema.load(data, instance=entry, session=db.session, partial=True)
        db.session.commit()
        return jsonify(entry_schema.dump(entry))
    db.session.delete(entry)
    db.session.commit()
    return "", 204


@payroll_bp.route("/entries", methods=["POST"])
def create_entry():
    """Crea un registro del franquiciado. Incluir period_date (YYYY-MM-DD)."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    if data.get("location_id"):
        loc = PayrollLocation.query.filter_by(id=data["location_id"], franchisee_id=fid).first()
        if not loc:
            return jsonify({"error": "Ubicación no encontrada o no pertenece al franquiciado"}), 400
    if data.get("period_date"):
        if isinstance(data["period_date"], str):
            data["period_date"] = _parse_date_param(data["period_date"])
    entry = entry_schema.load(data, session=db.session)
    db.session.add(entry)
    db.session.commit()
    return jsonify(entry_schema.dump(entry)), 201


@payroll_bp.route("/periods", methods=["GET"])
def list_periods():
    """
    Lista las fechas (periodos) que tienen datos de planilla del franquiciado.
    """
    from sqlalchemy import func
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    loc_ids = [l.id for l in PayrollLocation.query.filter_by(franchisee_id=fid).all()]
    q = db.session.query(PayrollEntry.period_date, func.count(PayrollEntry.id)).filter(
        PayrollEntry.period_date.isnot(None),
    )
    if loc_ids:
        q = q.filter(PayrollEntry.location_id.in_(loc_ids))
    rows = q.group_by(PayrollEntry.period_date).order_by(PayrollEntry.period_date.desc()).limit(100).all()
    return jsonify([
        {"period_date": d.isoformat() if d else None, "entries_count": c}
        for d, c in rows
    ])


# ---------- Import / Export Excel ----------
@payroll_bp.route("/import-excel", methods=["POST"])
def import_payroll_excel():
    """
    Importa desde el Excel DATOS PARA REBAJO Y PAGOS (tiendas y empleados).
    Body: period_date (YYYY-MM-DD) — fecha a la que corresponden estos datos (obligatorio para ingresar por fecha).
          path: ruta opcional al .xlsx.
          replace: si true, borra solo los registros de esa period_date antes de importar (o toda la planilla si no se envía period_date).
          replace_all: si true, borra toda la planilla y todas las ubicaciones antes de importar (como antes).
    """
    import os
    data = request.get_json() or {}
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = data.get("path") or os.path.join(base_dir, DEFAULT_PAYROLL_EXCEL)
    replace = data.get("replace", False)
    replace_all = data.get("replace_all", False)
    period_date = _parse_date_param(data.get("period_date"))
    if not period_date:
        period_date = datetime.utcnow().date()
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    locations_list, entries_list, err = _parse_payroll_excel(path)
    if err:
        return jsonify({"error": err}), 400
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    if replace_all:
        loc_ids = [l.id for l in PayrollLocation.query.filter_by(franchisee_id=fid).all()]
        PayrollEntry.query.filter(PayrollEntry.location_id.in_(loc_ids)).delete(synchronize_session=False)
        PayrollLocation.query.filter_by(franchisee_id=fid).delete()
        db.session.commit()
    elif replace and period_date:
        loc_ids = [l.id for l in PayrollLocation.query.filter_by(franchisee_id=fid).all()]
        PayrollEntry.query.filter(
            PayrollEntry.location_id.in_(loc_ids),
            PayrollEntry.period_date == period_date,
        ).delete(synchronize_session=False)
        db.session.commit()
    name_to_id = {}
    for loc_dict in locations_list:
        name = loc_dict["name"]
        loc = PayrollLocation.query.filter_by(franchisee_id=fid, name=name).first()
        if not loc:
            loc = PayrollLocation(franchisee_id=fid, name=name, display_order=loc_dict.get("display_order", 0))
            db.session.add(loc)
            db.session.flush()
        name_to_id[name] = loc.id
    created = 0
    for e in entries_list:
        loc_id = name_to_id.get(e["location_name"])
        if not loc_id:
            continue
        entry = PayrollEntry(
            location_id=loc_id,
            period_date=period_date,
            employee_name=e["employee_name"],
            entry_type=e.get("entry_type", "employee"),
            code=e.get("code"),
            hrs_extra=e.get("hrs_extra"),
            creditos_comida=e.get("creditos_comida") or 0,
            vale_efectivo=e.get("vale_efectivo"),
            ccss_rebajos=e.get("ccss_rebajos"),
            dia_psg=e.get("dia_psg"),
            incapacidades=e.get("incapacidades"),
            numero_cuenta=e.get("numero_cuenta"),
            fecha_ingreso=e.get("fecha_ingreso"),
            notes=e.get("notes"),
        )
        db.session.add(entry)
        created += 1
    db.session.commit()
    return jsonify({
        "message": "Importación correcta",
        "period_date": period_date.isoformat(),
        "locations": len(locations_list),
        "entries": created,
    }), 200


@payroll_bp.route("/export-excel", methods=["GET"])
def export_payroll_excel():
    """
    Exporta la planilla a un Excel con estructura mejorada.
    Query: period_date=YYYY-MM-DD para exportar solo esa fecha; si no se envía, exporta todos los registros.
    Una hoja por ubicación (tienda), columnas: Fecha Planilla, Código, Empleado, Tipo, Hrs Extra, Créditos Comida, Vale Efectivo, CCSS/Rebajos, Día PSG, Incapacidades, Nº Cuenta, Fecha Ingreso, Notas.
    """
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment
    except ImportError:
        return jsonify({"error": "openpyxl requerido para exportar"}), 500
    period_date = _parse_date_param(request.args.get("period_date"))
    fid = get_or_default_franchisee_id()
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    headers = [
        "Fecha Planilla", "Codigo", "Empleado", "Tipo", "Hrs Extra", "Creditos Comida", "Vale Efectivo",
        "CCSS/Rebajos", "Dia PSG", "Incapacidades", "Numero Cuenta", "Fecha Ingreso", "Notas"
    ]
    query = PayrollLocation.query.filter_by(franchisee_id=fid) if fid else PayrollLocation.query.filter(False)
    locations = query.order_by(PayrollLocation.display_order, PayrollLocation.name).all()
    for loc in locations:
        ws = wb.create_sheet(title=loc.name[:31])
        ws.append(headers)
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center", wrap_text=True)
        q = PayrollEntry.query.filter_by(location_id=loc.id)
        if period_date is not None:
            q = q.filter(PayrollEntry.period_date == period_date)
        entries = q.order_by(PayrollEntry.employee_name).all()
        for e in entries:
            ws.append([
                e.period_date.isoformat() if e.period_date else None,
                e.code,
                e.employee_name,
                e.entry_type,
                e.hrs_extra,
                e.creditos_comida,
                e.vale_efectivo,
                e.ccss_rebajos,
                e.dia_psg,
                e.incapacidades,
                e.numero_cuenta,
                e.fecha_ingreso.isoformat() if e.fecha_ingreso else None,
                e.notes,
            ])
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return send_file(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="planilla_mejorada.xlsx",
    )


# ---------- Desglose de planilla (payslip): salario por mes/quincena/semana/día/hora ----------
def _resolve_payslip_excel_path(base_dir, path_or_none):
    import os
    import glob
    if path_or_none and os.path.isabs(path_or_none):
        return path_or_none
    folder = os.path.join(base_dir, "excel_docs")
    if path_or_none:
        p = os.path.join(base_dir, path_or_none)
        if os.path.isfile(p):
            return p
    for name in os.listdir(folder):
        if name.upper().startswith("PLANILLA") and name.lower().endswith(".xlsx") and "PLAZA" in name.upper():
            return os.path.join(folder, name)
    return os.path.join(base_dir, DEFAULT_PAYSLIP_EXCEL)


@payroll_bp.route("/payslips/summary-pdf", methods=["GET"])
def payslips_summary_pdf():
    """
    Genera un PDF con el resumen de lo pagado en la quincena: lista de colaboradores
    y monto depositado a cada uno, más total general.
    Query: location_name=, period_start=YYYY-MM-DD, period_end=YYYY-MM-DD (obligatorios para el resumen).
    """
    from flask import Response
    from utils.payslip_pdf import build_summary_pdf
    location_name = request.args.get("location_name")
    period_start = _parse_date_param(request.args.get("period_start"))
    period_end = _parse_date_param(request.args.get("period_end"))
    if not location_name:
        return jsonify({"error": "Falta location_name"}), 400
    if not period_start or not period_end:
        return jsonify({"error": "Faltan period_start y period_end (YYYY-MM-DD)"}), 400
    fid = get_or_default_franchisee_id()
    query = Payslip.query.filter(
        Payslip.location_name.ilike(f"%{location_name}%"),
        Payslip.period_start == period_start,
        Payslip.period_end == period_end,
    )
    if fid:
        query = query.filter_by(franchisee_id=fid)
    payslips = query.order_by(Payslip.employee_name).all()
    if not payslips:
        return jsonify({"error": "No hay desgloses para esa ubicación y período"}), 404
    pdf_bytes = build_summary_pdf(payslips, location_name, period_start, period_end)
    filename = f"resumen_planilla_{period_start}_{period_end}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@payroll_bp.route("/payslips", methods=["GET"])
def list_payslips():
    """
    Lista desgloses de pago del franquiciado.
    Query: location_name=, employee_name=, period_start=, period_end= (YYYY-MM-DD).
    """
    fid = get_or_default_franchisee_id()
    location_name = request.args.get("location_name")
    employee_name = request.args.get("employee_name")
    period_start = _parse_date_param(request.args.get("period_start"))
    period_end = _parse_date_param(request.args.get("period_end"))
    query = Payslip.query.filter_by(franchisee_id=fid) if fid else Payslip.query.filter(False)
    if location_name:
        query = query.filter(Payslip.location_name.ilike(f"%{location_name}%"))
    if employee_name:
        query = query.filter(Payslip.employee_name.ilike(f"%{employee_name}%"))
    if period_start:
        query = query.filter(Payslip.period_end >= period_start)
    if period_end:
        query = query.filter(Payslip.period_start <= period_end)
    payslips = query.order_by(Payslip.period_start.desc(), Payslip.employee_name).limit(200).all()
    return jsonify(payslips_schema.dump(payslips))


@payroll_bp.route("/payslips/<int:payslip_id>", methods=["GET"])
def get_payslip(payslip_id):
    """Obtiene un desglose de pago por ID."""
    fid = get_or_default_franchisee_id()
    payslip = Payslip.query.filter_by(id=payslip_id, franchisee_id=fid).first() if fid else None
    if not payslip:
        return jsonify({"error": "Desglose no encontrado"}), 404
    return jsonify(payslip_schema.dump(payslip))


@payroll_bp.route("/payslips/<int:payslip_id>/pdf", methods=["GET"])
def payslip_pdf(payslip_id):
    """
    Genera el PDF del desglose de pago del colaborador para imprimir y firmar.
    """
    from flask import Response
    from utils.payslip_pdf import build_payslip_pdf
    fid = get_or_default_franchisee_id()
    payslip = Payslip.query.filter_by(id=payslip_id, franchisee_id=fid).first() if fid else None
    if not payslip:
        return jsonify({"error": "Desglose no encontrado"}), 404
    pdf_bytes = build_payslip_pdf(payslip)
    safe_name = re.sub(r"[^\w\s\-]", "", payslip.employee_name or "colaborador").replace(" ", "_")[:40]
    filename = f"desglose_{safe_name}_{payslip.period_start}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@payroll_bp.route("/import-payslip-excel", methods=["POST"])
def import_payslip_excel():
    """
    Importa el Excel de desglose de planilla para el franquiciado actual.
    Body: location_name (ej. PLAZA SAN CARLOS), path (opcional). replace: true borra payslips antes de importar.
    """
    import os
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = _resolve_payslip_excel_path(base_dir, data.get("path"))
    location_name = (data.get("location_name") or "PLAZA SAN CARLOS").strip()
    replace = data.get("replace", False)
    if not os.path.isfile(path):
        return jsonify({"error": f"Archivo no encontrado: {path}"}), 400
    try:
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    skip_sheets = ("RESUMEN DE PLANILLA", "RESUMEN")
    created = 0
    for sheet_name in wb.sheetnames:
        if any(skip in sheet_name.upper() for skip in skip_sheets):
            continue
        ws = wb[sheet_name]
        parsed = _parse_payslip_sheet(ws, location_name, sheet_name)
        if not parsed.get("employee_name") or not parsed.get("period_start"):
            continue
        if replace:
            Payslip.query.filter(
                Payslip.franchisee_id == fid,
                Payslip.location_name == location_name,
                Payslip.employee_name == parsed["employee_name"],
                Payslip.period_start == parsed["period_start"],
            ).delete(synchronize_session=False)
        ps = Payslip(
            franchisee_id=fid,
            location_name=parsed["location_name"],
            employee_name=parsed["employee_name"],
            position=parsed.get("position"),
            period_start=parsed["period_start"],
            period_end=parsed["period_end"],
            salary_mes=parsed.get("salary_mes"),
            salary_quincena=parsed.get("salary_quincena"),
            salary_semana=parsed.get("salary_semana"),
            salary_dia=parsed.get("salary_dia"),
            salary_hora_ordinaria=parsed.get("salary_hora_ordinaria"),
            salary_hora_extra=parsed.get("salary_hora_extra"),
            total_asignaciones=parsed.get("total_asignaciones"),
            total_deducciones=parsed.get("total_deducciones"),
            total_depositado=parsed.get("total_depositado"),
            numero_cuenta=parsed.get("numero_cuenta"),
        )
        db.session.add(ps)
        db.session.flush()
        for line in parsed.get("lines", []):
            pl = PayslipLine(
                payslip_id=ps.id,
                line_type=line.get("line_type", "asignacion"),
                concept=line.get("concept", ""),
                amount=line.get("amount", 0),
                quantity=line.get("quantity"),
                rate_or_pct=line.get("rate_or_pct"),
            )
            db.session.add(pl)
        created += 1
    wb.close()
    db.session.commit()
    return jsonify({
        "message": "Importación de desgloses correcta",
        "location_name": location_name,
        "payslips_created": created,
    }), 200
