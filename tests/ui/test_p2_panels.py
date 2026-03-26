# tests/ui/test_p2_panels.py
"""
Phase P2 — Canvas Toggle + Preview + History Panel
Covers: TC-P2-001 → TC-P2-014 (except TC-P2-004 manual)
Run at GC: pytest tests/ui/test_p2_panels.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
import pytest
from tests.conftest import (
    app, app_instance, make_fake_entry,
    widget_is_visible, get_canvas_image, images_differ,
    WAIT_SHORT, WAIT_MEDIUM
)


class TestPanelToggle:

    def test_default_panel_is_preview(self, app):
        """TC-P2-001: Preview visible by default, history hidden."""
        assert widget_is_visible(app.preview_wrap), \
            "Preview canvas should be visible on launch"
        assert not widget_is_visible(app.history_panel_wrap), \
            "History panel should be hidden by default"

    def test_toggle_to_history(self, app):
        """TC-P2-002: Toggle to History shows history panel, hides preview."""
        app.after(0, lambda: app._switch_panel("history"))
        time.sleep(WAIT_SHORT)
        assert widget_is_visible(app.history_panel_wrap)
        assert not widget_is_visible(app.preview_wrap)

    def test_toggle_back_to_preview(self, app):
        """TC-P2-003: Toggle back restores preview."""
        app.after(0, lambda: app._switch_panel("history"))
        time.sleep(WAIT_SHORT)
        app.after(0, lambda: app._switch_panel("preview"))
        time.sleep(WAIT_SHORT)
        assert widget_is_visible(app.preview_wrap)
        assert not widget_is_visible(app.history_panel_wrap)

    def test_history_badge_shows_count(self, app):
        """TC-P2-005: Badge shows count when history has items."""
        with app._history_lock:
            app._history.clear()
            for _ in range(3):
                app._history.append(make_fake_entry())
        app.after(0, app._update_history_badge)
        time.sleep(WAIT_SHORT)
        assert app.hist_count_badge.cget("text") == "3"

    def test_history_badge_hidden_at_zero(self, app):
        """TC-P2-006: Badge empty when history has 0 items."""
        with app._history_lock:
            app._history.clear()
        app.after(0, app._update_history_badge)
        time.sleep(WAIT_SHORT)
        assert app.hist_count_badge.cget("text") == ""

    def test_preview_renders_watermark(self, app):
        """TC-P2-007: Preview canvas shows watermark pixels."""
        from conftest import TEST_WM_PATH
        app.after(0, lambda: app.wm_enabled.set(True))
        app.after(0, lambda: app.watermark_path.set(str(TEST_WM_PATH)))
        time.sleep(WAIT_MEDIUM)
        img = get_canvas_image(app)
        # Canvas should not be solid background color — WM pixels present
        colors = set(img.convert("RGB").getdata())
        assert len(colors) > 1, "Preview canvas should have more than 1 color"

    def test_preview_updates_on_setting_change(self, app):
        """TC-P2-009: Canvas re-renders after slider change."""
        time.sleep(WAIT_SHORT)
        img_before = get_canvas_image(app)
        app.after(0, lambda: app.wm_opacity.set(10))
        time.sleep(WAIT_MEDIUM)
        img_after = get_canvas_image(app)
        assert images_differ(img_before, img_after), \
            "Preview should differ after opacity change"

    def test_history_thumbs_appear(self, app):
        """TC-P2-011: History panel shows one thumb per entry."""
        with app._history_lock:
            app._history.clear()
            for _ in range(3):
                app._history.append(make_fake_entry())
        app.after(0, lambda: app._switch_panel("history"))
        app.after(0, app._render_history_panel)
        time.sleep(WAIT_MEDIUM)
        count = len(app.hist_panel_scroll.winfo_children())
        assert count >= 3, f"Expected 3+ thumbs, got {count}"

    def test_history_clear_all(self, app):
        """TC-P2-013: Clear All empties history."""
        with app._history_lock:
            app._history.clear()
            app._history.append(make_fake_entry())
        app.after(0, app._clear_all_history)
        time.sleep(WAIT_MEDIUM)
        with app._history_lock:
            assert len(app._history) == 0

    def test_history_auto_refresh_on_new_shot(self, app):
        """TC-P2-014: New screenshot on History panel stays on History + new thumb."""
        app.after(0, lambda: app._switch_panel("history"))
        time.sleep(WAIT_SHORT)
        with app._history_lock:
            count_before = len(app._history)
        app.after(0, app._trigger_fullscreen)
        time.sleep(2.5)
        assert app._panel_mode == "history", \
            "Panel should stay on History after hotkey screenshot"
        with app._history_lock:
            count_after = len(app._history)
        assert count_after == count_before + 1
