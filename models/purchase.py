"""Modelos de órdenes de compra (ERP)."""
from datetime import datetime
from extensions import db


class PurchaseOrder(db.Model):
    __tablename__ = "purchase_orders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.id"), nullable=False)
    order_number = db.Column(db.String(50))
    order_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="draft")  # draft, sent, received, cancelled
    notes = db.Column(db.String(500))
    total = db.Column(db.Float, default=0)

    franchisee = db.relationship("Franchisee", backref="purchase_orders")
    supplier = db.relationship("Supplier", backref="purchase_orders")

    __table_args__ = (db.UniqueConstraint("franchisee_id", "order_number", name="uq_po_franchisee_number"),)
    items = db.relationship(
        "PurchaseOrderItem",
        backref="purchase_order",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def recalc_total(self):
        self.total = sum(item.subtotal() for item in self.items)

    def __repr__(self):
        return f"<PurchaseOrder {self.order_number or self.id}>"


class PurchaseOrderItem(db.Model):
    __tablename__ = "purchase_order_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey("purchase_orders.id"), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey("inventory_items.id"), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)  # Por si no está en inventario
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit = db.Column(db.String(20), default="UND")
    unit_price = db.Column(db.Float, nullable=False, default=0)
    notes = db.Column(db.String(200))

    inventory_item = db.relationship("InventoryItem", backref="purchase_items")

    def subtotal(self):
        return self.quantity * self.unit_price

    def __repr__(self):
        return f"<PurchaseOrderItem {self.product_name} x{self.quantity}>"
