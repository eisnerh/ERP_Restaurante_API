"""Puesto o cargo: empleado, administrador, administrativo, inventario o personalizado. Estándar global."""
from extensions import db


# Tipos base de puesto (no se eliminan)
POSITION_TYPES = ("empleado", "administrador", "administrativo", "inventario", "custom")

# CCSS Costa Rica: 10.83% trabajador (2026), 9.67% (2025). Incluye SEM+IVM.
DEFAULT_CCSS_PCT = 0.1083


class Position(db.Model):
    """Puesto/cargo estándar. Lista global compartida por todos los franquiciados."""
    __tablename__ = "positions"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(80), nullable=False, unique=True)  # ej. Líder de Cocina, Cajero, Gerente
    position_type = db.Column(db.String(30), nullable=False, default="empleado")  # empleado|administrador|administrativo|inventario|custom
    display_order = db.Column(db.Integer, default=0)

    # Salario y jornada para desglose automático
    salario_base = db.Column(db.Float)  # Salario mensual base (₡)
    horas_por_dia = db.Column(db.Float, default=8.0)  # Horas ordinarias por día
    dias_por_semana = db.Column(db.Float, default=6.0)  # Días laborales por semana (CR: 6)
    ccss_pct = db.Column(db.Float, default=DEFAULT_CCSS_PCT)  # % CCSS trabajador (ej. 0.1083 = 10.83%)
    aplicar_ccss = db.Column(db.Boolean, default=True)  # Si True, aplica deducción CCSS de ley; si False, no aplica

    def get_salary_breakdown(self):
        """
        Calcula el desglose salarial según salario_base, horas_por_dia y dias_por_semana.
        Retorna dict con: salario_mes, salario_quincena, salario_semana, salario_dia,
        salario_hora, horas_ordinarias_mes, dias_mes.
        """
        base = self.salario_base or 0
        if base <= 0:
            return None
        hpd = self.horas_por_dia or 8
        dps = self.dias_por_semana or 6
        # CR: ~4.33 semanas/mes, 26 días laborales (6*4.33), 208 hrs/mes
        semanas_mes = 4.33
        dias_mes = round(dps * semanas_mes, 1)  # ej. 26
        horas_mes = dias_mes * hpd  # ej. 208
        return {
            "salario_mes": round(base, 2),
            "salario_quincena": round(base / 2, 2),
            "salario_semana": round(base / semanas_mes, 2),
            "salario_dia": round(base / dias_mes, 2),
            "salario_hora": round(base / horas_mes, 2),
            "horas_ordinarias_mes": round(horas_mes, 1),
            "dias_mes": dias_mes,
        }

    def get_ccss_deduction(self, base_amount=None):
        """
        Calcula la deducción CCSS sobre el monto base.
        base_amount: salario bruto (mensual, quincenal, etc.). Si None, usa salario_base.
        """
        amt = base_amount if base_amount is not None else (self.salario_base or 0)
        pct = self.ccss_pct if self.ccss_pct is not None else DEFAULT_CCSS_PCT
        return round(amt * pct, 2) if amt > 0 else 0

    def __repr__(self):
        return f"<Position {self.name} ({self.position_type})>"
