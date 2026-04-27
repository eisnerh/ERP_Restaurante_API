"""API y rutas de configuración."""
import os
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from extensions import db
from models import AppSettings, Franchisee, Invoice
from utils.franchisee import get_or_default_franchisee_id
from utils.hacienda_crypto import list_p12_files, resolve_hacienda_p12_path

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "ico", "webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2 MB


def _allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _upload_dir():
    base = Path(current_app.static_folder) / "images"
    base.mkdir(parents=True, exist_ok=True)
    return base


@settings_bp.route("/upload-image", methods=["POST"])
def upload_image():
    """Sube una imagen y devuelve la URL para usarla como logo o favicon."""
    if "file" not in request.files and "image" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400
    file = request.files.get("file") or request.files.get("image")
    if not file or not file.filename:
        return jsonify({"error": "Archivo vacío"}), 400
    if not _allowed_file(file.filename):
        return jsonify({"error": "Formato no permitido. Use: png, jpg, jpeg, gif, ico, webp"}), 400
    content = file.read()
    if len(content) > MAX_FILE_SIZE:
        return jsonify({"error": "Archivo demasiado grande (máx. 2 MB)"}), 400
    ext = file.filename.rsplit(".", 1)[1].lower()
    safe_name = f"{uuid.uuid4().hex[:12]}.{ext}"
    dest = _upload_dir() / safe_name
    with open(dest, "wb") as f:
        f.write(content)
    url = f"/static/images/{safe_name}"
    return jsonify({"url": url})


def _crypto_settings_payload(fid):
    s = AppSettings.get(franchisee_id=fid)
    fname = getattr(s, "hacienda_p12_filename", None)
    resolved = resolve_hacienda_p12_path(franchisee_id=fid)
    return {
        "hacienda_p12_filename": fname or "",
        "hacienda_p12_resolved": str(resolved) if resolved else "",
        "hacienda_p12_available": list_p12_files(),
        "hacienda_p12_env_override": bool(os.environ.get("HACIENDA_P12_PATH", "").strip()),
        "hacienda_p12_password_configured": bool(os.environ.get("HACIENDA_P12_PASSWORD", "").strip()),
    }


@settings_bp.route("", methods=["GET"])
def get_settings():
    """Obtiene la configuración actual (del franquiciado seleccionado)."""
    fid = get_or_default_franchisee_id()
    s = AppSettings.get(franchisee_id=fid)
    out = {
        "app_name": s.app_name or "ERP Raul Castaño",
        "logo_url": s.logo_url or "",
        "favicon_url": s.favicon_url or "",
        "nav_icon": s.nav_icon or "",
    }
    if fid:
        last = int(getattr(s, "invoice_hacienda_last_seq", 0) or 0)
        inv_count = Invoice.query.filter_by(franchisee_id=fid).count()
        fr = db.session.get(Franchisee, fid)
        out["franchisee_id"] = fid
        out["franchisee_code"] = fr.code if fr else ""
        out["franchisee_name"] = fr.name if fr else ""
        out["invoice_hacienda_last_seq"] = last
        out["invoice_hacienda_next_seq_preview"] = last + 1
        out["invoices_count_in_erp"] = inv_count
    else:
        out["invoice_hacienda_last_seq"] = 0
        out["invoice_hacienda_next_seq_preview"] = 1
        out["invoices_count_in_erp"] = 0
    out.update(_crypto_settings_payload(fid))
    return jsonify(out)


@settings_bp.route("", methods=["PUT"])
def update_settings():
    """Actualiza la configuración del franquiciado actual."""
    fid = get_or_default_franchisee_id()
    s = AppSettings.get(franchisee_id=fid)
    data = request.get_json() or {}
    if "app_name" in data:
        s.app_name = (data.get("app_name") or "").strip() or "ERP Raul Castaño"
    if "logo_url" in data:
        s.logo_url = (data.get("logo_url") or "").strip() or None
    if "favicon_url" in data:
        s.favicon_url = (data.get("favicon_url") or "").strip() or None
    if "nav_icon" in data:
        s.nav_icon = (data.get("nav_icon") or "").strip() or None
    if "hacienda_p12_filename" in data and hasattr(s, "hacienda_p12_filename"):
        raw = (data.get("hacienda_p12_filename") or "").strip()
        if not raw:
            s.hacienda_p12_filename = None
        else:
            available = list_p12_files()
            if raw not in available:
                return jsonify({"error": f"El archivo .p12 no está en data/Llave: {raw}"}), 400
            s.hacienda_p12_filename = raw
    if fid and "invoice_hacienda_last_seq" in data and hasattr(s, "invoice_hacienda_last_seq"):
        try:
            v = int(data.get("invoice_hacienda_last_seq", 0))
        except (TypeError, ValueError):
            return jsonify({"error": "invoice_hacienda_last_seq debe ser un entero"}), 400
        if v < 0:
            return jsonify({"error": "El consecutivo no puede ser negativo"}), 400
        s.invoice_hacienda_last_seq = v
    db.session.commit()
    out = {
        "app_name": s.app_name,
        "logo_url": s.logo_url or "",
        "favicon_url": s.favicon_url or "",
        "nav_icon": s.nav_icon or "",
    }
    if fid:
        last = int(getattr(s, "invoice_hacienda_last_seq", 0) or 0)
        inv_count = Invoice.query.filter_by(franchisee_id=fid).count()
        fr = db.session.get(Franchisee, fid)
        out["franchisee_id"] = fid
        out["franchisee_code"] = fr.code if fr else ""
        out["franchisee_name"] = fr.name if fr else ""
        out["invoice_hacienda_last_seq"] = last
        out["invoice_hacienda_next_seq_preview"] = last + 1
        out["invoices_count_in_erp"] = inv_count
    out.update(_crypto_settings_payload(fid))
    return jsonify(out)


@settings_bp.route("/import-excel", methods=["POST"])
def import_excel():
    """Importa datos desde un archivo Excel. Form data: type, file, opcionalmente replace, replace_all, period_date."""
    if "file" not in request.files and "excel" not in request.files:
        return jsonify({"error": "No se envió ningún archivo"}), 400
    f = request.files.get("file") or request.files.get("excel")
    if not f or not f.filename or not f.filename.lower().endswith((".xlsx", ".xls")):
        return jsonify({"error": "Sube un archivo Excel (.xlsx)"}), 400
    import_type = (request.form.get("type") or "").strip().lower()
    if not import_type:
        return jsonify({"error": "Indica el tipo de importación"}), 400
    try:
        from utils.import_excel_api import IMPORT_HANDLERS
    except ImportError as e:
        return jsonify({"error": str(e)}), 500
    if import_type not in IMPORT_HANDLERS:
        return jsonify({"error": f"Tipo no válido: {import_type}"}), 400
    handler, extra_params = IMPORT_HANDLERS[import_type]
    file_bytes = f.read()
    if not file_bytes:
        return jsonify({"error": "Archivo vacío"}), 400
    fid = get_or_default_franchisee_id()
    opts = {"replace": request.form.get("replace", "").lower() in ("1", "true", "si", "yes")}
    if "replace_all" in extra_params:
        opts["replace_all"] = request.form.get("replace_all", "").lower() in ("1", "true", "si", "yes")
    if "period_date" in extra_params:
        from datetime import datetime
        pd = request.form.get("period_date", "").strip()
        opts["period_date"] = datetime.strptime(pd[:10], "%Y-%m-%d").date() if pd else None
    try:
        if import_type == "inventario":
            created, err = handler(file_bytes, fid, replace=opts["replace"])
        elif import_type == "planilla_ubicaciones":
            locs, entries, err = handler(
                file_bytes, fid,
                replace_all=opts.get("replace_all", False),
                period_date=opts.get("period_date"),
            )
            if err:
                return jsonify({"error": err}), 400
            return jsonify({
                "message": f"Importados {entries} registros en {locs} ubicaciones",
                "locations": locs,
                "entries": entries,
            }), 200
        elif import_type in ("casas", "unidades", "puestos", "tipos_registro", "tipos_deduccion"):
            created, err = handler(file_bytes)
        else:
            created, err = handler(file_bytes, fid)
        if err:
            return jsonify({"error": err}), 400
        return jsonify({"message": f"Importados {created} registros", "imported": created}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@settings_bp.route("/download-excel-templates", methods=["GET"])
def download_excel_templates():
    """Descarga un ZIP con todas las plantillas Excel para importar datos."""
    try:
        from utils.excel_templates import generate_all_as_zip
    except ImportError as e:
        return jsonify({"error": "openpyxl requerido: pip install openpyxl"}), 500
    try:
        data, filename = generate_all_as_zip()
        from io import BytesIO
        return send_file(
            BytesIO(data),
            mimetype="application/zip",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
