# -*- mode: python ; coding: utf-8 -*-
# Windows single-file release build.
# Produces: dist/StudyPoint.exe
# Build:    pyinstaller StudyPoint-release.spec

block_cipher = None

hidden_imports = [
    "PyQt5", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets", "PyQt5.sip",
    "dateutil", "dateutil.relativedelta", "dateutil.parser",
    "pywhatkit", "pyautogui",
    "openpyxl", "openpyxl.styles", "openpyxl.utils",
    "openpyxl.writer", "openpyxl.reader",
    "database", "styles",
    "ui.dashboard", "ui.seat_layout", "ui.student_management",
    "ui.payment_management", "ui.overdue_payments",
    "ui.removed_students", "ui.settings_panel",
    "utils.whatsapp", "utils.export",
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter", "matplotlib", "numpy", "scipy",
        "IPython", "notebook", "pytest", "setuptools", "pip",
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,      # include all binaries directly into the exe
    a.datas,
    [],
    name="StudyPoint",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # no black terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
