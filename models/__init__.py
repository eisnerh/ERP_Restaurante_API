"""Modelos de la base de datos."""
from extensions import db

from .franchisee import Franchisee
from .category import Category
from .dish import Dish
from .table_model import Table
from .order import Order, OrderItem
from .inventory import InventoryItem
from .inventory_alert import InventoryAlert
from .supplier import Supplier
from .client import Client
from .purchase import PurchaseOrder, PurchaseOrderItem
from .payroll_location import PayrollLocation
from .position import Position
from .deduction_type import DeductionType
from .employee import Employee
from .vacation_record import VacationRecord
from .payroll_entry import PayrollEntry
from .payslip import Payslip, PayslipLine
from .unit import Unit
from .app_settings import AppSettings
from .holiday import Holiday

__all__ = [
    "Franchisee",
    "Category", "Dish", "Table", "Order", "OrderItem",
    "InventoryItem", "InventoryAlert", "Supplier",
    "Client", "PurchaseOrder", "PurchaseOrderItem",
    "PayrollLocation", "Position", "DeductionType", "Employee", "VacationRecord", "PayrollEntry",
    "Payslip", "PayslipLine",
    "Unit",
    "AppSettings",
    "Holiday",
]
