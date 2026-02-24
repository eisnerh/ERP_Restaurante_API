"""Utilidades para el franquiciado actual (sesión)."""
from flask import session


SESSION_KEY = "franchisee_id"


def get_current_franchisee_id():
    """Obtiene el ID del franquiciado actual desde la sesión."""
    return session.get(SESSION_KEY)


def set_current_franchisee_id(franchisee_id):
    """Establece el franquiciado actual en la sesión."""
    session[SESSION_KEY] = franchisee_id


def clear_current_franchisee():
    """Limpia el franquiciado actual."""
    session.pop(SESSION_KEY, None)


def get_or_default_franchisee_id():
    """
    Obtiene el franquiciado actual o el primero activo como predeterminado.
    Retorna None si no hay franquiciados.
    """
    fid = get_current_franchisee_id()
    if fid is not None:
        return fid
    from models import Franchisee
    first = Franchisee.query.filter_by(active=True).first()
    if first:
        set_current_franchisee_id(first.id)
        return first.id
    return None
