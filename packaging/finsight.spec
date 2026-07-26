# PyInstaller spec — native FinSight.app for macOS (target-product §23; ADR-001 §3, ADR-008 §3).
#   Windowed --onedir bundle over the single desktop entry (finsight.delivery.desktop.app:main).
#   PyInstaller's PySide6 hook bundles the Qt runtime + platform plugins (crucially cocoa); we collect
#   ALL finsight submodules because the app imports many of them lazily (service composition).
#   Local-only: no cloud SDKs are referenced anywhere (see tests/ai/test_confidentiality.py), so nothing
#   network-bound is bundled beyond the local Ollama HTTP client (urllib, stdlib).
import os
from PyInstaller.utils.hooks import collect_submodules

_here = os.path.dirname(os.path.abspath(SPEC))
_src = os.path.join(_here, "..", "src")

hiddenimports = collect_submodules("finsight")

a = Analysis(
    [os.path.join(_here, "finsight_launch.py")],
    pathex=[_src],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz, a.scripts, [],
    exclude_binaries=True,
    name="FinSight",
    console=False,            # windowed (no terminal window)
    disable_windowed_traceback=False,
    argv_emulation=True,      # macOS: forward Finder file-open args
)
coll = COLLECT(exe, a.binaries, a.datas, name="FinSight")

app = BUNDLE(
    coll,
    name="FinSight.app",
    icon=None,
    bundle_identifier="com.finsight.desktop",
    info_plist={
        "CFBundleName": "FinSight",
        "CFBundleDisplayName": "FinSight",
        "CFBundleShortVersionString": "1.0.0",
        "NSHighResolutionCapable": True,     # crisp on Retina
        "LSMinimumSystemVersion": "11.0",
        "LSApplicationCategoryType": "public.app-category.finance",
    },
)
