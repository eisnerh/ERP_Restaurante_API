"""Modelos de pedido y línea de pedido."""
from extensions import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    table_id = db.Column(db.Integer, db.ForeignKey("tables.id"), nullable=False)
    status = db.Column(db.String(20), default="pending")  # pending, preparing, served, paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(300))

    items = db.relationship("OrderItem", backref="order", lazy="dynamic", cascade="all, delete-orphan")

    def total(self):
        return sum(item.subtotal() for item in self.items)

    def __repr__(self):
        return f"<Order {self.id} Table {self.table_id}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey("dishes.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)  # precio en el momento del pedido

    dish = db.relationship("Dish", backref="order_items")

    def subtotal(self):
        return self.quantity * self.unit_price

    def __repr__(self):
        return f"<OrderItem order={self.order_id} dish={self.dish_id} qty={self.quantity}>"
