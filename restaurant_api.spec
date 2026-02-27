# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para ERP Restaurant
# Ejecutar: python build_exe.py  o  pyinstaller restaurant_api.spec

import sys
from pathlib import Path

# Icono opcional
_icon = Path('icon.ico')
icon_param = str(_icon) if _icon.exists() else None

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
    excludes=['IPython', 'matplotlib', 'jedi', 'parso', 'PIL.ImageQt', 'tkinter'],
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
    icon=icon_param,
)
