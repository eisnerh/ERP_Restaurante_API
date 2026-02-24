"""API y rutas de configuración."""
import os
import uuid
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from extensions import db
from models import AppSettings
from utils.franchisee import get_or_default_franchisee_id

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


@settings_bp.route("", methods=["GET"])
def get_settings():
    """Obtiene la configuración actual (del franquiciado seleccionado)."""
    fid = get_or_default_franchisee_id()
    s = AppSettings.get(franchisee_id=fid)
    return jsonify({
        "app_name": s.app_name or "ERP Raul Castaño",
        "logo_url": s.logo_url or "",
        "favicon_url": s.favicon_url or "",
        "nav_icon": s.nav_icon or "",
    })


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
    db.session.commit()
    return jsonify({
        "app_name": s.app_name,
        "logo_url": s.logo_url or "",
        "favicon_url": s.favicon_url or "",
        "nav_icon": s.nav_icon or "",
    })
