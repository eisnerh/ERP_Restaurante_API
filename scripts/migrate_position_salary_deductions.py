"""
Añade a Position: salario_base, horas_por_dia, dias_por_semana, ccss_pct.
Añade a DeductionType: rate_pct.
Actualiza CCSS Trabajador con rate_pct=0.1083.
Uso: python scripts/migrate_position_salary_deductions.py
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass


def main():
    from app import app
    from extensions import db

    with app.app_context():
        from sqlalchemy import text, inspect

        dialect = db.engine.dialect.name
        print(f"Conectado a: {dialect}")

        insp = inspect(db.engine)
        if "positions" not in insp.get_table_names():
            print("Tabla positions no existe. Ejecuta migrate_add_positions_deductions primero.")
            return

        # positions
        pos_cols = [c["name"] for c in insp.get_columns("positions")]
        # payslips.tipo_pago
        if "payslips" in insp.get_table_names():
            ps_cols = [c["name"] for c in insp.get_columns("payslips")]
            if "tipo_pago" not in ps_cols:
                db.session.execute(text("ALTER TABLE payslips ADD COLUMN tipo_pago VARCHAR(20) DEFAULT 'mensual'"))
                db.session.commit()
                print("  payslips.tipo_pago añadida.")

        for col, col_type, default in [
            ("salario_base", "REAL", None),
            ("horas_por_dia", "REAL", "8.0"),
            ("dias_por_semana", "REAL", "6.0"),
            ("ccss_pct", "REAL", "0.1083"),
            ("aplicar_ccss", "BOOLEAN", "TRUE"),
        ]:
            if col in pos_cols:
                print(f"  positions.{col} ya existe.")
            else:
                sql = f"ALTER TABLE positions ADD COLUMN {col} {col_type}"
                if default:
                    sql += f" DEFAULT {default}"
                db.session.execute(text(sql))
                db.session.commit()
                print(f"  positions.{col} añadida.")

        # deduction_types
        if "deduction_types" in insp.get_table_names():
            ded_cols = [c["name"] for c in insp.get_columns("deduction_types")]
            if "rate_pct" in ded_cols:
                print("  deduction_types.rate_pct ya existe.")
            else:
                db.session.execute(text("ALTER TABLE deduction_types ADD COLUMN rate_pct REAL"))
                db.session.commit()
                print("  deduction_types.rate_pct añadida.")

            # Actualizar CCSS Trabajador con rate 0.1083
            try:
                if dialect == "postgresql":
                    r = db.session.execute(text(
                        "UPDATE deduction_types SET rate_pct = 0.1083 WHERE name ILIKE '%CCSS%trabajador%' OR name = 'CCSS Trabajador'"
                    ))
                else:
                    r = db.session.execute(text(
                        "UPDATE deduction_types SET rate_pct = 0.1083 WHERE LOWER(name) LIKE '%ccss%trabajador%' OR name = 'CCSS Trabajador'"
                    ))
                db.session.commit()
                if r.rowcount:
                    print("  CCSS Trabajador actualizado con rate_pct=0.1083")
            except Exception as e:
                db.session.rollback()
                print("  Nota: no se pudo actualizar CCSS:", e)

        print("Migración completada.")


if __name__ == "__main__":
    main()
