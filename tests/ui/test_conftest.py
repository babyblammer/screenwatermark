# tests/conftest.py
"""
Shared fixtures and helpers — ScreenWatermark Pro v8.0 modular package.

Place this file at:  screenwatermark/tests/conftest.py

Import resolution assumes tests are run from the project root:
    cd screenwatermark/
    pytest tests/ ...
"""

import sys
import os
import time
import json
import threading
from pathlib import Path
from typing import Generator

import pytest
import pyautogui
from PIL import Image, ImageChops

# ── Path setup ────────────────────────────────────────────────────────────────
# Project root = screenwatermark/ (one level above tests/)
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

# ── Constants ─────────────────────────────────────────────────────────────────
# Import from modular core/ after M1
try:
    from core.constants import SETTINGS_FILE, HISTORY_FILE
except ImportError:
    # Fallback if running pre-M1 (monolith still in place)
    SETTINGS_FILE = Path.home() / ".screenwatermark_settings.json"
    HISTORY_FILE  = Path.home() / ".screenwatermark_history.json"

LOCK_FILE    = Path.home() / ".screenwatermark_instance.lock"
TEST_WM_PATH = Path(__file__).parent / "assets" / "test_watermark.png"

WAIT_SHORT  = 0.3
WAIT_MEDIUM = 0.8
WAIT_LONG   = 2.0


# ── App fixture (GUI tests only — Tier 2) ─────────────────────────────────────
@pytest.fixture(scope="session")
def app_instance():
    """
    Launch ScreenWatermarkApp in-process on a background thread.
    Session-scoped: one instance for the entire GUI test session.

    Requires M1–M3 complete (modular package) before use.
    Import path: ui.main_window.ScreenWatermarkApp
    """
    for f in [SETTINGS_FILE, HISTORY_FILE, LOCK_FILE]:
        f.unlink(missing_ok=True)

    _ensure_test_watermark()

    # Import from modular package (available after M3)
    from ui.main_window import ScreenWatermarkApp

    app_ref = []
    ready   = threading.Event()

    def _run():
        app = ScreenWatermarkApp()
        app_ref.append(app)
        ready.set()
        app.mainloop()

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    ready.wait(timeout=15)
    assert app_ref, "App failed to start within 15 seconds"
    app = app_ref[0]
    time.sleep(0.5)
    yield app

    try:
        app.after(0, app._quit_app)
    except Exception:
        pass


@pytest.fixture(scope="function")
def app(app_instance):
    """Function-scoped: resets state between tests."""
    a = app_instance
    a.after(0, lambda: a.wm_enabled.set(True))
    a.after(0, lambda: a.wm_mode.set("normal"))
    a.after(0, lambda: a.wm_opacity.set(70))
    a.after(0, lambda: a.wm_scale.set(20))
    a.after(0, lambda: a.wm_position.set("bottom-left"))
    a.after(0, lambda: a.ts_enabled.set(True))
    a.after(0, lambda: a.ts_outside_canvas.set(False))
    a.after(0, lambda: a.watermark_path.set(str(TEST_WM_PATH)))
    time.sleep(WAIT_SHORT)
    return a


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ensure_test_watermark():
    """Create 200×100 solid red RGBA test watermark PNG."""
    TEST_WM_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not TEST_WM_PATH.exists():
        img = Image.new("RGBA", (200, 100), (255, 0, 0, 180))
        img.save(TEST_WM_PATH)


def wait_for(condition_fn, timeout=3.0, interval=0.1) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition_fn():
            return True
        time.sleep(interval)
    return False


def get_widget_text(widget) -> str:
    try:
        return widget.cget("text")
    except Exception:
        return ""


def widget_is_visible(widget) -> bool:
    try:
        return bool(widget.winfo_ismapped())
    except Exception:
        return False


def read_settings_json() -> dict:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def read_history_json() -> list:
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_canvas_image(app) -> Image.Image:
    app.update_idletasks()
    x = app.preview_canvas.winfo_rootx()
    y = app.preview_canvas.winfo_rooty()
    w = app.preview_canvas.winfo_width()
    h = app.preview_canvas.winfo_height()
    return pyautogui.screenshot(region=(x, y, w, h))


def get_clipboard_image() -> "Image.Image | None":
    try:
        import win32clipboard, win32con, io
        win32clipboard.OpenClipboard()
        try:
            data = win32clipboard.GetClipboardData(win32con.CF_DIB)
        finally:
            win32clipboard.CloseClipboard()
        header = (b'BM' + (len(data) + 14).to_bytes(4, 'little') +
                  b'\x00\x00\x00\x00\x36\x00\x00\x00')
        return Image.open(io.BytesIO(header + data))
    except Exception:
        return None


def pixel_region_has_color(img: Image.Image, region: tuple,
                            target_rgb: tuple, tolerance: int = 30) -> bool:
    cropped = img.crop(region).convert("RGB")
    for pixel in cropped.getdata():
        if all(abs(pixel[i] - target_rgb[i]) <= tolerance for i in range(3)):
            return True
    return False


def images_differ(img1: Image.Image, img2: Image.Image,
                  threshold: int = 5) -> bool:
    if img1.size != img2.size:
        return True
    diff = ImageChops.difference(img1.convert("RGB"), img2.convert("RGB"))
    return any(v > threshold for v in diff.getextrema()[0])


def click_widget(app, widget):
    app.update_idletasks()
    x = widget.winfo_rootx() + widget.winfo_width()  // 2
    y = widget.winfo_rooty() + widget.winfo_height() // 2
    pyautogui.click(x, y)
    time.sleep(WAIT_SHORT)


def find_toplevel(app, title_contains: str):
    for widget in app.winfo_children():
        try:
            if title_contains.lower() in widget.title().lower():
                return widget
        except Exception:
            continue
    return None


def make_fake_entry() -> dict:
    """Create a fake history entry for testing."""
    import uuid
    from datetime import datetime
    buf = __import__('io').BytesIO()
    Image.new("RGB", (800, 600), (60, 60, 90)).save(buf, "PNG")
    full = buf.getvalue()
    buf2 = __import__('io').BytesIO()
    Image.new("RGB", (96, 54), (60, 60, 90)).save(buf2, "JPEG", quality=80)
    thumb = buf2.getvalue()
    return {
        "entry_id":    str(uuid.uuid4()),
        "thumb_bytes": thumb,
        "full_bytes":  full,
        "timestamp":   datetime.now(),
        "width": 800, "height": 600,
    }
