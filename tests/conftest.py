"""
pytest configuration for ScreenWatermark Pro v8.0 tests
"""

import io
import os
import sys
import tempfile
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_WM_PATH = None

def pytest_configure(config):
    global TEST_WM_PATH
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        from PIL import Image
        img = Image.new("RGBA", (100, 50), (255, 0, 0, 180))
        img.save(f.name, "PNG")
        TEST_WM_PATH = f.name

def pytest_unconfigure(config):
    global TEST_WM_PATH
    if TEST_WM_PATH and os.path.exists(TEST_WM_PATH):
        try:
            os.unlink(TEST_WM_PATH)
        except:
            pass

@pytest.fixture(scope="session")
def app_instance():
    from ui.main_window import ScreenWatermarkApp
    app = ScreenWatermarkApp()
    yield app
    try:
        app.destroy()
    except:
        pass

@pytest.fixture
def app(app_instance):
    app_instance.after(0, lambda: None)
    app_instance.update()
    return app_instance

WAIT_SHORT = 0.1
WAIT_MEDIUM = 0.3
WAIT_LONG = 1.0

def wait_for(widget, timeout=1.0):
    start = time.time()
    while time.time() - start < timeout:
        try:
            widget.winfo_exists()
            return True
        except:
            pass
        time.sleep(0.05)
    return False

def get_widget_text(widget):
    try:
        return str(widget.cget("text"))
    except:
        return ""

def widget_is_visible(widget):
    try:
        return widget.winfo_viewable()
    except:
        return False

def click_widget(app, widget):
    try:
        widget.invoke()
    except:
        pass

def find_toplevel(app, title_contains):
    for win in app.winfo_children():
        try:
            if title_contains.lower() in win.title().lower():
                return win
        except:
            pass
    return None

def make_fake_entry(entry_id=0):
    from datetime import datetime
    return {
        "id": entry_id,
        "timestamp": datetime.now().isoformat(),
        "wm_enabled": True,
        "ts_enabled": True,
        "wm_mode": "normal",
        "wm_scale": 1.0,
        "wm_opacity": 80,
        "wm_text": "Test",
        "wm_color": "#FF0000",
        "ts_format": "%Y-%m-%d %H:%M:%S",
        "ts_color": "#FFFFFF",
        "ts_size": 12,
        "ts_outside": False,
        "output_dir": "",
        "preview_path": None
    }

def get_canvas_image(canvas, x=0, y=0, width=1, height=1):
    try:
        from PIL import Image
        ps_data = canvas.postscript(colormode="color", x=x, y=y, width=width, height=height)
        img = Image.open(io.BytesIO(ps_data.encode('utf-8')))
        return img
    except:
        return None

def images_differ(img1, img2, threshold=0.01):
    if img1 is None or img2 is None:
        return True
    try:
        import numpy as np
        from PIL import Image
        if img1.size != img2.size:
            img2 = img2.resize(img1.size)
            img2 = img2.convert('RGBA')
        arr1 = np.array(img1.convert('RGBA'))
        arr2 = np.array(img2.convert('RGBA'))
        diff = np.abs(arr1.astype(float) - arr2.astype(float)).mean()
        return diff > threshold
    except:
        return True

def read_settings_json(path):
    import json
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except:
        return None

def get_clipboard_image():
    try:
        from PIL import Image, ImageGrab
        img = ImageGrab.grabclipboard()
        return img
    except:
        return None
