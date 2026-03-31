# tests/test_p2_panels.py
"""
Phase 2 — Canvas Toggle + Preview + History Panel
Covers: TC-P2-001 to TC-P2-014 (except TC-P2-004 manual)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
import pytest
from tests.conftest import (
    app, app_instance,
    wait_for, widget_is_visible, get_canvas_image,
    get_clipboard_image, images_differ, click_widget,
    WAIT_SHORT, WAIT_MEDIUM, WAIT_LONG, TEST_WM_PATH
)


class TestPanelToggle:

    def test_default_panel_is_preview(self, app):
        """TC-P2-001: Preview panel visible by default, history hidden."""
        assert widget_is_visible(app.preview_wrap), "Preview canvas should be visible"
        assert not widget_is_visible(app.history_panel_wrap), \
            "History panel should be hidden by default"

    def test_toggle_to_history(self, app):
        """TC-P2-002: Toggle to History hides preview, shows history panel."""
        app.after(0, lambda: app._switch_panel("history"))
        time.sleep(WAIT_SHORT)
        assert widget_is_visible(app.history_panel_wrap), \
            "History panel should be visible after toggle"
        assert not widget_is_visible(app.preview_wrap), \
            "Preview should be hidden after toggle to history"

    def test_toggle_back_to_preview(self, app):
        """TC-P2-003: Toggle back to Preview restores canvas."""
        app.after(0, lambda: app._switch_panel("history"))
        time.sleep(WAIT_SHORT)
        app.after(0, lambda: app._switch_panel("preview"))
        time.sleep(WAIT_SHORT)
        assert widget_is_visible(app.preview_wrap), \
            "Preview should be visible after toggle back"
        assert not widget_is_visible(app.history_panel_wrap), \
            "History should be hidden"

    def test_history_badge_count(self, app):
        """TC-P2-005: Badge shows correct count when history has items."""
        import uuid
        from datetime import datetime
        from PIL import Image
        import io
        # Inject 3 fake entries
        fake_entry = lambda i: {
            "entry_id": str(uuid.uuid4()),
            "thumb_bytes": _make_thumb_bytes(),
            "full_bytes":  _make_full_bytes(),
            "timestamp":   datetime.now(),
            "width": 800, "height": 600,
        }
        with app._history_lock:
            app._history.clear()
            for i in range(3):
                app._history.append(fake_entry(i))
        app.after(0, app._update_history_badge)
        time.sleep(WAIT_SHORT)
        badge_text = app.hist_count_badge.cget("text")
        assert badge_text == "3", f"Badge should show '3', got '{badge_text}'"

    def test_history_badge_hidden_at_zero(self, app):
        """TC-P2-006: Badge hidden when history is empty."""
        with app._history_lock:
            app._history.clear()
        app.after(0, app._update_history_badge)
        time.sleep(WAIT_SHORT)
        badge_text = app.hist_count_badge.cget("text")
        assert badge_text == "", f"Badge should be empty at 0 items, got '{badge_text}'"

    def test_history_thumbs_appear(self, app):
        """TC-P2-011: History panel shows thumbnails for each entry."""
        import uuid
        from datetime import datetime
        with app._history_lock:
            app._history.clear()
            for _ in range(3):
                app._history.append({
                    "entry_id": str(uuid.uuid4()),
                    "thumb_bytes": _make_thumb_bytes(),
                    "full_bytes":  _make_full_bytes(),
                    "timestamp": datetime.now(),
                    "width": 800, "height": 600,
                })
        app.after(0, lambda: app._switch_panel("history"))
        app.after(0, app._render_history_panel)
        time.sleep(WAIT_MEDIUM)
        children = app.hist_panel_scroll.winfo_children()
        assert len(children) >= 3, \
            f"Expected 3+ thumb widgets, got {len(children)}"

    def test_history_clear_all(self, app):
        """TC-P2-013: Clear All empties history panel."""
        import uuid
        from datetime import datetime
        with app._history_lock:
            app._history.clear()
            app._history.append({
                "entry_id": str(uuid.uuid4()),
                "thumb_bytes": _make_thumb_bytes(),
                "full_bytes":  _make_full_bytes(),
                "timestamp": datetime.now(),
                "width": 800, "height": 600,
            })
        app.after(0, app._clear_all_history)
        time.sleep(WAIT_MEDIUM)
        with app._history_lock:
            count = len(app._history)
        assert count == 0, f"History should be empty after clear, got {count}"


# ── helpers ───────────────────────────────────────────────────────────────────
def _make_thumb_bytes() -> bytes:
    from PIL import Image
    import io
    buf = io.BytesIO()
    Image.new("RGB", (96, 54), (60, 60, 90)).save(buf, "JPEG", quality=80)
    return buf.getvalue()

def _make_full_bytes() -> bytes:
    from PIL import Image
    import io
    buf = io.BytesIO()
    Image.new("RGB", (800, 600), (60, 60, 90)).save(buf, "PNG")
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# tests/test_p3_wm_accordion.py
# Phase 3 — WM Accordion
# ─────────────────────────────────────────────────────────────────────────────

import time, json
from pathlib import Path


class TestWMAccordion:

    def test_wm_accordion_open_on_launch(self, app):
        """TC-P3-001: WM accordion body is visible on launch."""
        assert app._wm_acc_open is True, "WM accordion should be open on launch"
        assert widget_is_visible(app._wm_body), \
            "WM accordion body should be visible"

    def test_wm_accordion_toggle_close(self, app):
        """TC-P3-002/003: Accordion opens and closes correctly."""
        # Start open → close
        if not app._wm_acc_open:
            app.after(0, app._toggle_wm_accordion)
            time.sleep(WAIT_SHORT)
        app.after(0, app._toggle_wm_accordion)
        time.sleep(WAIT_SHORT)
        assert not app._wm_acc_open, "Accordion should be closed"
        assert not widget_is_visible(app._wm_body), \
            "Body should be hidden when closed"
        # Reopen
        app.after(0, app._toggle_wm_accordion)
        time.sleep(WAIT_SHORT)
        assert app._wm_acc_open
        assert widget_is_visible(app._wm_body)

    def test_wm_enable_off_sets_var(self, app):
        """TC-P3-004: Enable OFF sets wm_enabled=False and updates badge."""
        app.after(0, lambda: app.wm_enabled.set(False))
        time.sleep(WAIT_SHORT)
        assert app.wm_enabled.get() is False
        badge = app.wm_indicator.cget("text")
        assert "OFF" in badge, f"Badge should show OFF, got '{badge}'"

    def test_wm_mode_normal_shows_pos_and_scale(self, app):
        """TC-P3-005: Normal mode shows position and scale controls."""
        app.after(0, lambda: app.wm_mode.set("normal"))
        app.after(0, app._on_wm_mode_change_inline)
        time.sleep(WAIT_SHORT)
        assert widget_is_visible(app._wm_pos_menu), \
            "Position menu should be visible in Normal mode"
        assert widget_is_visible(app._wm_row2), \
            "Scale row should be visible in Normal mode"

    def test_wm_mode_full_hides_pos_and_scale(self, app):
        """TC-P3-006: Full mode hides position and scale."""
        app.after(0, lambda: app.wm_mode.set("full"))
        app.after(0, app._on_wm_mode_change_inline)
        time.sleep(WAIT_SHORT)
        assert not widget_is_visible(app._wm_pos_menu), \
            "Position menu should be hidden in Full mode"
        assert not widget_is_visible(app._wm_row2), \
            "Scale row should be hidden in Full mode"

    def test_wm_mode_pattern_hides_pos_shows_scale(self, app):
        """TC-P3-007: Pattern mode hides position, shows scale."""
        app.after(0, lambda: app.wm_mode.set("pattern"))
        app.after(0, app._on_wm_mode_change_inline)
        time.sleep(WAIT_SHORT)
        assert not widget_is_visible(app._wm_pos_menu), \
            "Position menu should be hidden in Pattern mode"
        assert widget_is_visible(app._wm_row2), \
            "Scale row should be visible in Pattern mode"

    def test_wm_opacity_var_updates(self, app):
        """TC-P3-009: Opacity var updates on slider change."""
        app.after(0, lambda: app.wm_opacity.set(45))
        time.sleep(WAIT_SHORT)
        assert app.wm_opacity.get() == 45

    def test_wm_scale_var_updates(self, app):
        """TC-P3-010: Scale var updates on slider change."""
        app.after(0, lambda: app.wm_scale.set(35))
        time.sleep(WAIT_SHORT)
        assert app.wm_scale.get() == 35

    def test_wm_file_set_updates_label(self, app):
        """TC-P3-012: Setting watermark path updates filename label."""
        app.after(0, lambda: app.watermark_path.set(str(TEST_WM_PATH)))
        time.sleep(WAIT_SHORT)
        label_text = app._wm_fname_lbl.cget("text")
        assert "test_watermark" in label_text, \
            f"Label should show filename, got '{label_text}'"

    def test_wm_clear_file_resets_path(self, app):
        """TC-P3-013: Clear ✕ resets watermark path and badge."""
        app.after(0, lambda: app.watermark_path.set(str(TEST_WM_PATH)))
        time.sleep(WAIT_SHORT)
        app.after(0, app._clear_watermark_path_inline)
        time.sleep(WAIT_SHORT)
        assert app.watermark_path.get() == "", \
            "watermark_path should be empty after clear"
        badge = app.wm_indicator.cget("text")
        assert "⚠" in badge or "OFF" in badge, \
            f"Badge should reflect no-file state, got '{badge}'"

    def test_wm_summary_updates_on_mode_change(self, app):
        """TC-P3-014: Summary label updates when mode changes."""
        app.after(0, lambda: app.wm_mode.set("full"))
        app.after(0, app._update_wm_summary)
        time.sleep(WAIT_SHORT)
        summary = app._wm_summary_lbl.cget("text")
        assert "Full" in summary, f"Summary should contain 'Full', got '{summary}'"

    def test_wm_settings_saved_to_json(self, app):
        """TC-P3-015: Changing opacity triggers autosave within 1s."""
        from conftest import read_settings_json
        app.after(0, lambda: app.wm_opacity.set(42))
        time.sleep(1.0)   # wait for 800ms debounce + write
        data = read_settings_json()
        assert data.get("wm_opacity") == 42, \
            f"Settings JSON should have wm_opacity=42, got {data.get('wm_opacity')}"

    def test_wm_normal_screenshot_pixel(self, app):
        """TC-P3-016: Normal mode WM appears in bottom-left of screenshot."""
        app.after(0, lambda: app.wm_mode.set("normal"))
        app.after(0, lambda: app.wm_position.set("bottom-left"))
        app.after(0, lambda: app.wm_enabled.set(True))
        app.after(0, lambda: app.watermark_path.set(str(TEST_WM_PATH)))
        time.sleep(WAIT_SHORT)
        # Trigger fullscreen screenshot
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        img = get_clipboard_image()
        assert img is not None, "No image in clipboard after screenshot"
        # Bottom-left region should have red pixels (test WM is red)
        w, h = img.size
        bl_region = (0, h*3//4, w//4, h)
        from conftest import pixel_region_has_color
        assert pixel_region_has_color(img, bl_region, (255, 0, 0), tolerance=60), \
            "Expected red WM pixel in bottom-left region"

    def test_wm_disabled_screenshot_no_wm(self, app):
        """TC-P8-019: WM disabled → no red pixels in WM region."""
        app.after(0, lambda: app.wm_enabled.set(False))
        time.sleep(WAIT_SHORT)
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        img = get_clipboard_image()
        assert img is not None
        w, h = img.size
        bl_region = (0, h*3//4, w//4, h)
        from conftest import pixel_region_has_color
        # Should NOT have red WM pixels
        assert not pixel_region_has_color(img, bl_region, (255, 0, 0), tolerance=40), \
            "WM should not appear when disabled"


class TestTSAccordion:

    def test_ts_accordion_closed_on_launch(self, app):
        """TC-P4-001: TS accordion body hidden on launch."""
        assert app._ts_acc_open is False, "TS accordion should be closed on launch"
        assert not widget_is_visible(app._ts_body), \
            "TS body should be hidden on launch"

    def test_ts_accordion_toggle(self, app):
        """TC-P4-002: TS accordion opens and closes."""
        app.after(0, app._toggle_ts_accordion)
        time.sleep(WAIT_SHORT)
        assert app._ts_acc_open
        assert widget_is_visible(app._ts_body)
        app.after(0, app._toggle_ts_accordion)
        time.sleep(WAIT_SHORT)
        assert not app._ts_acc_open

    def test_both_accordions_open_simultaneously(self, app):
        """Both WM and TS can be open at the same time."""
        # Ensure WM is open
        if not app._wm_acc_open:
            app.after(0, app._toggle_wm_accordion)
            time.sleep(WAIT_SHORT)
        # Open TS
        if not app._ts_acc_open:
            app.after(0, app._toggle_ts_accordion)
            time.sleep(WAIT_SHORT)
        assert app._wm_acc_open, "WM should still be open"
        assert app._ts_acc_open, "TS should be open"
        assert widget_is_visible(app._wm_body), "WM body visible"
        assert widget_is_visible(app._ts_body), "TS body visible"

    def test_ts_enable_off(self, app):
        """TC-P4-003: TS disabled removes timestamp from preview."""
        app.after(0, lambda: app.ts_enabled.set(True))
        time.sleep(WAIT_SHORT)
        img_before = get_canvas_image(app)
        app.after(0, lambda: app.ts_enabled.set(False))
        time.sleep(WAIT_MEDIUM)
        img_after = get_canvas_image(app)
        assert images_differ(img_before, img_after), \
            "Preview should change when TS is disabled"

    def test_ts_outside_canvas_var(self, app):
        """TC-P4-004: Outside toggle sets ts_outside_canvas var."""
        app.after(0, lambda: app.ts_outside_canvas.set(True))
        time.sleep(WAIT_SHORT)
        assert app.ts_outside_canvas.get() is True

    def test_ts_font_size_var(self, app):
        """TC-P4-006: Font size slider updates ts_font_size var."""
        app.after(0, lambda: app.ts_font_size.set(40))
        time.sleep(WAIT_SHORT)
        assert app.ts_font_size.get() == 40

    def test_ts_bold_var(self, app):
        """TC-P4-009: Bold toggle updates ts_bold var."""
        app.after(0, lambda: app.ts_bold.set(True))
        time.sleep(WAIT_SHORT)
        assert app.ts_bold.get() is True

    def test_ts_shadow_var(self, app):
        """TC-P4-010: Shadow toggle updates ts_shadow var."""
        app.after(0, lambda: app.ts_shadow.set(False))
        time.sleep(WAIT_SHORT)
        assert app.ts_shadow.get() is False

    def test_ts_summary_updates(self, app):
        """TC-P4-011: TS summary label reflects current state."""
        app.after(0, lambda: app.ts_enable.set("Outside"))
        app.after(0, app._update_ts_summary)
        time.sleep(WAIT_SHORT)
        summary = app.ts_summary.cget("text")
        assert "Outside" in summary, f"Summary should contain 'Outside', got '{summary}'"

    def test_ts_settings_saved(self, app):
        """TC-P4-012: TS font size change saves to JSON."""
        from conftest import read_settings_json
        app.after(0, lambda: app.ts_font_size.set(33))
        time.sleep(1.0)
        data = read_settings_json()
        assert data.get("ts_font_size") == 33, \
            f"Expected ts_font_size=33 in JSON, got {data.get('ts_font_size')}"

    def test_ts_outside_canvas_screenshot(self, app):
        """TC-P4-013: Outside=True makes image taller than original."""
        app.after(0, lambda: app.ts_outside_canvas.set(True))
        app.after(0, lambda: app.ts_enabled.set(True))
        time.sleep(WAIT_SHORT)
        # Get base screenshot height first
        import mss
        with mss.mss() as sct:
            mon = sct.monitors[0]
            base_h = mon["height"]
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        img = get_clipboard_image()
        assert img is not None
        assert img.height > base_h, \
            f"Image with outside TS should be taller than {base_h}px, got {img.height}px"

    def test_ts_overlay_screenshot(self, app):
        """TC-P4-014: Outside=False — image height equals screen height."""
        app.after(0, lambda: app.ts_outside_canvas.set(False))
        app.after(0, lambda: app.ts_enabled.set(True))
        time.sleep(WAIT_SHORT)
        import mss
        with mss.mss() as sct:
            mon = sct.monitors[0]
            base_h = mon["height"]
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        img = get_clipboard_image()
        assert img is not None
        assert img.height == base_h, \
            f"Overlay TS should keep image height={base_h}, got {img.height}"

    def test_ts_disabled_screenshot(self, app):
        """TC-P8-020: TS disabled — no timestamp strip or overlay."""
        app.after(0, lambda: app.ts_outside_canvas.set(False))
        app.after(0, lambda: app.ts_enabled.set(False))
        time.sleep(WAIT_SHORT)
        import mss
        with mss.mss() as sct:
            base_h = sct.monitors[0]["height"]
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        img = get_clipboard_image()
        assert img is not None
        assert img.height == base_h, \
            "TS disabled: image height should equal screen height exactly"


class TestShotButtons:

    def test_both_buttons_visible(self, app):
        """TC-P5-001: Both fullscreen and region buttons are visible."""
        assert widget_is_visible(app.btn_fullscreen), \
            "Fullscreen button should be visible"
        assert widget_is_visible(app.btn_region), \
            "Region button should be visible"

    def test_copy_button_disabled_at_start(self, app):
        """TC-P5-009: Copy button disabled before any screenshot."""
        # Fresh app — no screenshots taken yet
        if app.last_image is None:
            state = app.btn_copy.cget("state")
            assert state == "disabled", \
                f"Copy button should be disabled initially, got '{state}'"

    def test_fullscreen_screenshot_enables_copy(self, app):
        """TC-P5-010 / TC-P5-002: Fullscreen shot populates clipboard + enables copy."""
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        assert app.last_image is not None, "last_image should be set after screenshot"
        state = app.btn_copy.cget("state")
        assert state == "normal", \
            f"Copy button should be enabled after screenshot, got '{state}'"

    def test_copy_button_copies_to_clipboard(self, app):
        """TC-P5-002 extended: Clipboard contains valid image after shot."""
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        img = get_clipboard_image()
        assert img is not None, "Clipboard should contain an image"
        assert img.width > 0 and img.height > 0

    def test_buttons_disabled_during_capture(self, app):
        """TC-P5-004: Shot buttons disabled during screenshot flow."""
        states_during = []
        original_do_shot = app._do_screenshot

        def _patched(region):
            states_during.append(app.btn_fullscreen.cget("state"))
            original_do_shot(region)

        app._do_screenshot = _patched
        app.after(0, app._trigger_fullscreen)
        time.sleep(0.1)  # catch it in-flight
        # Restore
        app._do_screenshot = original_do_shot
        time.sleep(WAIT_LONG)
        if states_during:
            assert states_during[0] == "disabled", \
                "Fullscreen button should be disabled during capture"

    def test_status_bar_updates_after_shot(self, app):
        """TC-P8-017: Status bar shows success message after screenshot."""
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        status = app.status_var.get()
        assert "✓" in status or "copied" in status.lower(), \
            f"Status should show success, got '{status}'"

    def test_status_bar_restores(self, app):
        """TC-P8-018: Status bar restores to ready state after 3.5s."""
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 4.0)  # wait for restore
        status = app.status_var.get()
        assert "Ready" in status or "Siap" in status or \
               "Print Screen" in status or "F9" in status, \
            f"Status should restore to hotkey display, got '{status}'"
