"""Generación de PDF: desglose para firma del colaborador y resumen de quincena."""
import io
from datetime import date

# Paleta de colores (estilo planilla RAUL CASTAÑO: verde azulado oscuro, blanco, texto negro)
DARK_TEAL = "#1B5E5A"       # Verde azulado oscuro: encabezados, secciones, totales
WHITE = "#FFFFFF"
BLACK = "#333333"           # Texto principal de datos
LIGHT_GRAY = "#E8EDEA"      # Fondo alternativo suave (off-white / gris verdoso)
BORDER_GRAY = "#8B9E94"     # Bordes de celdas (gris verdoso)


def _fmt_money(val):
    if val is None:
        return "-"
    try:
        return "₡ {:,.2f}".format(float(val))
    except (TypeError, ValueError):
        return str(val)


def _fmt_date(d):
    if d is None:
        return "-"
    if hasattr(d, "strftime"):
        return d.strftime("%d/%m/%Y")
    return str(d)


def build_payslip_pdf(payslip):
    """
    Genera un PDF de una sola hoja con el desglose del colaborador,
    listo para imprimir y firmar.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, PageBreak

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
    )
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    normal.textColor = colors.HexColor(BLACK)
    title_para_style = ParagraphStyle(
        name="CustomTitle", parent=styles["Heading1"], fontSize=14, alignment=1,
        textColor=colors.HexColor(WHITE),
    )
    flow = []

    # Encabezado (barra verde azulado con texto blanco, como en la imagen)
    title_table = Table([["DESGLOSE DE PAGO QUINCENAL"]], colWidths=[6 * inch])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(WHITE)),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    flow.append(title_table)
    flow.append(Spacer(1, 0.15 * inch))
    flow.append(Paragraph(f"<b>{payslip.location_name}</b>", normal))
    flow.append(Paragraph(
        f"Período: {_fmt_date(payslip.period_start)} al {_fmt_date(payslip.period_end)}",
        normal
    ))
    flow.append(Spacer(1, 0.2 * inch))

    # Colaborador y cargo
    flow.append(Paragraph(
        f"<b>Colaborador:</b> {payslip.employee_name} &nbsp;&nbsp; <b>Cargo:</b> {payslip.position or '-'}",
        normal
    ))
    flow.append(Spacer(1, 0.15 * inch))

    # Desglose salarial (encabezado verde azulado, datos blanco/gris claro, bordes gris verdoso)
    sal_data = [
        ["Desglose del salario", "Valor"],
        ["Salario mensual", _fmt_money(payslip.salary_mes)],
        ["Salario quincenal", _fmt_money(payslip.salary_quincena)],
        ["Salario semanal", _fmt_money(payslip.salary_semana)],
        ["Salario día", _fmt_money(payslip.salary_dia)],
        ["Hora ordinaria", _fmt_money(payslip.salary_hora_ordinaria)],
        ["Hora extra", _fmt_money(payslip.salary_hora_extra)],
    ]
    t_sal = Table(sal_data, colWidths=[3 * inch, 1.5 * inch])
    t_sal.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(BLACK)),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER_GRAY)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor(WHITE), colors.HexColor(LIGHT_GRAY)]),
    ]))
    flow.append(t_sal)
    flow.append(Spacer(1, 0.2 * inch))

    # Asignaciones
    asig_rows = [["Concepto", "Cant.", "Monto (₡)"]]
    asig_lines = sorted([l for l in payslip.lines if l.line_type == "asignacion"], key=lambda x: x.id)
    for line in asig_lines:
        qty = str(int(line.quantity)) if line.quantity is not None and line.quantity == int(line.quantity) else (str(line.quantity) if line.quantity else "-")
        asig_rows.append([line.concept, qty, _fmt_money(line.amount)])
    asig_rows.append(["<b>TOTAL ASIGNACIONES</b>", "", _fmt_money(payslip.total_asignaciones)])
    t_asig = Table(asig_rows, colWidths=[2.5 * inch, 0.8 * inch, 1.5 * inch])
    t_asig.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor(WHITE)),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -2), colors.HexColor(BLACK)),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER_GRAY)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor(WHITE), colors.HexColor(LIGHT_GRAY)]),
    ]))
    flow.append(Paragraph("<b>ASIGNACIONES</b>", normal))
    flow.append(Spacer(1, 0.05 * inch))
    flow.append(t_asig)
    flow.append(Spacer(1, 0.15 * inch))

    # Deducciones
    ded_rows = [["Concepto", "Monto (₡)"]]
    ded_lines = sorted([l for l in payslip.lines if l.line_type == "deduccion"], key=lambda x: x.id)
    for line in ded_lines:
        ded_rows.append([line.concept, _fmt_money(line.amount)])
    ded_rows.append(["<b>TOTAL DEDUCCIONES</b>", _fmt_money(payslip.total_deducciones)])
    t_ded = Table(ded_rows, colWidths=[2.5 * inch, 1.5 * inch])
    t_ded.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor(WHITE)),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -2), colors.HexColor(BLACK)),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER_GRAY)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor(WHITE), colors.HexColor(LIGHT_GRAY)]),
    ]))
    flow.append(Paragraph("<b>DEDUCCIONES</b>", normal))
    flow.append(Spacer(1, 0.05 * inch))
    flow.append(t_ded)
    flow.append(Spacer(1, 0.2 * inch))

    # Total depositado (estilo imagen: énfasis en verde azulado)
    flow.append(Paragraph(
        f"<b>TOTAL A DEPOSITAR:</b> {_fmt_money(payslip.total_depositado)}",
        ParagraphStyle(name="Total", parent=normal, fontSize=12, textColor=colors.HexColor(DARK_TEAL))
    ))
    if payslip.numero_cuenta:
        flow.append(Paragraph(f"Nº cuenta: {payslip.numero_cuenta}", normal))
    flow.append(Spacer(1, 0.4 * inch))

    # Línea de firma
    flow.append(Paragraph("_" * 50, normal))
    flow.append(Paragraph(
        "Firma del colaborador &nbsp;&nbsp;&nbsp; Fecha: _______________",
        ParagraphStyle(name="Firma", parent=normal, textColor=colors.HexColor(BLACK))
    ))

    doc.build(flow)
    buf.seek(0)
    return buf.getvalue()


def build_summary_pdf(payslips, location_name, period_start, period_end):
    """
    Genera un PDF de resumen de la quincena: lista de colaboradores y monto depositado,
    más total general.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
    )
    styles = getSampleStyleSheet()
    normal_style = ParagraphStyle(name="NormalBlack", parent=styles["Normal"], textColor=colors.HexColor(BLACK))
    flow = []

    # Título (barra verde azulado, texto blanco)
    title_table = Table([["RESUMEN DE PLANILLA QUINCENAL"]], colWidths=[6 * inch])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(WHITE)),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    flow.append(title_table)
    flow.append(Spacer(1, 0.1 * inch))
    flow.append(Paragraph(f"<b>{location_name}</b>", normal_style))
    flow.append(Paragraph(
        f"Período: {_fmt_date(period_start)} al {_fmt_date(period_end)}",
        normal_style
    ))
    flow.append(Spacer(1, 0.2 * inch))

    total_general = 0
    rows = [["#", "Colaborador", "Cargo", "Total depositado (₡)"]]
    for idx, p in enumerate(payslips, 1):
        rows.append([
            str(idx),
            p.employee_name,
            (p.position or "-")[:25],
            _fmt_money(p.total_depositado),
        ])
        if p.total_depositado is not None:
            total_general += float(p.total_depositado)

    rows.append(["", "", "TOTAL QUINCENA", _fmt_money(total_general)])

    col_widths = [0.4 * inch, 2.2 * inch, 2 * inch, 1.8 * inch]
    t = Table(rows, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.HexColor(WHITE)),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -2), colors.HexColor(BLACK)),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER_GRAY)),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.HexColor(WHITE), colors.HexColor(LIGHT_GRAY)]),
    ]))
    flow.append(t)
    flow.append(Spacer(1, 0.2 * inch))
    flow.append(Paragraph(
        f"Cantidad de colaboradores: {len(payslips)}",
        normal_style
    ))

    doc.build(flow)
    buf.seek(0)
    return buf.getvalue()


def build_employee_report_pdf(report_data):
    """
    Genera un PDF del reporte por empleado: pagos realizados y deducciones aplicadas.
    report_data: dict con employee, payments, deductions_summary, total_paid, total_deductions, net, from_date, to_date.
    """
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=0.5 * inch, rightMargin=0.5 * inch,
        topMargin=0.5 * inch, bottomMargin=0.5 * inch,
    )
    styles = getSampleStyleSheet()
    normal = ParagraphStyle(name="NormalBlack", parent=styles["Normal"], textColor=colors.HexColor(BLACK))
    flow = []

    emp = report_data.get("employee") or {}
    emp_name = emp.get("name") or "Empleado"
    from_date = report_data.get("from_date")
    to_date = report_data.get("to_date")
    period_str = ""
    if from_date or to_date:
        period_str = f"Período: {from_date or '...'} a {to_date or '...'}"

    title_table = Table([["REPORTE POR EMPLEADO"]], colWidths=[6 * inch])
    title_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(WHITE)),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    flow.append(title_table)
    flow.append(Spacer(1, 0.1 * inch))
    flow.append(Paragraph(f"<b>{emp_name}</b>", normal))
    if period_str:
        flow.append(Paragraph(period_str, normal))
    flow.append(Spacer(1, 0.2 * inch))

    payments = report_data.get("payments") or []
    pay_rows = [["Fecha pago", "Período", "Ubicación", "Días/Hrs", "Monto (₡)"]]
    for p in payments:
        per = (p.get("period_start") and p.get("period_end")) and f"{p['period_start']} a {p['period_end']}" or (p.get("periodo_tipo") or "-")
        dh = p.get("days_worked") is not None and f"{p['days_worked']} d" or (p.get("hours_worked") is not None and f"{p['hours_worked']} h" or "-")
        pay_rows.append([
            p.get("payment_date") or "-",
            per[:30],
            (p.get("location_name") or "-")[:20],
            dh,
            _fmt_money(p.get("amount")),
        ])
    if len(pay_rows) > 1:
        t_pay = Table(pay_rows, colWidths=[1.2 * inch, 1.8 * inch, 1.2 * inch, 0.7 * inch, 1.2 * inch])
        t_pay.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(BLACK)),
            ("ALIGN", (4, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER_GRAY)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor(WHITE), colors.HexColor(LIGHT_GRAY)]),
        ]))
        flow.append(Paragraph("<b>Pagos realizados</b>", normal))
        flow.append(Spacer(1, 0.05 * inch))
        flow.append(t_pay)
        flow.append(Spacer(1, 0.15 * inch))

    deductions = report_data.get("deductions_summary") or []
    if deductions:
        ded_rows = [["Concepto", "Total (₡)"]]
        for d in deductions:
            ded_rows.append([(d.get("concept") or "-")[:50], _fmt_money(d.get("total"))])
        t_ded = Table(ded_rows, colWidths=[3.5 * inch, 1.5 * inch])
        t_ded.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(BLACK)),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(BORDER_GRAY)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor(WHITE), colors.HexColor(LIGHT_GRAY)]),
        ]))
        flow.append(Paragraph("<b>Deducciones aplicadas</b>", normal))
        flow.append(Spacer(1, 0.05 * inch))
        flow.append(t_ded)
        flow.append(Spacer(1, 0.15 * inch))

    total_paid = report_data.get("total_paid") or 0
    total_ded = report_data.get("total_deductions") or 0
    net = report_data.get("net") or (total_paid - total_ded)
    flow.append(Paragraph(
        f"<b>Total pagado:</b> {_fmt_money(total_paid)} &nbsp;&nbsp; <b>Total deducciones:</b> {_fmt_money(total_ded)} &nbsp;&nbsp; <b>Neto:</b> {_fmt_money(net)}",
        ParagraphStyle(name="Totals", parent=normal, fontSize=10, textColor=colors.HexColor(DARK_TEAL))
    ))

    doc.build(flow)
    buf.seek(0)
    return buf.getvalue()
