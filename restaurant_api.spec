# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para ERP Restaurant
# Ejecutar: pyinstaller restaurant_api.spec

import sys

# En Windows, usar ; como separador para datas
sep = ';' if sys.platform == 'win32' else ':'

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('static', 'static'),
    ],
    hiddenimports=[
        'flask', 'flask.json', 'flask.templating', 'jinja2', 'werkzeug',
        'sqlalchemy', 'sqlalchemy.dialects.postgresql', 'sqlalchemy.dialects.sqlite',
        'psycopg2', 'pyodbc', 'openpyxl', 'reportlab', 'reportlab.pdfbase.ttfonts',
        'marshmallow', 'flask_sqlalchemy', 'flask_marshmallow', 'marshmallow_sqlalchemy',
        'dotenv', 'holidays',
        'routes', 'routes.menu', 'routes.orders', 'routes.tables', 'routes.inventory',
        'routes.payroll', 'routes.web', 'routes.clients', 'routes.purchases',
        'routes.settings', 'routes.franchisees', 'routes.expenses', 'routes.holidays',
        'models', 'schemas', 'utils.franchisee', 'utils.holidays_sync', 'utils.payslip_pdf',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='ERP_Restaurant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # True = ventana consola (ver logs), False = sin consola
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Puedes añadir 'icon.ico' si tienes un icono
)
