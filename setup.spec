# Devil ERP — PyInstaller Build Spec
# Developed by Devil One Pvt Ltd & Nexuzy Lab
# Lead Developer: David K. Angel
#
# Build command: pyinstaller setup.spec
# Output: dist/DevilERP_Setup/

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
        ('ai/', 'ai'),
        ('ocr/', 'ocr'),
        ('backup/', 'backup'),
        ('auth/', 'auth'),
        ('reports/', 'reports'),
        ('installer/', 'installer'),
        ('hr/', 'hr'),
        ('tryton_modules/', 'tryton_modules'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui',
        'PySide6.QtPrintSupport',
        'transformers', 'sentence_transformers', 'llama_cpp',
        'pytesseract', 'cv2', 'fitz', 'PIL', 'PIL.Image',
        'pyrebase', 'google.auth', 'google.oauth2',
        'googleapiclient', 'googleapiclient.discovery',
        'reportlab', 'reportlab.platypus', 'reportlab.lib',
        'openpyxl', 'barcode', 'escpos',
        'psutil', 'sqlite3', 'psycopg2',
        'trytond', 'trytond.pool', 'trytond.model',
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
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
    version_file=None,
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
