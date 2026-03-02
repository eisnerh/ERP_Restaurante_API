"""Esquemas Marshmallow para serialización."""
from .dish import DishSchema
from .category import CategorySchema, CategorySchemaNested
from .table_schema import TableSchema
from .order import OrderSchema, OrderItemSchema, OrderSchemaNested
from .inventory_schema import InventoryItemSchema
from .inventory_alert_schema import InventoryAlertSchema
from .supplier_schema import SupplierSchema
from .client_schema import ClientSchema
from .purchase_schema import PurchaseOrderSchema, PurchaseOrderItemSchema
from .payroll_schema import PayrollLocationSchema, PayrollEntrySchema, PayrollEntryTypeSchema
from .position_schema import PositionSchema
from .deduction_type_schema import DeductionTypeSchema
from .employee_schema import EmployeeSchema
from .vacation_record_schema import VacationRecordSchema
from .payslip_schema import PayslipSchema, PayslipLineSchema
from .payment_record_schema import PaymentRecordSchema
from .unit_schema import UnitSchema

__all__ = [
    "CategorySchema",
    "CategorySchemaNested",
    "DishSchema",
    "TableSchema",
    "OrderSchema",
    "OrderItemSchema",
    "OrderSchemaNested",
    "InventoryItemSchema",
    "InventoryAlertSchema",
    "SupplierSchema",
    "ClientSchema",
    "PurchaseOrderSchema",
    "PurchaseOrderItemSchema",
    "PayrollLocationSchema",
    "PayrollEntrySchema",
    "PayrollEntryTypeSchema",
    "PositionSchema",
    "DeductionTypeSchema",
    "EmployeeSchema",
    "VacationRecordSchema",
    "PayslipSchema",
    "PayslipLineSchema",
    "PaymentRecordSchema",
    "UnitSchema",
]
