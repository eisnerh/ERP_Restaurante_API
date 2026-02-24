"""Esquemas de órdenes de compra."""
from extensions import ma
from models import PurchaseOrder, PurchaseOrderItem
from schemas.supplier_schema import SupplierSchema


class PurchaseOrderItemSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PurchaseOrderItem
        load_instance = True

    id = ma.auto_field()
    purchase_order_id = ma.auto_field()
    inventory_item_id = ma.auto_field()
    product_name = ma.auto_field()
    quantity = ma.auto_field()
    unit = ma.auto_field()
    unit_price = ma.auto_field()
    notes = ma.auto_field()


class PurchaseOrderSchema(ma.SQLAlchemySchema):
    class Meta:
        model = PurchaseOrder
        load_instance = True

    id = ma.auto_field()
    supplier_id = ma.auto_field()
    order_number = ma.auto_field()
    order_date = ma.auto_field()
    status = ma.auto_field()
    notes = ma.auto_field()
    total = ma.auto_field()
    supplier = ma.Nested(SupplierSchema)
    items = ma.Nested(PurchaseOrderItemSchema, many=True)
