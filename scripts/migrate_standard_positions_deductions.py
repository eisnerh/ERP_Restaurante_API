"""
Migración: Puestos y tipos de deducción estándar (global, sin franchisee_id).

Uso: python scripts/migrate_standard_positions_deductions.py
"""
import os
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
    from sqlalchemy import text, inspect

    with app.app_context():
        engine = db.engine
        insp = inspect(engine)

        # 1. Migrar positions a global
        if "positions" in insp.get_table_names():
            cols = [c["name"] for c in insp.get_columns("positions")]
            if "franchisee_id" in cols:
                print("Migrando positions a global...")
                with engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE positions_new (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(80) NOT NULL UNIQUE,
                            position_type VARCHAR(30) NOT NULL DEFAULT 'empleado',
                            display_order INTEGER DEFAULT 0
                        )
                    """))
                    conn.commit()
                    conn.execute(text("""
                        INSERT INTO positions_new (name, position_type, display_order)
                        SELECT DISTINCT ON (name) name, position_type, COALESCE(display_order,0)
                        FROM positions ORDER BY name, id
                    """))
                    conn.commit()
                    conn.execute(text("""
                        UPDATE employees e SET position_id = pn.id
                        FROM positions p, positions_new pn
                        WHERE e.position_id = p.id AND p.name = pn.name
                    """))
                    conn.commit()
                    conn.execute(text("""
                        UPDATE payroll_entries pe SET position_id = pn.id
                        FROM positions p, positions_new pn
                        WHERE pe.position_id = p.id AND p.name = pn.name
                    """))
                    conn.commit()
                    conn.execute(text("""
                        UPDATE payslips ps SET position_id = pn.id
                        FROM positions p, positions_new pn
                        WHERE ps.position_id = p.id AND p.name = pn.name
                    """))
                    conn.commit()
                    conn.execute(text("DROP TABLE positions CASCADE"))
                    conn.execute(text("ALTER TABLE positions_new RENAME TO positions"))
                    conn.commit()
                print("   Positions migrado.")
            else:
                print("   positions: ya migrado (sin franchisee_id)")

        # 2. Migrar deduction_types a global
        if "deduction_types" in insp.get_table_names():
            cols = [c["name"] for c in insp.get_columns("deduction_types")]
            if "franchisee_id" in cols:
                print("Migrando deduction_types a global...")
                with engine.connect() as conn:
                    conn.execute(text("""
                        CREATE TABLE deduction_types_new (
                            id SERIAL PRIMARY KEY,
                            name VARCHAR(120) NOT NULL UNIQUE,
                            description VARCHAR(200),
                            can_be_negative BOOLEAN DEFAULT FALSE,
                            is_hours_based BOOLEAN DEFAULT FALSE,
                            display_order INTEGER DEFAULT 0
                        )
                    """))
                    conn.commit()
                    conn.execute(text("""
                        INSERT INTO deduction_types_new (name, description, can_be_negative, is_hours_based, display_order)
                        SELECT DISTINCT ON (name) name, description, COALESCE(can_be_negative,false), COALESCE(is_hours_based,false), COALESCE(display_order,0)
                        FROM deduction_types ORDER BY name, id
                    """))
                    conn.commit()
                    conn.execute(text("""
                        UPDATE payslip_lines pl SET deduction_type_id = dn.id
                        FROM deduction_types d, deduction_types_new dn
                        WHERE pl.deduction_type_id = d.id AND d.name = dn.name
                    """))
                    conn.commit()
                    conn.execute(text("DROP TABLE deduction_types CASCADE"))
                    conn.execute(text("ALTER TABLE deduction_types_new RENAME TO deduction_types"))
                    conn.commit()
                print("   DeductionTypes migrado.")
            else:
                print("   deduction_types: ya migrado (sin franchisee_id)")

        print("\nMigración completada.")


if __name__ == "__main__":
    main()
