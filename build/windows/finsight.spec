# PyInstaller specification — FinSight Windows desktop build.
#
# Build (from the repository root, on Windows, inside the build venv):
#     pyinstaller --clean --noconfirm build/windows/finsight.spec
#
# Produces dist/FinSight/FinSight.exe (one-dir). One-dir is deliberate: it starts faster than
# one-file (no per-launch temp extraction of ~100 MB of Qt) and is what the Inno Setup installer
# in this directory packages.
import os
import sys

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(SPEC)), "..", ".."))
SRC = os.path.join(ROOT, "src")
HERE = os.path.join(ROOT, "build", "windows")

# The src/ layout is not installed into the build environment, so make it importable while this
# spec is evaluated. Without it collect_submodules() below silently returns nothing and the
# belt-and-braces migration collection would quietly cover no modules at all.
if SRC not in sys.path:
    sys.path.insert(0, SRC)

# QtAwesome ships its icon fonts and charmaps as package data and has no PyInstaller hook in
# pyinstaller-hooks-contrib. Without this the executable builds and launches, but every icon in
# the shell renders blank — collect the fonts explicitly.
datas = collect_data_files("qtawesome")

# sqlcipher3 is imported lazily inside a function (secure_store.open_encrypted_connection), so the
# static analyser can miss it; naming it here guarantees the encrypted store can be opened. The
# Windows wheel is a single self-contained .pyd — SQLCipher and its crypto are linked in, so there
# is no external DLL to collect alongside it.
hiddenimports = collect_submodules("sqlcipher3")

# Windows-only platform adapters that are reached through ctypes/late imports rather than a plain
# top-level import, plus the DPAPI/identity surface they depend on.
hiddenimports += ["ctypes", "ctypes.wintypes", "msvcrt"]

# The migration modules are registered statically in runner.MIGRATIONS, so the analyser follows
# them; collect_submodules is used anyway so an added migration cannot silently drop out of a build.
hiddenimports += collect_submodules("finsight.infrastructure.migrations")

# An optional branded icon. The build must not fail when it is absent, so it is only passed to the
# EXE when the file is actually present.
_icon = os.path.join(HERE, "finsight.ico")
icon = _icon if os.path.exists(_icon) else None

_version_file = os.path.join(HERE, "version_info.txt")
version = _version_file if os.path.exists(_version_file) else None


a = Analysis(
    [os.path.join(HERE, "finsight_win_entry.py")],
    pathex=[SRC],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Qt ships several large optional stacks FinSight never loads. Excluding them keeps the
    # installer materially smaller without touching anything the shell actually imports.
    excludes=[
        "tkinter",
        "PySide6.QtQuick3D",
        "PySide6.QtCharts",
        "PySide6.QtMultimedia",
        "PySide6.QtMultimediaWidgets",
        "PySide6.QtWebEngineCore",
        "PySide6.QtWebEngineWidgets",
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FinSight",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX-compressed binaries are a common false positive for AV scanners
    console=False,      # windowed application: no console window on launch
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon,
    version=version,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FinSight",
)
