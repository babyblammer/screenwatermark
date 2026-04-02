# tests/i18n/test_i18n_keys.py
"""
Phase 1 - Translation Keys Verification
Covers: TC-I18N-001 to TC-I18N-004
Tests that all required translation keys exist and function correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest


class TestI18nKeys:
    """Test all translation keys exist in both languages."""

    REQUIRED_KEYS = [
        # UI Labels
        "app_title", "settings", "preview", "history", "watermark", "timestamp",
        "fullscreen", "region", "copy", "enable", "mode", "opacity", "scale",
        "position", "font_size", "bold", "shadow", "outside", "file", "choose",
        "no_file", "startup", "capture", "hotkeys", "language", "close",
        "reset_default", "credits", "status_ready", "status_copied", "status_failed",
        "status_saved", "clear_all", "wm_on", "wm_warn", "wm_off", "on", "off",
        "run_at_startup", "start_minimized", "default_mode", "delay", "restart_required",
        "normal", "full", "pattern", "select_area", "screenshot", "click_region",
        "press_escape_cancel", "countdown_text", "cancel_esc", "show_panel",
        "run_in_background", "clear_history_confirm", "history_tab_hint",
        "history_empty", "preview_hint", "select_file",
        # NEW - Missing keys
        "exit", "screenshot_copied", "error_reading_history",
        "area_not_selected", "clear_history", "wm_active",
        # Dropdown values
        "wm_off_mode", "wm_normal_mode", "wm_full_mode", "wm_pattern_mode",
        "pos_bottom_left", "pos_bottom_right", "pos_top_left", "pos_top_right", "pos_center",
        "ts_off_mode", "ts_outside_mode",
        # UI Labels (for hardcoded strings)
        "label_mode", "label_opacity", "label_position", "label_scale",
        "label_path", "label_pattern_gap", "label_enable", "label_format",
        "label_text_color", "label_font_size",
        # Card titles
        "card_watermark", "card_timestamp",
        # Overlay texts
        "countdown_top", "countdown_bottom",
        "overlay_region_hint", "overlay_region_cancel",
        # History popup
        "history_title", "history_copy_hint", "history_no_items",
        "history_copied", "copy_button",
        # Settings
        "startup_status_registered", "startup_status_not_registered",
        "hotkeys_title", "hotkeys_note", "credits_title",
        # Misc
        "confirm_restart", "restart_now", "restart_later",
        "area_screenshot", "wm_file_not_set", "wm_disabled",
        "seconds", "reset_region", "region_coords",
    ]

    def test_all_keys_exist_in_english(self):
        """TC-I18N-001: All required keys exist in English translation."""
        from i18n import _STRINGS, set_language
        set_language("en")
        
        missing = []
        for key in self.REQUIRED_KEYS:
            if key not in _STRINGS["en"]:
                missing.append(key)
        
        assert not missing, f"Missing English keys: {missing}"

    def test_all_keys_exist_in_indonesian(self):
        """TC-I18N-002: All required keys exist in Indonesian translation."""
        from i18n import _STRINGS, set_language
        set_language("id")
        
        missing = []
        for key in self.REQUIRED_KEYS:
            if key not in _STRINGS["id"]:
                missing.append(key)
        
        assert not missing, f"Missing Indonesian keys: {missing}"

    def test_t_function_returns_correct_value(self):
        """TC-I18N-003: t() returns correct value for current language."""
        from i18n import t, set_language
        
        # Test English
        set_language("en")
        assert t("settings") == "Settings"
        assert t("watermark") == "Watermark"
        assert t("close") == "Close"
        
        # Test Indonesian
        set_language("id")
        assert t("settings") == "Pengaturan"
        assert t("watermark") == "Watermark"
        assert t("close") == "Tutup"

    def test_t_function_fallback_to_english(self):
        """TC-I18N-004: t() returns key name for missing keys (fallback)."""
        from i18n import t, set_language
        set_language("en")
        
        result = t("nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz", \
            "Missing keys should return key name as fallback"

    def test_set_language_switches_correctly(self):
        """TC-I18N-005: set_language() switches between en and id."""
        from i18n import set_language, get_language
        
        set_language("en")
        assert get_language() == "en"
        
        set_language("id")
        assert get_language() == "id"
        
        # Invalid language should keep previous
        set_language("invalid")
        assert get_language() == "id"

    def test_no_empty_translations(self):
        """TC-I18N-006: No translation value should be empty string."""
        from i18n import _STRINGS
        
        for lang in ["en", "id"]:
            empty_keys = []
            for key, value in _STRINGS[lang].items():
                if value == "" or value is None:
                    empty_keys.append(key)
            
            assert not empty_keys, f"Empty translations in {lang}: {empty_keys}"

    def test_all_keys_match_between_languages(self):
        """TC-I18N-007: Same keys exist in both en and id."""
        from i18n import _STRINGS
        
        en_keys = set(_STRINGS["en"].keys())
        id_keys = set(_STRINGS["id"].keys())
        
        missing_in_id = en_keys - id_keys
        missing_in_en = id_keys - en_keys
        
        assert not missing_in_id, f"Keys in en but not id: {missing_in_id}"
        assert not missing_in_en, f"Keys in id but not en: {missing_in_en}"
