"""API y rutas de configuración."""
from flask import Blueprint, request, jsonify
from extensions import db
from models import AppSettings
from utils.franchisee import get_or_default_franchisee_id

settings_bp = Blueprint("settings", __name__, url_prefix="/api/settings")


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
