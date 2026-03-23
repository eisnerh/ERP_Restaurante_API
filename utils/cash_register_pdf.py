"""Generación de PDF del reporte de cierre de caja."""
import io
from datetime import datetime


DARK_TEAL = "#1B5E5A"
WHITE = "#FFFFFF"
BLACK = "#333333"


def _fmt_money(val):
    if val is None:
        return "-"
    try:
        v = float(val)
        s = "{:,.2f}".format(v)
        return "₡ " + s.replace(",", " ").replace(".", ",")
    except (TypeError, ValueError):
        return str(val)


def _fmt_datetime(s):
    if not s:
        return "-"
    try:
        dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except (ValueError, TypeError):
        return str(s)


def build_cash_register_report_pdf(detail_data, arqueo_data=None):
    """
    Genera PDF del reporte de cierre de caja.
    detail_data: dict de get_session_detail (session, orders, expenses)
    arqueo_data: dict opcional de get_arqueo_data (resumen_moneda, ventas_por_familia)
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
    normal = ParagraphStyle(name="NormalBlack", parent=styles["Normal"], textColor=colors.HexColor(BLACK))
    flow = []

    session = detail_data.get("session") or {}
    session_id = session.get("id", "-")
    arqueo_num = session.get("arqueo_number") or (arqueo_data.get("arqueo_number") if arqueo_data else None)
    opened = _fmt_datetime(session.get("opened_at"))
    closed = _fmt_datetime(session.get("closed_at"))

    # Título
    title = Table([["REPORTE DE CIERRE DE CAJA"]], colWidths=[7 * inch])
    title.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(WHITE)),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 14),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    flow.append(title)
    flow.append(Spacer(1, 0.15 * inch))

    # Cabecera
    header_rows = [
        ["Sesión", str(session_id), "Arqueo Z", str(arqueo_num) if arqueo_num else "-"],
        ["Apertura", opened, "Cierre", closed],
    ]
    t_head = Table(header_rows, colWidths=[1.2 * inch, 2.5 * inch, 1.2 * inch, 2.5 * inch])
    t_head.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor(BLACK)),
    ]))
    flow.append(t_head)
    flow.append(Spacer(1, 0.2 * inch))

    # Resumen de caja
    sum_rows = [
        ["Concepto", "Monto"],
        ["Saldo apertura", _fmt_money(session.get("opening_balance"))],
        ["Ventas (cobradas)", _fmt_money(session.get("sales_total"))],
        ["Gastos", _fmt_money(session.get("expenses_total"))],
        ["Saldo esperado", _fmt_money(session.get("expected_balance"))],
        ["Saldo cierre", _fmt_money(session.get("closing_balance"))],
        ["Diferencia", _fmt_money(session.get("difference"))],
    ]
    t_sum = Table(sum_rows, colWidths=[2.5 * inch, 2 * inch])
    t_sum.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(BLACK)),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8EDEA")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor(DARK_TEAL)),
        ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor(DARK_TEAL)),
    ]))
    flow.append(t_sum)
    flow.append(Spacer(1, 0.25 * inch))

    # Ventas (pedidos)
    flow.append(Paragraph("<b>Ventas</b>", normal))
    orders = detail_data.get("orders") or []
    if orders:
        ord_rows = [["#", "Medio pago", "Total", "Fecha"]]
        for i, o in enumerate(orders, 1):
            pt = (o.get("payment_type") or "efectivo").replace("_", " ").title()
            ord_rows.append([
                str(i),
                pt,
                _fmt_money(o.get("total")),
                _fmt_datetime(o.get("updated_at")),
            ])
        ord_rows.append(["", "", "TOTAL", _fmt_money(session.get("sales_total"))])
        t_ord = Table(ord_rows, colWidths=[0.5 * inch, 1.5 * inch, 1.5 * inch, 2 * inch])
        t_ord.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(BLACK)),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8EDEA")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        flow.append(t_ord)
    else:
        flow.append(Paragraph("<i>Sin ventas</i>", normal))
    flow.append(Spacer(1, 0.2 * inch))

    # Gastos
    flow.append(Paragraph("<b>Gastos operacionales</b>", normal))
    expenses = detail_data.get("expenses") or []
    if expenses:
        exp_rows = [["Descripción", "Monto", "Medio", "Compra"]]
        for e in expenses:
            desc = (e.get("description") or "-")[:40]
            compra = ""
            if e.get("purchase_order"):
                po = e["purchase_order"]
                compra = (po.get("order_number") or "") + (" - " + (po.get("supplier_name") or "") if po.get("supplier_name") else "")
            exp_rows.append([
                desc,
                _fmt_money(e.get("amount")),
                (e.get("payment_type") or "efectivo").replace("_", " ").title(),
                compra[:25] if compra else "-",
            ])
        exp_rows.append(["TOTAL", _fmt_money(session.get("expenses_total")), "", ""])
        t_exp = Table(exp_rows, colWidths=[2 * inch, 1.2 * inch, 1.2 * inch, 1.8 * inch])
        t_exp.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(BLACK)),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#E8EDEA")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        flow.append(t_exp)
    else:
        flow.append(Paragraph("<i>Sin gastos</i>", normal))
    flow.append(Spacer(1, 0.25 * inch))

    # Arqueo Z: resumen por medio de pago (si cerrada)
    if arqueo_data and arqueo_data.get("resumen_moneda"):
        flow.append(Paragraph("<b>Resumen por medio de pago (Arqueo Z)</b>", normal))
        resumen = arqueo_data["resumen_moneda"]
        res_rows = [["Medio", "Calculado", "Declarado", "Descuadre"]]
        for r in resumen:
            decl = r.get("declarado")
            calc = r.get("calculado") or 0
            decl_val = decl if decl is not None else calc
            desc = (decl_val - calc) if decl is not None else 0
            res_rows.append([
                r.get("label", ""),
                _fmt_money(calc),
                _fmt_money(decl) if decl is not None else "-",
                (_fmt_money(desc) if desc >= 0 else "-" + _fmt_money(-desc).replace("₡ ", "")) if decl is not None else "-",
            ])
        t_res = Table(res_rows, colWidths=[1.5 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
        t_res.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(BLACK)),
        ]))
        flow.append(t_res)
        flow.append(Spacer(1, 0.2 * inch))

    # Ventas por familia
    if arqueo_data and arqueo_data.get("ventas_por_familia"):
        flow.append(Paragraph("<b>Ventas por familia</b>", normal))
        fam = arqueo_data["ventas_por_familia"]
        fam_rows = [["Familia", "Unidades", "Monto"]]
        for f in fam[:15]:  # Máximo 15 filas
            fam_rows.append([
                (f.get("familia") or "-")[:30],
                str(f.get("unidades", 0)),
                _fmt_money(f.get("monto")),
            ])
        t_fam = Table(fam_rows, colWidths=[2.5 * inch, 1.2 * inch, 1.5 * inch])
        t_fam.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK_TEAL)),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(WHITE)),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor(BLACK)),
        ]))
        flow.append(t_fam)

    doc.build(flow)
    buf.seek(0)
    return buf.getvalue()
