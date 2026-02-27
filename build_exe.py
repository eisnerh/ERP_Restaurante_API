"""
Genera el ejecutable ERP_Restaurant.exe con PyInstaller.
Requisitos: pip install pyinstaller
Ejecutar: python build_exe.py
"""
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent


def main():
    # Crear icono si no existe (opcional)
    icon_path = PROJECT_ROOT / "icon.ico"
    if not icon_path.exists():
        try:
            print("Creando icono...")
            subprocess.check_call([sys.executable, str(PROJECT_ROOT / "scripts" / "crear_icono.py")], cwd=str(PROJECT_ROOT))
        except Exception:
            print("(Icono omitido, continuando...)")

    try:
        import PyInstaller
    except ImportError:
        print("Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        import PyInstaller

    print("Generando ejecutable...")
    result = subprocess.run(
        [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(PROJECT_ROOT / "restaurant_api.spec"),
        ],
        cwd=str(PROJECT_ROOT),
    )
    if result.returncode == 0:
        exe_path = PROJECT_ROOT / "dist" / "ERP_Restaurant.exe"
        print(f"\n✓ Ejecutable creado: {exe_path}")
        print("\nPara usar:")
        print("  1. Copia .env (o .env.example) junto al .exe")
        print("  2. Configura PostgreSQL en .env")
        print("  3. Ejecuta ERP_Restaurant.exe")
    else:
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
