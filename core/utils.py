"""
ScreenWatermark Pro - Core Utils Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import re
from datetime import datetime

def safe_hex_to_rgb(h: str) -> tuple:
    try:
        h = h.strip().lstrip("#")
        if len(h) == 3: h = h[0]*2+h[1]*2+h[2]*2
        if len(h) != 6 or not re.fullmatch(r"[0-9a-fA-F]{6}", h):
            return (255,255,255)
        return tuple(int(h[i:i+2],16) for i in (0,2,4))
    except: return (255,255,255)

def safe_strftime(fmt: str, dt: datetime) -> str:
    try: return dt.strftime(fmt)
    except: return dt.strftime("%Y-%m-%d %H:%M:%S")
