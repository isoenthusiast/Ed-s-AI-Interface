# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Ed's AI Interface — Desktop GUI.
Build with: pyinstaller EdAI.spec
"""

import sys
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────
# SPECPATH is provided by PyInstaller — it's the directory containing the .spec file
PROJECT_ROOT = Path(SPECPATH).resolve()
SRC_DIR = PROJECT_ROOT / "src"

# ── Hidden imports (modules PyInstaller can't auto-detect) ────────
hiddenimports = [
    # === customtkinter v6.0.0 internals ===
    "customtkinter",
    "customtkinter.windows",
    "customtkinter.windows.ctk_input_dialog",
    "customtkinter.windows.ctk_tk",
    "customtkinter.windows.ctk_toplevel",
    "customtkinter.windows.widgets",
    "customtkinter.windows.widgets.appearance_mode",
    "customtkinter.windows.widgets.appearance_mode.appearance_mode_base_class",
    "customtkinter.windows.widgets.appearance_mode.appearance_mode_tracker",
    "customtkinter.windows.widgets.core_rendering",
    "customtkinter.windows.widgets.core_rendering.ctk_canvas",
    "customtkinter.windows.widgets.core_rendering.draw_engine",
    "customtkinter.windows.widgets.core_widget_classes",
    "customtkinter.windows.widgets.core_widget_classes.ctk_base_class",
    "customtkinter.windows.widgets.core_widget_classes.dropdown_menu",
    "customtkinter.windows.widgets.font",
    "customtkinter.windows.widgets.font.ctk_font",
    "customtkinter.windows.widgets.font.font_manager",
    "customtkinter.windows.widgets.image",
    "customtkinter.windows.widgets.image.ctk_image",
    "customtkinter.windows.widgets.scaling",
    "customtkinter.windows.widgets.scaling.scaling_base_class",
    "customtkinter.windows.widgets.scaling.scaling_tracker",
    "customtkinter.windows.widgets.theme",
    "customtkinter.windows.widgets.theme.theme_manager",
    "customtkinter.windows.widgets.utility",
    "customtkinter.windows.widgets.utility.utility_functions",
    # === OpenAI / HTTP client ===
    "openai",
    "httpx",
    "httpcore",
    "h11",
    # === PIL / Pillow ===
    "PIL",
    "PIL.Image",
    "PIL.ImageTk",
    "PIL.ImageDraw",
    "PIL.ImageFont",
    # === Attachments ===
    "PyPDF2",
    "docx",
    # === duckduckgo-search ===
    "duckduckgo_search",
    # === Standard library modules sometimes missed ===
    "tkinter",
    "tkinter.ttk",
    "tkinter.font",
    "tkinter.messagebox",
    "tkinter.filedialog",
    "tkinter.simpledialog",
    "tkinter.scrolledtext",
    "json",
    "sqlite3",
    "hashlib",
    "uuid",
    "re",
    "threading",
    "queue",
    "datetime",
    "pathlib",
    "traceback",
    "io",
    "base64",
]

# ── Collect data files ────────────────────────────────────────────
datas = []

# Collect customtkinter theme files
try:
    import customtkinter as ctk
    ctk_dir = Path(ctk.__file__).parent
    theme_dir = ctk_dir / "assets" / "themes"
    if theme_dir.exists():
        datas.append((str(theme_dir), "customtkinter/assets/themes"))
except Exception:
    pass

# ── Collect binaries ──────────────────────────────────────────────
binaries = []

# ── Exclude heavy/unused modules ─────────────────────────────────
excludes = [
    "matplotlib",
    "pandas",
    "jupyter",
    "IPython",
    "notebook",
    "nbformat",
    "pytest",
    "setuptools",
    "pip",
    "wheel",
    "tkinter.test",
    "unittest",
    "test",
    "tests",
]

# ── Analysis ─────────────────────────────────────────────────────
a = Analysis(
    [str(PROJECT_ROOT / "gui_main.py")],
    pathex=[str(PROJECT_ROOT), str(SRC_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
    optimize=0,
)

# ── PYZ ──────────────────────────────────────────────────────────
pyz = PYZ(a.pure)

# ── EXE ──────────────────────────────────────────────────────────
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Ed's AI Interface",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,              # Add icon path here if you have one
)
