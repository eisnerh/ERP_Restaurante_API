"""Esquema de proveedor."""
from extensions import ma
from models import Supplier


class SupplierSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Supplier
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    phone = ma.auto_field()
    contact = ma.auto_field()
    visit_day = ma.auto_field()
    visit_schedule = ma.auto_field()
