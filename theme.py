# theme.py
import sys
from pathlib import Path
import tkinter as tk
from tkinter import font as tkfont

# ----------------------------------------------------------------------
# Bundled display font: Abril Fatface (SIL Open Font License, see fonts/).
# On Windows it is loaded for this program only, so nothing needs installing.
# ----------------------------------------------------------------------
BUNDLED_FONT = Path(__file__).parent / "fonts" / "AbrilFatface-Regular.ttf"

def _load_bundled_font():
    if sys.platform == "win32" and BUNDLED_FONT.exists():
        try:
            import ctypes
            ctypes.windll.gdi32.AddFontResourceExW(str(BUNDLED_FONT), 0x10, 0)   # 0x10 = private to this process
        except Exception:
            pass

_load_bundled_font()

# ----------------------------------------------------------------------
# Fonts: the first installed font in each list is used.
# Put the font you like best at the front of its list.
# ----------------------------------------------------------------------
HEADING_CHOICES = ["Abril Fatface", "Bodoni Moda", "Playfair Display", "Bodoni MT", "Didot", "Cormorant Garamond", "Georgia"]
BODY_CHOICES = ["Jost", "Montserrat", "Century Gothic", "Futura", "Segoe UI"]

def _installed_fonts():
    root = tk.Tk()
    root.withdraw()
    names = set(tkfont.families())
    root.destroy()
    return names

_INSTALLED = _installed_fonts()

def _pick(choices):
    for name in choices:
        if name in _INSTALLED:
            return name
    return choices[-1]

HEADING = _pick(HEADING_CHOICES)
BODY = _pick(BODY_CHOICES)

# Abril Fatface is already ultra-bold and has no italic, so it is used as-is
# (a fake bold or italic would only blur it). Other fonts get bold / bold italic.
HEAVY = HEADING == "Abril Fatface"
HEADING_STYLE = "" if HEAVY else "bold"
BRAND_STYLE = "" if HEAVY else "italic bold"

THEME = {
    "bg": "#FFFFFF",
    "surface": "#FFFFFF",
    "surface_subtle": "#EDEDED",
    "sidebar": "#000000",
    "sidebar_hover": "#222222",
    "sidebar_active": "#222222",
    "primary": "#000000",
    "primary_hover": "#333333",
    "text": "#000000",
    "text_muted": "#333333",
    "border": "#000000",
    "border_focus": "#000000",
    "danger": "#000000",
    "on_dark": "#FFFFFF",        # text on black areas
    "on_dark_muted": "#BBBBBB",  # secondary text on black areas
}

# everything bold
FONTS = {
    "title": (HEADING, 22, HEADING_STYLE),
    "subtitle": (HEADING, 16, HEADING_STYLE),
    "heading": (HEADING, 13, HEADING_STYLE),
    "body": (BODY, 11, "bold"),
    "body_bold": (BODY, 11, "bold"),
    "caption": (BODY, 9, "bold"),
    "brand": (HEADING, 24, BRAND_STYLE),
    "brand_small": (HEADING, 18, BRAND_STYLE),
}