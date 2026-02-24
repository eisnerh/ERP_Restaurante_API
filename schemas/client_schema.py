"""Esquema de cliente."""
from extensions import ma
from models import Client


class ClientSchema(ma.SQLAlchemySchema):
    class Meta:
        model = Client
        load_instance = True

    id = ma.auto_field()
    name = ma.auto_field()
    tax_id = ma.auto_field()
    email = ma.auto_field()
    phone = ma.auto_field()
    address = ma.auto_field()
    notes = ma.auto_field()
    active = ma.auto_field()
