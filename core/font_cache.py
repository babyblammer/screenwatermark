"""
ScreenWatermark Pro - Core Font Cache Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import os
import sys
from functools import lru_cache

@lru_cache(maxsize=16)
def load_font(size: int, bold: bool = False) -> "ImageFont.ImageFont":
    """[P1] Cache hasil load per (size, bold) - TTF tidak dibaca ulang dari disk."""
    from PIL import ImageFont
    size = max(8, size)
    if sys.platform == "win32":
        paths = ["C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
                 "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf"]
    elif sys.platform == "darwin":
        paths = ["/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
                 "/System/Library/Fonts/Helvetica.ttc"]
    else:
        paths = ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
                 else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                 "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold
                 else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]
    for p in paths:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except (OSError, IOError): continue
    return ImageFont.load_default()
