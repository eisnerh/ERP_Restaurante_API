"""Configuración de la aplicación (nombre, logo, etc.)."""
from sqlalchemy.exc import IntegrityError

from extensions import db


class AppSettings(db.Model):
    """Configuración global (franchisee_id=null) o por franquiciado."""
    __tablename__ = "app_settings"
    __table_args__ = (
        # Una sola fila de ajustes por franquicia (PostgreSQL permite varias con franchisee_id NULL).
        db.UniqueConstraint("franchisee_id", name="uq_app_settings_franchisee_id"),
    )

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=True)  # null = global
    app_name = db.Column(db.String(120), default="ERP Raul Castaño")
    logo_url = db.Column(db.String(500))
    favicon_url = db.Column(db.String(500))
    nav_icon = db.Column(db.String(50))
    # Facturación Hacienda: nombre del .p12 dentro de data/Llave (null = usar el primero encontrado)
    hacienda_p12_filename = db.Column(db.String(255), nullable=True)
    # Último número secuencial interno ya usado en facturas alineado con Hacienda (por franquicia).
    # La siguiente emisión usa invoice_hacienda_last_seq + 1 y luego actualiza este valor.
    invoice_hacienda_last_seq = db.Column(db.Integer, nullable=False, default=0)

    franchisee = db.relationship("Franchisee", backref="app_settings")

    @classmethod
    def get(cls, franchisee_id=None):
        """Obtiene la configuración para el franquiciado (o global si franchisee_id=None)."""
        if franchisee_id:
            s = cls.query.filter_by(franchisee_id=franchisee_id).order_by(cls.id.asc()).first()
        else:
            s = cls.query.filter_by(franchisee_id=None).order_by(cls.id.asc()).first()
        if not s:
            s = cls(franchisee_id=franchisee_id)
            db.session.add(s)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                if franchisee_id:
                    s = cls.query.filter_by(franchisee_id=franchisee_id).order_by(cls.id.asc()).first()
                else:
                    s = cls.query.filter_by(franchisee_id=None).order_by(cls.id.asc()).first()
        return s
