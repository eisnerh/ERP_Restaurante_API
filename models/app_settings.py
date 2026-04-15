"""Configuración de la aplicación (nombre, logo, etc.)."""
from extensions import db


class AppSettings(db.Model):
    """Configuración global (franchisee_id=null) o por franquiciado."""
    __tablename__ = "app_settings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    franchisee_id = db.Column(db.Integer, db.ForeignKey("franchisees.id"), nullable=True)  # null = global
    app_name = db.Column(db.String(120), default="ERP Raul Castaño")
    logo_url = db.Column(db.String(500))
    favicon_url = db.Column(db.String(500))
    nav_icon = db.Column(db.String(50))
    # Facturación Hacienda: nombre del .p12 dentro de data/Llave (null = usar el primero encontrado)
    hacienda_p12_filename = db.Column(db.String(255), nullable=True)

    franchisee = db.relationship("Franchisee", backref="app_settings")

    @classmethod
    def get(cls, franchisee_id=None):
        """Obtiene la configuración para el franquiciado (o global si franchisee_id=None)."""
        if franchisee_id:
            s = cls.query.filter_by(franchisee_id=franchisee_id).first()
        else:
            s = cls.query.filter_by(franchisee_id=None).first()
        if not s:
            s = cls(franchisee_id=franchisee_id)
            db.session.add(s)
            db.session.commit()
        return s
