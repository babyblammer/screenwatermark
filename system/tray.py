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
    img = Image.new("RGBA", (64, 64), (0,0,0,0))
    d   = ImageDraw.Draw(img)
    d.rounded_rectangle([2,2,62,62], radius=12, fill="#6c63ff")
    d.rectangle([12,20,52,44], outline="white", width=3)
    d.ellipse([26,26,38,38], fill="white")
    d.polygon([(44,36),(52,44),(52,36)], fill="#43e97b")
    return img

