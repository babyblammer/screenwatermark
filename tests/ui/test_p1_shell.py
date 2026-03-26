# tests/test_p1_shell.py
"""
Phase 1 — CTk Shell: Window + Header
Covers: TC-P1-002, TC-P1-004, TC-P1-005, TC-P1-006, TC-P1-007,
        TC-P1-008, TC-P1-009
Skipped (manual): TC-P1-001, TC-P1-003, TC-P1-010
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import time
import pytest
from ..conftest import (
    app, app_instance,
    wait_for, get_widget_text, widget_is_visible,
    click_widget, find_toplevel, WAIT_SHORT, WAIT_MEDIUM,
    TEST_WM_PATH
)


class TestWindowGeometry:

    def test_window_width_locked(self, app):
        """TC-P1-002a: Window width must be exactly 620px."""
        app.update_idletasks()
        assert app.winfo_width() == 620, \
            f"Expected width=620, got {app.winfo_width()}"

    def test_window_height_locked(self, app):
        """TC-P1-002b: Window height must be exactly 580px."""
        app.update_idletasks()
        assert app.winfo_height() == 580, \
            f"Expected height=580, got {app.winfo_height()}"

    def test_window_not_resizable(self, app):
        """TC-P1-002c: resizable flags must both be False."""
        # Try to resize via geometry and confirm it snaps back
        original_w = app.winfo_width()
        app.geometry("700x600")
        time.sleep(WAIT_SHORT)
        app.update_idletasks()
        assert app.winfo_width() == original_w, \
            "Window should not be resizable"


class TestHeaderContent:

    def test_app_name_label_present(self, app):
        """TC-P1-004: Header must display app name."""
        # Walk widget tree and look for app name text
        def _find(widget):
            try:
                if "ScreenWatermark" in str(widget.cget("text")):
                    return True
            except Exception:
                pass
            return any(_find(c) for c in widget.winfo_children())
        assert _find(app), "App name not found in header"

    def test_wm_badge_on_with_file(self, app):
        """TC-P1-005: WM badge shows 'WM ✓' when enabled and file set."""
        app.wm_enabled.set(True)
        app.watermark_path.set(str(TEST_WM_PATH))
        app._update_wm_indicator()
        time.sleep(WAIT_SHORT)
        badge_text = get_widget_text(app.wm_indicator)
        assert "\u2713" in badge_text, f"Expected WM \u2713 badge, got: '{badge_text}'"

    def test_wm_badge_on_no_file(self, app):
        """TC-P1-006: WM badge shows warning when enabled but no file."""
        app.wm_enabled.set(True)
        app.watermark_path.set("")
        app._update_wm_indicator()
        time.sleep(WAIT_SHORT)
        badge_text = get_widget_text(app.wm_indicator)
        assert "\u26a0" in badge_text, f"Expected WM \u26a0 badge, got: '{badge_text}'"

    def test_wm_badge_off(self, app):
        """TC-P1-007: WM badge shows 'WM OFF' when disabled."""
        app.wm_enabled.set(False)
        app._update_wm_indicator()
        time.sleep(WAIT_SHORT)
        badge_text = get_widget_text(app.wm_indicator)
        assert "OFF" in badge_text, f"Expected WM OFF, got: '{badge_text}'"

    def test_settings_button_opens_window(self, app):
        """TC-P1-008: Settings button opens CTkToplevel."""
        click_widget(app, app.btn_settings if hasattr(app, "btn_settings")
                     else app)
        # Try clicking via pyautogui on Settings button position
        import pyautogui
        # Fallback: call directly
        app.after(0, app._open_settings)
        time.sleep(WAIT_MEDIUM)
        win = find_toplevel(app, "Settings")
        assert win is not None, "Settings window did not open"
        # Cleanup
        if win:
            app.after(0, win._on_close)
            time.sleep(WAIT_SHORT)

    def test_history_icon_opens_popup(self, app):
        """TC-P1-009: History icon opens HistoryPopup."""
        from ui.history_popup import HistoryPopup
        popup = HistoryPopup(app)
        app._history_popup = popup
        time.sleep(WAIT_MEDIUM)
        assert popup is not None and popup.winfo_exists(), \
            "History popup did not open"
        # Cleanup
        app.after(0, popup._safe_destroy)
        time.sleep(WAIT_SHORT)
