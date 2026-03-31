"""
ScreenWatermark Pro - System Tray Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

from PIL import Image, ImageDraw
import pystray

_app_ref_notify: list = []   # diisi setelah app siap (untuk kompatibilitas)

def _win_toast(title: str, message: str, on_click_show: bool = False) -> bool:
    """Selalu return False — delegasikan ke pystray.notify() di caller."""
    return False


# ── Tray icon ─────────────────────────────────────────────────────────────────
def _make_tray_icon() -> "Image.Image":
    img = Image.new("RGBA", (32, 32), (0,0,0,0))
    d   = ImageDraw.Draw(img)
    d.rounded_rectangle([1,1,30,30], radius=4, fill="#6c63ff")
    d.rectangle([6,10,26,22], outline="white", width=2)
    d.ellipse([13,13,19,19], fill="white")
    d.polygon([(22,18),(26,22),(26,18)], fill="#43e97b")
    return img

