"""Cupón de fidelización ligado a factura (descuento o regalía)."""
import secrets
from datetime import datetime, timezone

from extensions import db


class LoyaltyCoupon(db.Model):
    __tablename__ = "loyalty_coupons"
    __table_args__ = (
        db.Index("ix_loyalty_franchisee_invoice", "franchisee_id", "invoice_number"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey("payroll_locations.id"), nullable=True)
    invoice_number = db.Column(db.String(64), nullable=False)
    kind = db.Column(db.String(20), nullable=False)  # discount | reward
    discount_percent = db.Column(db.Numeric(5, 2), nullable=True)
    discount_amount = db.Column(db.Numeric(12, 2), nullable=True)
    reward_description = db.Column(db.String(500), nullable=True)
    public_token = db.Column(db.String(64), unique=True, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    redeemed_at = db.Column(db.DateTime, nullable=True)

    franchisee = db.relationship("Franchisee", backref=db.backref("loyalty_coupons", lazy="dynamic"))
    location = db.relationship("PayrollLocation", backref=db.backref("loyalty_coupons", lazy="dynamic"))

    @staticmethod
    def generate_token() -> str:
        return secrets.token_urlsafe(24)

    def __repr__(self):
        return f"<LoyaltyCoupon {self.invoice_number} {self.kind}>"
