"""Modelo de ítem de inventario (salón y cocina)."""
from extensions import db

# Tabla asociación: un ítem puede tener varios proveedores
item_suppliers = db.Table(
    "item_suppliers",
    db.Column("inventory_item_id", db.Integer, db.ForeignKey("inventory_items.id"), primary_key=True),
    db.Column("supplier_id", db.Integer, db.ForeignKey("suppliers.id"), primary_key=True),
)


# Unidades de medida válidas
INVENTORY_UNITS = ("KG", "GR", "CJ", "UND")


class InventoryItem(db.Model):
    __tablename__ = "inventory_items"

    id = db.Column(db.Integer, primary_key=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    code = db.Column(db.String(50))
    area = db.Column(db.String(20), nullable=False)  # "salon" | "cocina"
    product_name = db.Column(db.String(200), nullable=False)
    unit = db.Column(db.String(10), default="UND")  # KG, GR, CJ, UND
    existence = db.Column(db.Float, default=0)   # Existencia
    stock = db.Column(db.Float, default=0)       # Stock / cantidad en inventario
    order_quantity = db.Column(db.Float, default=None)  # Pedido sugerido (opcional)
    supplier = db.Column(db.String(120))  # Texto libre / primer proveedor (legacy)
    responsible = db.Column(db.String(120))  # Responsable del ítem (ej. Arlen Nuñez)
    purchase_price = db.Column(db.Float, default=None)  # Último precio de compra (histórico)

    franchisee = db.relationship("Franchisee", backref="inventory_items")
    suppliers = db.relationship(
        "Supplier",
        secondary=item_suppliers,
        backref=db.backref("inventory_items", lazy="dynamic"),
        lazy="select",
    )

    def __repr__(self):
        return f"<InventoryItem {self.product_name} ({self.area})>"
