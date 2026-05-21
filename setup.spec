# -*- mode: python ; coding: utf-8 -*-
# Devil ERP — PyInstaller Build Spec
# Run: pyinstaller setup.spec

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('assets/', 'assets'),
        ('models/', 'models'),
        ('database/', 'database'),
        ('core/', 'core'),
        ('ui/', 'ui'),
        ('billing/', 'billing'),
        ('accounting/', 'accounting'),
        ('inventory/', 'inventory'),
        ('hr/', 'hr'),
        ('backup/', 'backup'),
        ('auth/', 'auth'),
        ('ocr/', 'ocr'),
        ('reports/', 'reports'),
        ('installer/', 'installer'),
    ],
    hiddenimports=[
        'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui',
        'PySide6.QtPrintSupport',
        'transformers', 'sentence_transformers', 'llama_cpp',
        'pytesseract', 'cv2', 'fitz', 'PIL', 'PIL.Image',
        'pyrebase', 'google.auth', 'googleapiclient',
        'reportlab', 'openpyxl', 'psutil',
        'trytond', 'trytond.model', 'trytond.pool',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'jupyter', 'IPython'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='DevilERP',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='DevilERP_Setup',
)
