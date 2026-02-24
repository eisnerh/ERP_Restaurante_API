"""API de planilla: trabajos, cargos y importación desde Excel."""
import io
import re
from datetime import datetime, date as date_type
from flask import Blueprint, request, jsonify, Response, send_file
from extensions import db
from models import PayrollLocation, PayrollEntry, Payslip, PayslipLine, Employee, Position, DeductionType, VacationRecord, PaymentRecord
from schemas import PayrollLocationSchema, PayrollEntrySchema, PayslipSchema, EmployeeSchema, PositionSchema, DeductionTypeSchema, VacationRecordSchema, PaymentRecordSchema
from utils.franchisee import get_or_default_franchisee_id

payroll_bp = Blueprint("payroll", __name__, url_prefix="/api/payroll")

location_schema = PayrollLocationSchema()
locations_schema = PayrollLocationSchema(many=True)
entry_schema = PayrollEntrySchema()
entries_schema = PayrollEntrySchema(many=True)
employee_schema = EmployeeSchema()
employees_schema = EmployeeSchema(many=True)
position_schema = PositionSchema()
positions_schema = PositionSchema(many=True)
deduction_type_schema = DeductionTypeSchema()
deduction_types_schema = DeductionTypeSchema(many=True)
vacation_record_schema = VacationRecordSchema()
vacation_records_schema = VacationRecordSchema(many=True)
payslip_schema = PayslipSchema()
payslips_schema = PayslipSchema(many=True)
payment_record_schema = PaymentRecordSchema()
payment_records_schema = PaymentRecordSchema(many=True)

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
                entry_type = "empleado"
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
def _ensure_default_location(fid):
    """Si el franquiciado no tiene ubicaciones, crea una con el nombre del franquiciado."""
    if not fid:
        return
    from models import Franchisee
    count = PayrollLocation.query.filter_by(franchisee_id=fid).count()
    if count > 0:
        return
    f = db.session.get(Franchisee, fid)
    if not f or not f.name:
        return
    loc = PayrollLocation(franchisee_id=fid, name=f.name.strip(), display_order=0)
    db.session.add(loc)
    db.session.commit()


@payroll_bp.route("/locations", methods=["GET"])
def list_locations():
    fid = get_or_default_franchisee_id()
    if fid:
        _ensure_default_location(fid)
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


def _parse_date_param(s):
    """Convierte 'YYYY-MM-DD' a date o None."""
    if not s:
        return None
    try:
        return datetime.strptime(str(s).strip()[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


# ---------- Employees ----------
@payroll_bp.route("/employees", methods=["GET"])
def list_employees():
    """Lista empleados del franquiciado actual."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    location_id = request.args.get("location_id", type=int)
    active_only = request.args.get("active", "1").lower() in ("1", "true", "yes")
    query = Employee.query.filter_by(franchisee_id=fid)
    if active_only:
        query = query.filter_by(active=True)
    if location_id is not None:
        query = query.filter_by(location_id=location_id)
    employees = query.order_by(Employee.name).all()
    return jsonify(employees_schema.dump(employees))


@payroll_bp.route("/employees", methods=["POST"])
def create_employee():
    """Crea un empleado del franquiciado."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    if data.get("location_id"):
        loc = PayrollLocation.query.filter_by(id=data["location_id"], franchisee_id=fid).first()
        if not loc:
            return jsonify({"error": "Ubicación no encontrada"}), 400
    data["franchisee_id"] = fid
    for f in ("fecha_ingreso", "fecha_salida"):
        if f in data:
            parsed = _parse_date_param(data[f]) if data[f] else None
            if parsed is not None:
                data[f] = parsed
            else:
                data.pop(f, None)  # Quitar clave para que el esquema no intente deserializar
    # Contrato indefinido: fecha_salida = fecha_ingreso + 99 años (efectivamente sin fin)
    if data.get("tipo_contrato") == "indefinido" and "fecha_salida" not in data:
        base = data.get("fecha_ingreso") or date_type.today()
        try:
            data["fecha_salida"] = base.replace(year=base.year + 99)
        except ValueError:  # 29 feb en año no bisiesto
            data["fecha_salida"] = base.replace(year=base.year + 99, day=28)
    emp = employee_schema.load(data, session=db.session)
    db.session.add(emp)
    db.session.commit()
    return jsonify(employee_schema.dump(emp)), 201


@payroll_bp.route("/employees/<int:emp_id>", methods=["GET", "PUT", "DELETE"])
def employee_detail(emp_id):
    fid = get_or_default_franchisee_id()
    emp = Employee.query.filter_by(id=emp_id, franchisee_id=fid).first() if fid else None
    if not emp:
        return jsonify({"error": "Empleado no encontrado"}), 404
    if request.method == "GET":
        return jsonify(employee_schema.dump(emp))
    if request.method == "PUT":
        data = request.get_json() or {}
        for f in ("fecha_ingreso", "fecha_salida"):
            if f in data:
                parsed = _parse_date_param(data[f]) if data[f] else None
                if parsed is not None:
                    data[f] = parsed
                else:
                    data[f] = None  # En PUT parcial, pasar None para limpiar el campo
        # Contrato indefinido: fecha_salida = fecha_ingreso + 99 años
        tipo = data.get("tipo_contrato") or emp.tipo_contrato
        if tipo == "indefinido" and (data.get("fecha_salida") is None or "fecha_salida" not in data):
            base = data.get("fecha_ingreso") or emp.fecha_ingreso or date_type.today()
            try:
                data["fecha_salida"] = base.replace(year=base.year + 99)
            except ValueError:
                data["fecha_salida"] = base.replace(year=base.year + 99, day=28)
        employee_schema.load(data, instance=emp, session=db.session, partial=True)
        db.session.commit()
        return jsonify(employee_schema.dump(emp))
    db.session.delete(emp)
    db.session.commit()
    return "", 204


@payroll_bp.route("/employees/<int:emp_id>/report", methods=["GET"])
def employee_report(emp_id):
    """
    Reporte por empleado: pagos realizados y deducciones aplicadas.
    Query: from_date=YYYY-MM-DD, to_date=YYYY-MM-DD (opcional).
    """
    fid = get_or_default_franchisee_id()
    emp = Employee.query.filter_by(id=emp_id, franchisee_id=fid).first() if fid else None
    if not emp:
        return jsonify({"error": "Empleado no encontrado"}), 404
    from_date = _parse_date_param(request.args.get("from_date"))
    to_date = _parse_date_param(request.args.get("to_date"))

    # Pagos registrados (PaymentRecord)
    pay_query = PaymentRecord.query.filter_by(employee_id=emp_id, franchisee_id=fid)
    if from_date:
        pay_query = pay_query.filter(PaymentRecord.payment_date >= from_date)
    if to_date:
        pay_query = pay_query.filter(PaymentRecord.payment_date <= to_date)
    payments = pay_query.order_by(PaymentRecord.payment_date.desc()).all()

    # Desgloses (Payslips) para deducciones - por employee_id o por nombre (legacy)
    emp_name = (emp.name or "").strip()
    ps_query = Payslip.query.filter(
        Payslip.franchisee_id == fid,
        db.or_(
            Payslip.employee_id == emp_id,
            (Payslip.employee_id.is_(None)) & (Payslip.employee_name.ilike(emp_name)) if emp_name else (Payslip.id < 0),
        ),
    )
    if from_date:
        ps_query = ps_query.filter(Payslip.period_end >= from_date)
    if to_date:
        ps_query = ps_query.filter(Payslip.period_start <= to_date)
    payslips = ps_query.order_by(Payslip.period_start.desc()).all()

    # Deducciones por concepto (agregadas de todos los payslips)
    deductions_by_concept = {}
    for ps in payslips:
        for line in ps.lines:
            if line.line_type == "deduccion" and line.concept:
                key = (line.concept.strip() or "Otro")[:80]
                deductions_by_concept[key] = deductions_by_concept.get(key, 0) + (line.amount or 0)

    total_paid = sum((p.amount or 0) for p in payments)
    total_deductions = sum(deductions_by_concept.values())

    return jsonify({
        "employee": employee_schema.dump(emp),
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None,
        "payments": [
            {
                "id": p.id,
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "amount": p.amount,
                "periodo_tipo": p.periodo_tipo,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
                "hours_worked": p.hours_worked,
                "days_worked": p.days_worked,
                "location_name": p.location.name if p.location else None,
            }
            for p in payments
        ],
        "payslips": [
            {
                "id": ps.id,
                "period_start": ps.period_start.isoformat() if ps.period_start else None,
                "period_end": ps.period_end.isoformat() if ps.period_end else None,
                "location_name": ps.location_name,
                "total_asignaciones": ps.total_asignaciones,
                "total_deducciones": ps.total_deducciones,
                "total_depositado": ps.total_depositado,
                "deductions": [
                    {"concept": pl.concept, "amount": pl.amount}
                    for pl in ps.lines if pl.line_type == "deduccion"
                ],
            }
            for ps in payslips
        ],
        "deductions_summary": [{"concept": k, "total": v} for k, v in sorted(deductions_by_concept.items())],
        "total_paid": round(total_paid, 2),
        "total_deductions": round(total_deductions, 2),
        "net": round(total_paid - total_deductions, 2),
    })


@payroll_bp.route("/employees/<int:emp_id>/report-pdf", methods=["GET"])
def employee_report_pdf(emp_id):
    """Genera PDF del reporte por empleado. Query: from_date=, to_date= (opcional)."""
    from flask import Response
    from utils.payslip_pdf import build_employee_report_pdf
    fid = get_or_default_franchisee_id()
    emp = Employee.query.filter_by(id=emp_id, franchisee_id=fid).first() if fid else None
    if not emp:
        return jsonify({"error": "Empleado no encontrado"}), 404
    from_date = _parse_date_param(request.args.get("from_date"))
    to_date = _parse_date_param(request.args.get("to_date"))

    pay_query = PaymentRecord.query.filter_by(employee_id=emp_id, franchisee_id=fid)
    if from_date:
        pay_query = pay_query.filter(PaymentRecord.payment_date >= from_date)
    if to_date:
        pay_query = pay_query.filter(PaymentRecord.payment_date <= to_date)
    payments = pay_query.order_by(PaymentRecord.payment_date.desc()).all()

    emp_name = (emp.name or "").strip()
    ps_query = Payslip.query.filter(
        Payslip.franchisee_id == fid,
        db.or_(
            Payslip.employee_id == emp_id,
            (Payslip.employee_id.is_(None)) & (Payslip.employee_name.ilike(emp_name)) if emp_name else (Payslip.id < 0),
        ),
    )
    if from_date:
        ps_query = ps_query.filter(Payslip.period_end >= from_date)
    if to_date:
        ps_query = ps_query.filter(Payslip.period_start <= to_date)
    payslips = ps_query.order_by(Payslip.period_start.desc()).all()

    deductions_by_concept = {}
    for ps in payslips:
        for line in ps.lines:
            if line.line_type == "deduccion" and line.concept:
                key = (line.concept.strip() or "Otro")[:80]
                deductions_by_concept[key] = deductions_by_concept.get(key, 0) + (line.amount or 0)

    total_paid = sum((p.amount or 0) for p in payments)
    total_deductions = sum(deductions_by_concept.values())

    report_data = {
        "employee": employee_schema.dump(emp),
        "from_date": from_date.isoformat() if from_date else None,
        "to_date": to_date.isoformat() if to_date else None,
        "payments": [
            {
                "payment_date": p.payment_date.isoformat() if p.payment_date else None,
                "amount": p.amount,
                "periodo_tipo": p.periodo_tipo,
                "period_start": p.period_start.isoformat() if p.period_start else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
                "hours_worked": p.hours_worked,
                "days_worked": p.days_worked,
                "location_name": p.location.name if p.location else None,
            }
            for p in payments
        ],
        "deductions_summary": [{"concept": k, "total": v} for k, v in sorted(deductions_by_concept.items())],
        "total_paid": round(total_paid, 2),
        "total_deductions": round(total_deductions, 2),
        "net": round(total_paid - total_deductions, 2),
    }
    pdf_bytes = build_employee_report_pdf(report_data)
    f_str = (from_date.isoformat() if from_date else "all")
    t_str = (to_date.isoformat() if to_date else "all")
    filename = f"reporte_empleado_{emp_id}_{f_str}_{t_str}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


@payroll_bp.route("/employees/<int:emp_id>/vacation-records", methods=["GET", "POST"])
def employee_vacation_records(emp_id):
    """Lista o registra vacaciones tomadas. POST: {fecha_desde, fecha_hasta, dias_tomados, tipo, notes}."""
    fid = get_or_default_franchisee_id()
    emp = Employee.query.filter_by(id=emp_id, franchisee_id=fid).first() if fid else None
    if not emp:
        return jsonify({"error": "Empleado no encontrado"}), 404
    if request.method == "GET":
        records = VacationRecord.query.filter_by(employee_id=emp_id).order_by(VacationRecord.fecha_desde.desc()).all()
        return jsonify(vacation_records_schema.dump(records))
    data = request.get_json() or {}
    data["employee_id"] = emp_id
    for f in ("fecha_desde", "fecha_hasta"):
        if f in data:
            data[f] = _parse_date_param(data[f]) if data[f] else None
    rec = vacation_record_schema.load(data, session=db.session)
    db.session.add(rec)
    # Los días se deducen automáticamente desde vacation_records (Employee.vacation_days)
    db.session.commit()
    return jsonify(vacation_record_schema.dump(rec)), 201


# ---------- Positions (Puestos) - estándar global ----------
@payroll_bp.route("/positions", methods=["GET"])
def list_positions():
    """Lista puestos estándar. Tipos: empleado, administrador, administrativo, inventario, custom."""
    position_type = request.args.get("type")  # Filtrar por tipo
    query = Position.query
    if position_type in ("empleado", "administrador", "administrativo", "inventario", "custom"):
        query = query.filter_by(position_type=position_type)
    positions = query.order_by(Position.display_order, Position.name).all()
    return jsonify(positions_schema.dump(positions))


@payroll_bp.route("/positions", methods=["POST"])
def create_position():
    """Crea un puesto estándar. position_type: empleado|administrador|administrativo|inventario|custom."""
    data = request.get_json() or {}
    if not data.get("position_type"):
        data["position_type"] = "empleado"
    if data["position_type"] not in ("empleado", "administrador", "administrativo", "inventario", "custom"):
        data["position_type"] = "custom"
    pos = position_schema.load(data, session=db.session)
    db.session.add(pos)
    db.session.commit()
    return jsonify(position_schema.dump(pos)), 201


@payroll_bp.route("/positions/<int:pos_id>", methods=["GET", "PUT", "DELETE"])
def position_detail(pos_id):
    pos = Position.query.get(pos_id)
    if not pos:
        return jsonify({"error": "Puesto no encontrado"}), 404
    if request.method == "GET":
        data = position_schema.dump(pos)
        breakdown = pos.get_salary_breakdown()
        if breakdown:
            data["salary_breakdown"] = breakdown
            data["ccss_mensual"] = pos.get_ccss_deduction()
            data["ccss_quincena"] = pos.get_ccss_deduction(breakdown.get("salario_quincena"))
        return jsonify(data)
    if request.method == "PUT":
        data = request.get_json() or {}
        if data.get("position_type") and data["position_type"] not in ("empleado", "administrador", "administrativo", "inventario", "custom"):
            data["position_type"] = "custom"
        position_schema.load(data, instance=pos, session=db.session, partial=True)
        db.session.commit()
        return jsonify(position_schema.dump(pos))
    db.session.delete(pos)
    db.session.commit()
    return "", 204


# ---------- Deduction Types (Tipos de deducción) - estándar global ----------
@payroll_bp.route("/deduction-types", methods=["GET"])
def list_deduction_types():
    """Lista tipos de deducción estándar. can_be_negative permite valores negativos (ej. horas negociables)."""
    types = DeductionType.query.order_by(DeductionType.display_order, DeductionType.name).all()
    return jsonify(deduction_types_schema.dump(types))


@payroll_bp.route("/deduction-types", methods=["POST"])
def create_deduction_type():
    """Crea tipo de deducción estándar. can_be_negative: si True, amount/quantity pueden ser negativos."""
    data = request.get_json() or {}
    dt = deduction_type_schema.load(data, session=db.session)
    db.session.add(dt)
    db.session.commit()
    return jsonify(deduction_type_schema.dump(dt)), 201


@payroll_bp.route("/deduction-types/<int:dt_id>", methods=["GET", "PUT", "DELETE"])
def deduction_type_detail(dt_id):
    dt = DeductionType.query.get(dt_id)
    if not dt:
        return jsonify({"error": "Tipo de deducción no encontrado"}), 404
    if request.method == "GET":
        return jsonify(deduction_type_schema.dump(dt))
    if request.method == "PUT":
        data = request.get_json() or {}
        deduction_type_schema.load(data, instance=dt, session=db.session, partial=True)
        db.session.commit()
        return jsonify(deduction_type_schema.dump(dt))
    db.session.delete(dt)
    db.session.commit()
    return "", 204


# ---------- Entries ----------
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
    valid_types = ("empleado", "administrador", "administrativo", "inventario", "custom", "mermas", "other", "employee")
    if entry_type in valid_types:
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
    entry = db.get_or_404(PayrollEntry, entry_id)
    if fid:
        loc = PayrollLocation.query.filter_by(id=entry.location_id, franchisee_id=fid).first()
        if not loc:
            return jsonify({"error": "Registro no encontrado"}), 404
    if request.method == "GET":
        return jsonify(entry_schema.dump(entry))
    if request.method == "PUT":
        data = request.get_json() or {}
        if "period_date" in data:
            data["period_date"] = _parse_date_param(data["period_date"]) if data["period_date"] else None
        if data.get("employee_id"):
            emp = Employee.query.filter_by(id=data["employee_id"], franchisee_id=fid).first()
            if not emp:
                data.pop("employee_id", None)
        if data.get("position_id"):
            pos = Position.query.get(data["position_id"]) if data.get("position_id") else None
            if not pos:
                data.pop("position_id", None)
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
    if "period_date" in data:
        data["period_date"] = _parse_date_param(data["period_date"]) if data["period_date"] else None
    if data.get("employee_id"):
        emp = Employee.query.filter_by(id=data["employee_id"], franchisee_id=fid).first()
        if not emp:
            data.pop("employee_id", None)
    if data.get("position_id"):
        pos = Position.query.get(data["position_id"]) if data.get("position_id") else None
        if not pos:
            data.pop("position_id", None)
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


def _normalize_emp_name(s):
    """Normaliza nombre para agrupar: sin acentos, espacios colapsados, mayúsculas."""
    if not s:
        return ""
    import unicodedata
    s = str(s).strip().upper()
    nfd = unicodedata.normalize("NFD", s)
    s = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


# ---------- Generar desgloses desde BD (consultas SQL) ----------
def _generate_payslips_from_entries(fid, location_id, period_date, replace=False):
    """
    Genera Payslips desde PayrollEntry y Employee (consultas SQL).
    Agrupa registros por empleado y período, calcula salarios y líneas desde la BD.
    """
    from calendar import monthrange

    loc = PayrollLocation.query.filter_by(id=location_id, franchisee_id=fid).first()
    if not loc:
        return 0, "Ubicación no encontrada"
    location_name = loc.name

    # Período: mes del period_date
    period_start = date_type(period_date.year, period_date.month, 1)
    _, last_day = monthrange(period_date.year, period_date.month)
    period_end = date_type(period_date.year, period_date.month, last_day)

    # Registros del mes (period_date dentro del mes)
    entries = PayrollEntry.query.filter(
        PayrollEntry.location_id == location_id,
        PayrollEntry.period_date >= period_start,
        PayrollEntry.period_date <= period_end,
    ).order_by(PayrollEntry.employee_name).all()

    if not entries:
        return 0, "No hay registros de planilla para esa ubicación y período"

    if replace:
        payslips_to_del = Payslip.query.filter(
            Payslip.franchisee_id == fid,
            Payslip.location_name == location_name,
            Payslip.period_start == period_start,
            Payslip.period_end == period_end,
        ).all()
        for ps in payslips_to_del:
            db.session.delete(ps)
        db.session.flush()

    # Agrupar por empleado (nombre normalizado: sin acentos, espacios colapsados)
    groups = {}
    for e in entries:
        key = _normalize_emp_name(e.employee_name)
        if not key:
            continue
        if key not in groups:
            groups[key] = []
        groups[key].append(e)

    created = 0
    for emp_name_upper, group_entries in groups.items():
        emp_id = next((e.employee_id for e in group_entries if e.employee_id), None)
        emp = Employee.query.filter_by(id=emp_id, franchisee_id=fid).first() if emp_id else None
        if not emp:
            # Buscar por nombre normalizado (sin acentos)
            all_emps = Employee.query.filter_by(franchisee_id=fid).all()
            for ae in all_emps:
                if _normalize_emp_name(ae.name) == emp_name_upper:
                    emp = ae
                    break
        emp_name = group_entries[0].employee_name if group_entries else ""
        if emp:
            emp_name = emp.name or emp_name
        if not emp_name:
            continue

        pos = emp.position if emp else None
        pos_id = pos.id if pos else None
        pos_name = pos.name if pos else None
        if not pos_name and group_entries:
            first_pos = Position.query.get(group_entries[0].position_id) if group_entries[0].position_id else None
            pos_name = first_pos.name if first_pos else None
            pos_id = first_pos.id if first_pos else None
            if first_pos and not pos:
                pos = first_pos

        # Salario: empleado primero, luego puesto (desglose automático desde puesto)
        salario_mes = emp.salario_base if emp else None
        if (salario_mes is None or salario_mes <= 0) and pos and pos.salario_base:
            salario_mes = pos.salario_base
        if salario_mes is None or salario_mes <= 0:
            salario_mes = 0
        # Desglose: usar puesto si tiene salario_base, sino calcular con defaults
        if pos and pos.get_salary_breakdown():
            sb = pos.get_salary_breakdown()
            salary_quincena = sb.get("salario_quincena")
            salary_semana = sb.get("salario_semana")
            salary_dia = sb.get("salario_dia")
            salary_hora_ord = sb.get("salario_hora")
        else:
            hpd = (pos.horas_por_dia if pos else None) or 8
            dps = (pos.dias_por_semana if pos else None) or 6
            semanas_mes = 4.33
            dias_mes = round(dps * semanas_mes, 1)
            salary_quincena = salario_mes / 2 if salario_mes else None
            salary_semana = salario_mes / semanas_mes if salario_mes else None
            salary_dia = salario_mes / dias_mes if salario_mes else None
            salary_hora_ord = salario_mes / (dias_mes * hpd) if salario_mes else None
        salary_hora_extra = salary_hora_ord * 1.5 if salary_hora_ord else None  # CR: 1.5x

        numero_cuenta = emp.numero_cuenta if emp else None
        if not numero_cuenta and group_entries:
            for ge in group_entries:
                if ge.numero_cuenta:
                    numero_cuenta = ge.numero_cuenta
                    break

        tipo_pago = (emp.periodo_pago if emp and emp.periodo_pago else None) or "mensual"
        if tipo_pago == "quincenal" and salary_quincena:
            base_salario_periodo = salary_quincena
        elif tipo_pago == "semanal" and salary_semana:
            base_salario_periodo = salary_semana * 2
        elif tipo_pago == "diario" and salary_dia:
            base_salario_periodo = salary_dia * 13
        elif tipo_pago == "por_hora" and salary_hora_ord:
            base_salario_periodo = salary_hora_ord * 104
        else:
            base_salario_periodo = salario_mes or 0
        total_asig = base_salario_periodo
        total_ded = 0
        lines = []

        for ge in group_entries:
            if ge.entry_type == "mermas":
                amt = (ge.creditos_comida or 0) + (ge.vale_efectivo or 0)
                if amt == 0 and (ge.ccss_rebajos or 0) != 0:
                    amt = ge.ccss_rebajos
                if amt == 0:
                    amt = ge.creditos_comida or 0
                amt = -abs(float(amt)) if amt else 0
                lines.append({"line_type": "deduccion", "concept": "Mermas (gasto del empleado)", "amount": amt})
                total_ded += abs(amt)
            else:
                if (ge.hrs_extra or 0) != 0 and salary_hora_extra:
                    val = ge.hrs_extra * salary_hora_extra
                    lines.append({"line_type": "asignacion", "concept": "Horas extra", "amount": val, "quantity": ge.hrs_extra})
                    total_asig += val
                if (ge.creditos_comida or 0) != 0:
                    val = float(ge.creditos_comida)
                    lines.append({"line_type": "deduccion", "concept": "Créditos comida", "amount": -abs(val) if val > 0 else val})
                    total_ded += abs(val) if val > 0 else abs(val)
                if (ge.vale_efectivo or 0) != 0:
                    val = float(ge.vale_efectivo)
                    lines.append({"line_type": "deduccion", "concept": "Vale efectivo", "amount": -abs(val) if val > 0 else val})
                    total_ded += abs(val) if val > 0 else abs(val)
                if (ge.ccss_rebajos or 0) != 0:
                    val = float(ge.ccss_rebajos)
                    lines.append({"line_type": "deduccion", "concept": "CCSS / Rebajos", "amount": -abs(val)})
                    total_ded += abs(val)

        # Deducción CCSS automática si no viene en registros (ley CR) y el puesto tiene aplicar_ccss=True
        has_ccss = any("CCSS" in str(l.get("concept", "")) for l in lines)
        aplicar_ccss = pos is None or getattr(pos, "aplicar_ccss", True)  # default True si no existe el campo
        if not has_ccss and salario_mes and aplicar_ccss:
            ccss_pct = None
            if pos and pos.ccss_pct is not None:
                ccss_pct = pos.ccss_pct
            else:
                dt_ccss = DeductionType.query.filter(
                    DeductionType.name.ilike("%ccss%trabajador%")
                ).first()
                if dt_ccss and dt_ccss.rate_pct is not None:
                    ccss_pct = dt_ccss.rate_pct
            if ccss_pct is not None:
                base_ccss = base_salario_periodo
                ccss_amt = round(base_ccss * ccss_pct, 2)
                if ccss_amt > 0:
                    lines.append({"line_type": "deduccion", "concept": "CCSS Trabajador", "amount": -ccss_amt})
                    total_ded += ccss_amt

        if salario_mes and not any("Salario base" in str(l.get("concept", "")) for l in lines):
            amt = base_salario_periodo
            lines.insert(0, {"line_type": "asignacion", "concept": "Salario base", "amount": amt})

        total_depositado = total_asig - total_ded

        ps = Payslip(
            franchisee_id=fid,
            employee_id=emp.id if emp else None,
            position_id=pos_id,
            location_name=location_name,
            employee_name=emp_name,
            position=pos_name,
            period_start=period_start,
            period_end=period_end,
            tipo_pago=tipo_pago,
            salary_mes=salario_mes,
            salary_quincena=salary_quincena,
            salary_semana=salary_semana,
            salary_dia=salary_dia,
            salary_hora_ordinaria=salary_hora_ord,
            salary_hora_extra=salary_hora_extra,
            total_asignaciones=total_asig,
            total_deducciones=total_ded,
            total_depositado=total_depositado,
            numero_cuenta=numero_cuenta,
        )
        db.session.add(ps)
        db.session.flush()
        for line in lines:
            pl = PayslipLine(
                payslip_id=ps.id,
                line_type=line.get("line_type", "asignacion"),
                concept=line.get("concept", ""),
                amount=line.get("amount", 0),
                quantity=line.get("quantity"),
            )
            db.session.add(pl)
        created += 1

    db.session.commit()
    return created, None


@payroll_bp.route("/generate-payslips", methods=["POST"])
def generate_payslips():
    """
    Genera desgloses de pago desde la BD (PayrollEntry + Employee).
    Body: location_id (int) o location_name (str), period_date (YYYY-MM-DD), replace (bool).
    """
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    period_date = _parse_date_param(data.get("period_date"))
    if not period_date:
        return jsonify({"error": "Falta period_date (YYYY-MM-DD)"}), 400
    location_id = data.get("location_id")
    if location_id is not None and not isinstance(location_id, (int, float)):
        try:
            location_id = int(location_id)
        except (TypeError, ValueError):
            location_id = None
    location_name = (data.get("location_name") or "").strip()
    if not location_id and location_name:
        loc = PayrollLocation.query.filter_by(franchisee_id=fid, name=location_name).first()
        location_id = loc.id if loc else None
    if not location_id:
        return jsonify({"error": "Falta location_id o location_name"}), 400
    replace = data.get("replace", False)
    created, err = _generate_payslips_from_entries(fid, location_id, period_date, replace=replace)
    if err:
        return jsonify({"error": err}), 400
    return jsonify({
        "message": "Desgloses generados desde la base de datos",
        "payslips_created": created,
    }), 200


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


@payroll_bp.route("/payslips/periods", methods=["GET"])
def list_payslip_periods():
    """Lista períodos únicos (ubicación, inicio, fin) para el resumen PDF."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"periods": []})
    rows = db.session.query(
        Payslip.location_name,
        Payslip.period_start,
        Payslip.period_end,
    ).filter_by(franchisee_id=fid).distinct().order_by(
        Payslip.period_start.desc(),
        Payslip.location_name,
    ).limit(50).all()
    return jsonify({
        "periods": [
            {
                "location_name": r[0],
                "period_start": r[1].isoformat() if r[1] else None,
                "period_end": r[2].isoformat() if r[2] else None,
            }
            for r in rows
        ],
    })


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
        query = query.filter(Payslip.period_start >= period_start)
    if period_end:
        query = query.filter(Payslip.period_end <= period_end)
    payslips = query.order_by(Payslip.period_start.asc(), Payslip.period_end.asc(), Payslip.employee_name).limit(200).all()
    return jsonify(payslips_schema.dump(payslips))


@payroll_bp.route("/payslips/<int:payslip_id>", methods=["GET"])
def get_payslip(payslip_id):
    """Obtiene un desglose de pago por ID."""
    fid = get_or_default_franchisee_id()
    payslip = Payslip.query.filter_by(id=payslip_id, franchisee_id=fid).first() if fid else None
    if not payslip:
        return jsonify({"error": "Desglose no encontrado"}), 404
    return jsonify(payslip_schema.dump(payslip))


@payroll_bp.route("/payslips/batch-pdf", methods=["GET"])
def payslips_batch_pdf():
    """
    Genera un PDF con todos los desgloses (uno por página).
    Query opcionales: employee_id=, from_date=, to_date=, periodo_tipo=, location_name=.
    Sin filtros: imprime todos los desgloses del franquiciado.
    """
    from flask import Response
    from utils.payslip_pdf import build_batch_payslip_pdf
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    query = Payslip.query.filter_by(franchisee_id=fid)
    employee_id = request.args.get("employee_id", type=int)
    from_date = _parse_date_param(request.args.get("from_date")) or _parse_date_param(request.args.get("period_start"))
    to_date = _parse_date_param(request.args.get("to_date")) or _parse_date_param(request.args.get("period_end"))
    periodo_tipo = request.args.get("periodo_tipo", "").strip()
    location_name = request.args.get("location_name", "").strip()
    if employee_id:
        query = query.filter(Payslip.employee_id == employee_id)
    if from_date:
        query = query.filter(Payslip.period_start >= from_date)
    if to_date:
        query = query.filter(Payslip.period_end <= to_date)
    if periodo_tipo and periodo_tipo in ("mensual", "quincenal", "semanal", "diario", "por_hora"):
        query = query.filter(Payslip.tipo_pago == periodo_tipo)
    if location_name:
        query = query.filter(Payslip.location_name.ilike(f"%{location_name}%"))
    payslips = query.order_by(Payslip.period_start.asc(), Payslip.period_end.asc(), Payslip.employee_name).limit(500).all()
    pdf_bytes = build_batch_payslip_pdf(payslips)
    filename = "desgloses_planilla.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )


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
    emp_by_name = {e.name.strip().upper(): e for e in Employee.query.filter_by(franchisee_id=fid, active=True).all() if (e.name or "").strip()}
    pos_by_name = {p.name.strip().upper(): p for p in Position.query.all() if (p.name or "").strip()}
    created = 0
    for sheet_name in wb.sheetnames:
        if any(skip in sheet_name.upper() for skip in skip_sheets):
            continue
        ws = wb[sheet_name]
        parsed = _parse_payslip_sheet(ws, location_name, sheet_name)
        if not parsed.get("employee_name") or not parsed.get("period_start"):
            continue
        if replace:
            payslips_to_del = Payslip.query.filter(
                Payslip.franchisee_id == fid,
                Payslip.location_name == location_name,
                Payslip.employee_name == parsed["employee_name"],
                Payslip.period_start == parsed["period_start"],
            ).all()
            for ps in payslips_to_del:
                db.session.delete(ps)
        emp_name = (parsed.get("employee_name") or "").strip()
        emp = emp_by_name.get(emp_name.upper()) if emp_name else None
        pos_name = (parsed.get("position") or "").strip()
        pos = pos_by_name.get(pos_name.upper()) if pos_name else None
        ps = Payslip(
            franchisee_id=fid,
            employee_id=emp.id if emp else None,
            position_id=pos.id if pos else None,
            location_name=parsed["location_name"],
            employee_name=parsed["employee_name"],
            position=parsed.get("position"),
            period_start=parsed["period_start"],
            period_end=parsed["period_end"],
            tipo_pago=parsed.get("tipo_pago") or "mensual",
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


# ---------- Registro de pagos ----------
@payroll_bp.route("/payments", methods=["GET"])
def list_payments():
    """Lista registros de pago del franquiciado. Query: employee_id=, location_id=, from_date=, to_date=, periodo_tipo=."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify([])
    query = PaymentRecord.query.filter_by(franchisee_id=fid)
    employee_id = request.args.get("employee_id", type=int)
    location_id = request.args.get("location_id", type=int)
    periodo_tipo = request.args.get("periodo_tipo", "").strip()
    from_date = _parse_date_param(request.args.get("from_date"))
    to_date = _parse_date_param(request.args.get("to_date"))
    if employee_id:
        query = query.filter_by(employee_id=employee_id)
    if periodo_tipo and periodo_tipo in ("mensual", "quincenal", "semanal", "diario", "por_hora"):
        query = query.filter_by(periodo_tipo=periodo_tipo)
    if location_id:
        query = query.filter_by(location_id=location_id)
    if from_date:
        query = query.filter(PaymentRecord.payment_date >= from_date)
    if to_date:
        query = query.filter(PaymentRecord.payment_date <= to_date)
    records = query.order_by(PaymentRecord.payment_date.desc()).limit(500).all()
    data = payment_records_schema.dump(records)
    for i, r in enumerate(records):
        if r.employee:
            data[i]["employee_name"] = r.employee.name
        if r.location:
            data[i]["location_name"] = r.location.name
    return jsonify(data)


def _calc_payment_amount(emp, data):
    """Calcula amount según periodo_tipo y datos del empleado."""
    periodo = data.get("periodo_tipo") or emp.periodo_pago or "mensual"
    salario = emp.salario_base or 0
    amount = _to_float(data.get("amount"))

    if periodo == "por_hora":
        hrs = _to_float(data.get("hours_worked")) or 0
        hrs_extra = _to_float(data.get("hours_extra")) or 0
        rate = _to_float(data.get("hourly_rate")) or emp.salario_hora or (salario / ((emp.horas_por_dia or 8) * 22) if salario else None)
        is_festivo = data.get("hours_extra_festivo") in (True, "true", "1")
        if rate and rate > 0 and (hrs > 0 or hrs_extra > 0):
            # CR Código de Trabajo: ordinarias 1x, extras 1.5x (50% recargo), festivos 2x
            amt = (hrs * rate) + (hrs_extra * rate * (2.0 if is_festivo else 1.5))
            return round(amt, 2), {"hours_worked": hrs, "hours_extra": hrs_extra, "hourly_rate": rate, "hours_extra_festivo": is_festivo}

    def _add_hours_extra(base_amt, extra_data):
        """Suma horas extras según CR: 1.5x ordinarias, 2x festivos."""
        hrs_extra = _to_float(data.get("hours_extra")) or 0
        if hrs_extra <= 0:
            return base_amt, extra_data
        rate = emp.salario_hora or (salario / ((emp.horas_por_dia or 8) * 22) if salario else None)
        if not rate or rate <= 0:
            return base_amt, extra_data
        is_festivo = data.get("hours_extra_festivo") in (True, "true", "1")
        ext = hrs_extra * rate * (2.0 if is_festivo else 1.5)
        extra_data["hours_extra"] = hrs_extra
        extra_data["hours_extra_festivo"] = is_festivo
        return base_amt + ext, extra_data

    if periodo == "diario":
        days = _to_float(data.get("days_worked"))
        incl_sun = data.get("include_sundays") in (True, "true", "1")
        if days and days > 0 and salario > 0:
            dias_mes = 26 if incl_sun else 22
            base = salario / dias_mes * days
            base, extra = _add_hours_extra(base, {"days_worked": days, "include_sundays": incl_sun})
            return round(base, 2), extra

    if periodo == "mensual" and salario > 0 and (amount is None or amount <= 0):
        base, extra = _add_hours_extra(salario, {})
        return round(base, 2), extra
    if periodo == "quincenal" and salario > 0 and (amount is None or amount <= 0):
        base, extra = _add_hours_extra(salario / 2, {})
        return round(base, 2), extra
    if periodo == "semanal" and salario > 0 and (amount is None or amount <= 0):
        base, extra = _add_hours_extra(salario / 4.33, {})
        return round(base, 2), extra

    return amount, {}


@payroll_bp.route("/payments", methods=["POST"])
def create_payment():
    """Registra un pago. Body: employee_id, amount, payment_date, period_start, period_end, periodo_tipo, hours_worked, hourly_rate, days_worked, include_sundays, location_id, payslip_id, notes."""
    fid = get_or_default_franchisee_id()
    if not fid:
        return jsonify({"error": "Selecciona un franquiciado"}), 400
    data = request.get_json() or {}
    if not data.get("employee_id"):
        return jsonify({"error": "Falta employee_id"}), 400
    emp = Employee.query.filter_by(id=data["employee_id"], franchisee_id=fid).first()
    if not emp:
        return jsonify({"error": "Empleado no encontrado"}), 400
    # Calcular amount automáticamente si es posible
    calc_amt, extra = _calc_payment_amount(emp, data)
    if calc_amt is not None and calc_amt > 0:
        data["amount"] = calc_amt
        data.update(extra)
    if data.get("amount") is None:
        return jsonify({"error": "Falta amount. Ingresa datos según el período (días, horas, etc.) o el salario del empleado."}), 400
    payment_date = _parse_date_param(data.get("payment_date"))
    if not payment_date:
        payment_date = date_type.today()
    for f in ("period_start", "period_end"):
        if f in data and data[f]:
            data[f] = _parse_date_param(data[f])
    data["franchisee_id"] = fid
    data["payment_date"] = payment_date
    data.setdefault("periodo_tipo", emp.periodo_pago or "mensual")
    rec = payment_record_schema.load(data, session=db.session)
    db.session.add(rec)
    db.session.commit()
    out = payment_record_schema.dump(rec)
    out["employee_name"] = emp.name
    return jsonify(out), 201


@payroll_bp.route("/payments/<int:pay_id>", methods=["GET", "PUT", "DELETE"])
def payment_detail(pay_id):
    """Obtiene, actualiza o elimina un registro de pago."""
    fid = get_or_default_franchisee_id()
    rec = PaymentRecord.query.filter_by(id=pay_id, franchisee_id=fid).first() if fid else None
    if not rec:
        return jsonify({"error": "Registro no encontrado"}), 404
    if request.method == "GET":
        out = payment_record_schema.dump(rec)
        if rec.employee:
            out["employee_name"] = rec.employee.name
        return jsonify(out)
    if request.method == "PUT":
        data = request.get_json() or {}
        for f in ("payment_date", "period_start", "period_end"):
            if f in data and data[f]:
                data[f] = _parse_date_param(data[f])
        if rec.employee:
            calc_amt, extra = _calc_payment_amount(rec.employee, {**data, "periodo_tipo": data.get("periodo_tipo") or rec.periodo_tipo})
            if calc_amt is not None and calc_amt > 0:
                data["amount"] = calc_amt
                data.update(extra)
        payment_record_schema.load(data, instance=rec, session=db.session, partial=True)
        db.session.commit()
        return jsonify(payment_record_schema.dump(rec))
    db.session.delete(rec)
    db.session.commit()
    return "", 204


@payroll_bp.route("/payments/<int:pay_id>/payslip-pdf", methods=["GET"])
def payment_payslip_pdf(pay_id):
    """
    Genera el PDF del desglose asociado a un registro de pago.
    Si el pago tiene payslip_id, usa ese desglose. Si no, busca por empleado (id o nombre) y período.
    """
    from flask import Response
    from utils.payslip_pdf import build_payslip_pdf
    fid = get_or_default_franchisee_id()
    rec = PaymentRecord.query.filter_by(id=pay_id, franchisee_id=fid).first() if fid else None
    if not rec:
        return jsonify({"error": "Registro de pago no encontrado"}), 404
    payslip = None
    if rec.payslip_id:
        payslip = Payslip.query.filter_by(id=rec.payslip_id, franchisee_id=fid).first()
    emp_name = (rec.employee.name or "").strip() if rec.employee else ""
    if not payslip:
        # Buscar por employee_id O por employee_name (payslips importados pueden tener employee_id null)
        emp_filter = db.or_(
            Payslip.employee_id == rec.employee_id,
            (Payslip.employee_id.is_(None)) & (Payslip.employee_name.ilike(emp_name)) if emp_name else (Payslip.id < 0),
        ) if (rec.employee_id or emp_name) else (Payslip.id < 0)
        q = Payslip.query.filter(Payslip.franchisee_id == fid, emp_filter)
        if rec.period_start:
            q = q.filter(Payslip.period_end >= rec.period_start)
        if rec.period_end:
            q = q.filter(Payslip.period_start <= rec.period_end)
        if not rec.period_start and not rec.period_end and rec.payment_date:
            # Sin período: buscar desgloses cercanos a la fecha de pago
            q = q.filter(
                db.or_(
                    Payslip.period_start <= rec.payment_date,
                    Payslip.period_end >= rec.payment_date,
                )
            )
        payslip = q.order_by(Payslip.period_start.desc()).first()
    if not payslip and (rec.employee_id or emp_name):
        # Último intento: cualquier desglose del empleado (por id o nombre, incl. coincidencia parcial)
        conds = []
        if rec.employee_id:
            conds.append(Payslip.employee_id == rec.employee_id)
        if emp_name:
            conds.append(Payslip.employee_name.ilike(emp_name))
            conds.append(Payslip.employee_name.ilike(f"%{emp_name}%"))  # Coincidencia parcial
        if conds:
            payslip = Payslip.query.filter(Payslip.franchisee_id == fid, db.or_(*conds)).order_by(Payslip.period_start.desc()).first()
    if payslip:
        pdf_bytes = build_payslip_pdf(payslip)
        safe_name = re.sub(r"[^\w\s\-]", "", payslip.employee_name or "colaborador").replace(" ", "_")[:40]
        filename = f"desglose_{safe_name}_{payslip.period_start}.pdf"
    else:
        from utils.payslip_pdf import build_payment_summary_pdf
        pdf_bytes = build_payment_summary_pdf(rec)
        safe_name = re.sub(r"[^\w\s\-]", "", (rec.employee.name if rec.employee else "") or "pago").replace(" ", "_")[:40]
        filename = f"comprobante_pago_{safe_name}_{rec.payment_date}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"inline; filename={filename}"},
    )
