# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec — one-folder, windowed Windows build of ChemEng SimLab.

Build:  pyinstaller --clean --noconfirm ChemEng_SimLab.spec
Output: dist/ChemEng_SimLab/  (distribute the whole folder, e.g. zipped)
"""
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(
    ['scada_app/main.py'],
    pathex=['scada_app', '.'],          # resolve scada_app modules + reactor_simulation
    binaries=[],
    datas=[
        ('images/pfr/diagram.svg', 'images/pfr'),
        ('images/rtd/rtd_normal_operation.svg', 'images/rtd'),
        ('images/rtd/cip_r102.svg', 'images/rtd'),
        ('images/rtd/cip_r103.svg', 'images/rtd'),
        ('images/rtd/cip_r104.svg', 'images/rtd'),
        ('images/rtd/overlay_v106_green.svg', 'images/rtd'),
        ('scada_app/scenarios/plants', 'scada_app/scenarios/plants'),
        ('scada_app/scenarios/sensor.json', 'scada_app/scenarios'),
        ('scada_app/scenarios/pfr', 'scada_app/scenarios/pfr'),
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
    name='ChemEng_SimLab',
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
    name='ChemEng_SimLab',
)
