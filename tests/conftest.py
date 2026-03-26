"""
pytest configuration for ScreenWatermark Pro v8.0 tests
"""

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
