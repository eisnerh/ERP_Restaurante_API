"""Blueprints de la API y de la interfaz web."""
from .menu import menu_bp
from .orders import orders_bp
from .tables import tables_bp
from .inventory import inventory_bp
from .payroll import payroll_bp
from .web import web_bp

__all__ = ["menu_bp", "orders_bp", "tables_bp", "inventory_bp", "payroll_bp", "web_bp"]
