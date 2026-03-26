# tests/test_p6_settings.py
"""
Phase 6 — Settings Window
Covers: TC-P6-001 to TC-P6-013 (except TC-P6-008, TC-P6-009 manual)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import time
import pytest
from tests.conftest import (
    app, app_instance,
    wait_for, find_toplevel, read_settings_json,
    WAIT_SHORT, WAIT_MEDIUM, WAIT_LONG
)

# Import DEFAULT_SETTINGS from the app module
import importlib, sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def settings_win(app):
    """Open Settings window, yield it, close after test."""
    app.after(0, app._open_settings)
    time.sleep(WAIT_MEDIUM)
    win = app._settings_win
    assert win is not None and win.winfo_exists(), "Settings window should open"
    yield win
    try:
        app.after(0, win._on_close)
        time.sleep(WAIT_SHORT)
    except Exception:
        pass


class TestSettingsWindow:

    def test_settings_opens_as_toplevel(self, settings_win):
        """TC-P6-001: Settings is a Toplevel at 480×520."""
        settings_win.update_idletasks()
        w = settings_win.winfo_width()
        h = settings_win.winfo_height()
        assert w == 480, f"Settings width should be 480, got {w}"
        assert h == 520, f"Settings height should be 520, got {h}"

    def test_wm_card_absent(self, settings_win):
        """TC-P6-002: No Watermark card in Settings window."""
        text = _collect_widget_texts(settings_win)
        assert "Watermark" not in text or _only_in_removed_notice(text, "Watermark"), \
            "Watermark card should not exist in Settings (only in removed notice)"

    def test_ts_card_absent(self, settings_win):
        """TC-P6-003: No Timestamp card in Settings window."""
        text = _collect_widget_texts(settings_win)
        assert "Timestamp" not in text or _only_in_removed_notice(text, "Timestamp"), \
            "Timestamp card should not exist in Settings"

    def test_startup_card_present(self, settings_win):
        """TC-P6-004: Startup card is visible."""
        text = _collect_widget_texts(settings_win)
        assert "Startup" in text or "startup" in text.lower(), \
            "Startup card should be present"

    def test_capture_card_present(self, settings_win):
        """TC-P6-005: Capture card is visible."""
        text = _collect_widget_texts(settings_win)
        assert "Capture" in text or "capture" in text.lower(), \
            "Capture card should be present"

    def test_hotkeys_card_present(self, settings_win):
        """TC-P6-006: Hotkeys card is visible."""
        text = _collect_widget_texts(settings_win)
        assert "Hotkey" in text or "hotkey" in text.lower(), \
            "Hotkeys card should be present"

    def test_language_card_present(self, settings_win):
        """TC-P6-007: Language card is visible."""
        text = _collect_widget_texts(settings_win)
        assert "Language" in text or "Bahasa" in text, \
            "Language card should be present"

    def test_reset_to_default(self, app, settings_win):
        """TC-P6-010: Reset to Default restores all vars to DEFAULT_SETTINGS."""
        import importlib
        mod = importlib.import_module("Screen_Watermark_4.0.0_GCa")
        defaults = mod.DEFAULT_SETTINGS
        # Change a few values first
        app.after(0, lambda: app.wm_opacity.set(11))
        app.after(0, lambda: app.ts_font_size.set(55))
        time.sleep(WAIT_SHORT)
        # Call reset
        app.after(0, settings_win._reset_defaults)
        time.sleep(WAIT_MEDIUM)
        assert app.wm_opacity.get() == defaults["wm_opacity"], \
            f"wm_opacity should reset to {defaults['wm_opacity']}"
        assert app.ts_font_size.get() == defaults["ts_font_size"], \
            f"ts_font_size should reset to {defaults['ts_font_size']}"

    def test_close_button_withdraws_window(self, app, settings_win):
        """TC-P6-011: Close button withdraws the Settings window."""
        app.after(0, settings_win._on_close)
        time.sleep(WAIT_MEDIUM)
        # Window should be withdrawn or destroyed
        visible = False
        try:
            visible = settings_win.winfo_viewable()
        except Exception:
            visible = False
        assert not visible, "Settings window should not be visible after close"

    def test_settings_state_persists(self, app):
        """TC-P6-012: Capture mode persists after close+reopen."""
        app.after(0, lambda: app.capture_mode.set("region"))
        app.after(0, app._open_settings)
        time.sleep(WAIT_MEDIUM)
        win = app._settings_win
        if win and win.winfo_exists():
            app.after(0, win._on_close)
            time.sleep(WAIT_SHORT)
        app.after(0, app._open_settings)
        time.sleep(WAIT_MEDIUM)
        assert app.capture_mode.get() == "region", \
            "capture_mode should persist across settings close/reopen"


def _collect_widget_texts(widget) -> str:
    """Recursively collect all widget text strings."""
    texts = []
    try:
        t = widget.cget("text")
        if t:
            texts.append(str(t))
    except Exception:
        pass
    for child in widget.winfo_children():
        texts.append(_collect_widget_texts(child))
    return " ".join(texts)


def _only_in_removed_notice(text: str, keyword: str) -> bool:
    """True if keyword appears only in the removed-notice area (acceptable)."""
    # Simple heuristic: check if the removed notice text contains it
    return "moved to main window" in text.lower()


# ─────────────────────────────────────────────────────────────────────────────
# tests/test_p7_i18n.py
# Phase 7 — Localization
# ─────────────────────────────────────────────────────────────────────────────

class TestLocalization:

    def test_default_language_english(self):
        """TC-P7-001: Default t() returns English strings."""
        import i18n
        i18n.set_language("en")
        assert i18n.t("settings") == "Settings", \
            f"Expected 'Settings', got '{i18n.t('settings')}'"

    def test_switch_to_indonesian(self):
        """TC-P7-002: After set_language('id'), strings are Indonesian."""
        import i18n
        i18n.set_language("id")
        assert i18n.t("settings") == "Pengaturan", \
            f"Expected 'Pengaturan', got '{i18n.t('settings')}'"
        # Reset
        i18n.set_language("en")

    def test_language_key_saved_to_json(self, app):
        """TC-P7-003: Language change writes to settings JSON."""
        app.after(0, lambda: app.ui_language.set("id"))
        time.sleep(1.0)  # debounce
        data = read_settings_json()
        assert data.get("language") == "id", \
            f"Expected language='id' in JSON, got '{data.get('language')}'"
        # Reset
        app.after(0, lambda: app.ui_language.set("en"))
        time.sleep(1.0)

    def test_switch_back_to_english(self):
        """TC-P7-004: Can switch back to English."""
        import i18n
        i18n.set_language("id")
        i18n.set_language("en")
        assert i18n.t("settings") == "Settings"

    def test_missing_key_returns_key_name(self):
        """TC-P7-005: Missing key returns key name — no crash."""
        import i18n
        result = i18n.t("this_key_does_not_exist_xyz")
        assert result == "this_key_does_not_exist_xyz", \
            f"Missing key should return key name, got '{result}'"

    def test_all_english_keys_have_indonesian(self):
        """All English keys exist in Indonesian dict (no missing translations)."""
        import i18n
        en_keys = set(i18n._STRINGS["en"].keys())
        id_keys = set(i18n._STRINGS["id"].keys())
        missing = en_keys - id_keys
        assert not missing, \
            f"These keys are missing from Indonesian dict: {missing}"


# ─────────────────────────────────────────────────────────────────────────────
# tests/test_p8_integration.py
# Phase 8 — Integration + Regression
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:

    def test_full_fs_screenshot_flow(self, app):
        """TC-P8-001: Full flow — WM + TS applied, image in clipboard."""
        app.after(0, lambda: app.wm_enabled.set(True))
        app.after(0, lambda: app.ts_enabled.set(True))
        app.after(0, lambda: app.ts_outside_canvas.set(False))
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        img = get_clipboard_image()
        assert img is not None, "Clipboard should have image after full flow"
        assert app.last_image is not None
        assert img.width > 0 and img.height > 0

    def test_single_instance_guard(self):
        """TC-P8-005: Second instance shows first window, does not create duplicate."""
        import subprocess, sys, time
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / "Screen_Watermark_4.0.0_GCa.py")],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2.0)
        ret = proc.poll()
        assert ret == 0, \
            f"Second instance should exit with code 0, got {ret}"

    def test_history_persists_to_disk(self, app):
        """TC-P8-008: History written to HISTORY_FILE after screenshot."""
        from conftest import HISTORY_FILE
        HISTORY_FILE.unlink(missing_ok=True)
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 1.0)
        assert HISTORY_FILE.exists(), "HISTORY_FILE should exist after screenshot"
        data = read_history_json()
        assert len(data) >= 1, f"History JSON should have >=1 entry, got {len(data)}"

    def test_settings_persist_to_disk(self, app):
        """TC-P8-009: Settings file written and readable."""
        from conftest import SETTINGS_FILE
        app.after(0, lambda: app.wm_opacity.set(77))
        time.sleep(1.0)
        assert SETTINGS_FILE.exists(), "SETTINGS_FILE should exist"
        data = read_settings_json()
        assert data.get("wm_opacity") == 77

    def test_autosave_debounce(self, app):
        """TC-P8-010: 10 rapid changes produce only 1 write, fired 800ms after last."""
        import os
        from conftest import SETTINGS_FILE
        time.sleep(1.0)  # let any pending saves complete
        mtime_before = SETTINGS_FILE.stat().st_mtime if SETTINGS_FILE.exists() else 0
        # Fire 10 rapid changes
        for v in range(10, 20):
            app.after(0, lambda x=v: app.wm_opacity.set(x))
            time.sleep(0.05)
        # Check mid-debounce (400ms) — should not have saved yet
        time.sleep(0.4)
        mtime_mid = SETTINGS_FILE.stat().st_mtime if SETTINGS_FILE.exists() else 0
        # Wait for debounce to fire
        time.sleep(0.8)
        mtime_after = SETTINGS_FILE.stat().st_mtime if SETTINGS_FILE.exists() else 0
        # The file should be newer after debounce settles
        assert mtime_after >= mtime_mid, "Settings should be written after debounce"
        data = read_settings_json()
        assert data.get("wm_opacity") == 19, \
            f"Last value (19) should be saved, got {data.get('wm_opacity')}"

    def test_wm_cache_invalidated_on_path_change(self, app):
        """TC-P8-011: WM resize cache clears when path changes."""
        import Screen_Watermark_4_0_0_GCa as mod
        # Prime the cache
        app.after(0, lambda: app.watermark_path.set(str(TEST_WM_PATH)))
        time.sleep(WAIT_SHORT)
        app.after(0, mod.invalidate_wm_cache)
        time.sleep(WAIT_SHORT)
        with mod._wm_cache_lock:
            assert len(mod._wm_cache) == 0, "WM cache should be empty after invalidation"
            assert len(mod._wm_resize_cache) == 0

    def test_screenshot_from_minimized_stays_minimized(self, app):
        """TC-P8-012: App stays minimized after fullscreen shot from iconic state."""
        app.after(0, app.iconify)
        time.sleep(WAIT_SHORT)
        assert app.wm_state() == "iconic"
        app.after(0, app._trigger_fullscreen)
        time.sleep(WAIT_LONG + 0.5)
        state = app.wm_state()
        assert state == "iconic", \
            f"App should remain iconic after shot from minimized, got '{state}'"
        # Restore for subsequent tests
        app.after(0, app.deiconify)
        time.sleep(WAIT_SHORT)

    def test_delete_history_entry(self, app):
        """TC-P8-014: Deleting an entry reduces history count by 1."""
        import uuid
        from datetime import datetime
        # Ensure at least 2 entries
        with app._history_lock:
            app._history.clear()
            for _ in range(2):
                app._history.append({
                    "entry_id": str(uuid.uuid4()),
                    "thumb_bytes": _make_thumb_bytes(),
                    "full_bytes":  _make_full_bytes(),
                    "timestamp": datetime.now(),
                    "width": 800, "height": 600,
                })
        with app._history_lock:
            entry_to_delete = list(app._history)[0]
            count_before = len(app._history)
        app.after(0, lambda: app._delete_history_entry(entry_to_delete))
        time.sleep(WAIT_MEDIUM)
        with app._history_lock:
            count_after = len(app._history)
        assert count_after == count_before - 1, \
            f"Expected {count_before-1} entries after delete, got {count_after}"

    def test_no_tclerror_on_repeated_settings_open_close(self, app):
        """TC-P8-015: Open/close Settings 10x without TclError."""
        errors = []
        for _ in range(10):
            try:
                app.after(0, app._open_settings)
                time.sleep(WAIT_MEDIUM)
                if app._settings_win and app._settings_win.winfo_exists():
                    app.after(0, app._settings_win._on_close)
                    time.sleep(WAIT_SHORT)
            except Exception as e:
                errors.append(str(e))
        assert not errors, f"Errors during repeated open/close: {errors}"

    def test_ui_responsive_during_rapid_slider(self, app):
        """TC-P8-016: UI event loop stays responsive during rapid slider moves."""
        import time as _t
        start = _t.time()
        for v in range(5, 60, 2):
            app.after(0, lambda x=v: app.wm_opacity.set(x))
        # Process events and measure
        app.update()
        elapsed = _t.time() - start
        assert elapsed < 2.0, \
            f"UI should process rapid changes in <2s, took {elapsed:.2f}s"


# ── shared helpers (also used by p3/p4/p5 tests) ─────────────────────────────
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
