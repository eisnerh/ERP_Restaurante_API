"""Esquemas de inventario."""
from extensions import ma
from models import InventoryItem


class InventoryItemSchema(ma.SQLAlchemySchema):
    class Meta:
        model = InventoryItem
        load_instance = True

    id = ma.auto_field()
    franchisee_id = ma.auto_field()
    code = ma.auto_field()
    area = ma.auto_field()
    product_name = ma.auto_field()
    unit = ma.auto_field()
    existence = ma.auto_field()
    responsible = ma.auto_field()
    stock = ma.auto_field()
    order_quantity = ma.auto_field()
    supplier = ma.auto_field()
    purchase_price = ma.auto_field()
    supplier_ids = ma.Method("get_supplier_ids", dump_only=True)
    supplier_names = ma.Method("get_supplier_names", dump_only=True)

    def get_supplier_ids(self, obj):
        if obj is None or not hasattr(obj, "suppliers"):
            return []
        return [s.id for s in obj.suppliers]

    def get_supplier_names(self, obj):
        if obj is None or not hasattr(obj, "suppliers"):
            return []
        return [s.name for s in obj.suppliers]
