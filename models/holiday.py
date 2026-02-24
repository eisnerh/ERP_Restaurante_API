"""Feriados (días festivos) - se sincronizan automáticamente."""
from datetime import date
from extensions import db


class Holiday(db.Model):
    __tablename__ = "holidays"

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    country_code = db.Column(db.String(5), default="CR")  # CR = Costa Rica
    year = db.Column(db.Integer, nullable=False)  # Para búsquedas rápidas

    __table_args__ = (db.UniqueConstraint("date", "country_code", name="uq_holiday_date_country"),)

    def __repr__(self):
        return f"<Holiday {self.date} {self.name}>"
