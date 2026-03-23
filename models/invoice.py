"""Modelos de facturación electrónica."""
from datetime import datetime
from extensions import db


class Invoice(db.Model):
    """Factura emitida desde un pedido (FE, TE, NC, ND)."""
    __tablename__ = "invoices"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=True)
    tipo_documento = db.Column(db.String(5), nullable=False)  # FE, TE, NC, ND
    clave = db.Column(db.String(50), unique=True, nullable=True)
    consecutivo = db.Column(db.String(50), nullable=True)
    estado_hacienda = db.Column(db.String(50), nullable=True)  # aceptado, rechazado, pendiente
    xml_content = db.Column(db.Text, nullable=True)
    pdf_path = db.Column(db.String(500), nullable=True)
    is_simulated = db.Column(db.Boolean, default=False)
    total = db.Column(db.Numeric(12, 2), nullable=True)
    subtotal = db.Column(db.Numeric(12, 2), nullable=True)
    impuesto = db.Column(db.Numeric(12, 2), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    franchisee = db.relationship("Franchisee", backref="invoices")
    cliente = db.relationship("Client", backref="invoices")
    order = db.relationship("Order", backref="invoices")
    items = db.relationship("InvoiceItem", backref="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice {self.id} {self.consecutivo}>"


class InvoiceItem(db.Model):
    """Línea de factura."""
    __tablename__ = "invoice_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey("invoices.id"), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey("dishes.id"), nullable=True)
    description = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    unit_price = db.Column(db.Numeric(12, 2), nullable=False)
    subtotal = db.Column(db.Numeric(12, 2), nullable=True)
    tax = db.Column(db.Numeric(12, 2), nullable=True)

    dish = db.relationship("Dish", backref="invoice_items")

    def __repr__(self):
        return f"<InvoiceItem {self.id} {self.description}>"
