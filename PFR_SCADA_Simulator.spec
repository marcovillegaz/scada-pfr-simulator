# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — one-folder, windowed Windows build of the PFR SCADA Simulator.

Build:  pyinstaller --clean --noconfirm PFR_SCADA_Simulator.spec
Output: dist/PFR_SCADA_Simulator/  (distribute the whole folder, e.g. zipped)
"""
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['scada_app/main.py'],
    pathex=['scada_app', '.'],          # resolve scada_app modules + reactor_simulation
    binaries=[],
    datas=[
        ('images/diagram.svg', 'images'),
        ('images/rtd_diagram.svg', 'images'),
        ('scada_app/scenarios/plants', 'scada_app/scenarios/plants'),
    ],
    hiddenimports=collect_submodules('reactor_simulation'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PFR_SCADA_Simulator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,                      # windowed (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PFR_SCADA_Simulator',
)
