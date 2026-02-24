"""Modelo de notificación por inventario bajo."""
from datetime import datetime
from extensions import db


class InventoryAlert(db.Model):
    __tablename__ = "inventory_alerts"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    threshold = db.Column(db.Float, nullable=False)   # ej. 0.1 = 10%
    item_count = db.Column(db.Integer, default=0)
    # Snapshot de los ítems que estaban bajo stock en el momento de la alerta (JSON)
    items_snapshot = db.Column(db.JSON, default=list)

    franchisee = db.relationship("Franchisee", backref="inventory_alerts")

    def __repr__(self):
        return f"<InventoryAlert {self.id} {self.item_count} ítems @ {self.created_at}>"
