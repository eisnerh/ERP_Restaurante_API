"""Modelos de la base de datos."""
from extensions import db

from .franchisee import Franchisee
from .category import Category
from .dish import Dish
from .table_model import Table
from .order import Order, OrderItem
from .cash_register import CashRegisterSession
from .operational_expense import OperationalExpense
from .invoice import Invoice, InvoiceItem
from .inventory import InventoryItem
from .inventory_alert import InventoryAlert
from .supplier import Supplier
from .client import Client
from .purchase import PurchaseOrder, PurchaseOrderItem
from .payroll_location import PayrollLocation
from .payroll_entry_type import PayrollEntryType
from .position import Position
from .deduction_type import DeductionType
from .employee import Employee
from .vacation_record import VacationRecord
from .payroll_entry import PayrollEntry
from .payslip import Payslip, PayslipLine
from .payment_record import PaymentRecord
from .unit import Unit
from .app_settings import AppSettings
from .holiday import Holiday
from .payment_method import PaymentMethod
from .discount_reason import DiscountReason
from .loyalty_coupon import LoyaltyCoupon

__all__ = [
    "Franchisee",
    "Category", "Dish", "Table", "Order", "OrderItem",
    "CashRegisterSession", "OperationalExpense", "Invoice", "InvoiceItem",
    "InventoryItem", "InventoryAlert", "Supplier",
    "Client", "PurchaseOrder", "PurchaseOrderItem",
    "PayrollLocation", "PayrollEntryType", "Position", "DeductionType", "Employee", "VacationRecord", "PayrollEntry",
    "Payslip", "PayslipLine",
    "PaymentRecord",
    "Unit",
    "AppSettings",
    "Holiday",
    "PaymentMethod",
    "DiscountReason",
    "LoyaltyCoupon",
]
