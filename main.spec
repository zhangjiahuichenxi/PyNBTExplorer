# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['/Users/zhangjiahui/PycharmProjects/PyNBTExplorer/.venv/lib/python3.13/site-packages'],
    binaries=[],
    datas=[],
    hiddenimports=["nbtlib","platform","os","subprocess","re","pillow"],
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
    a.binaries,
    a.datas,
    [],
    name='PyNBTExplorer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='/Users/zhangjiahui/PycharmProjects/PyNBTExplorer/icon.png'
)