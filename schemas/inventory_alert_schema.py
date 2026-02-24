"""Esquemas para alertas de inventario."""
from extensions import ma
from models import InventoryAlert


class InventoryAlertSchema(ma.SQLAlchemySchema):
    class Meta:
        model = InventoryAlert
        load_instance = True

    id = ma.auto_field()
    created_at = ma.auto_field()
    threshold = ma.auto_field()
    item_count = ma.auto_field()
    items_snapshot = ma.auto_field()
