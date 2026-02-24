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
from .payroll_schema import PayrollLocationSchema, PayrollEntrySchema
from .payslip_schema import PayslipSchema, PayslipLineSchema
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
    "PayslipSchema",
    "PayslipLineSchema",
    "UnitSchema",
]
