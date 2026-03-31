# tests/core/test_m1_core.py
"""
Phase M1 — core/ Extraction Verification
Run at M1 milestone: pytest tests/core/ -v
Headless — no display, no app window required.
Covers: TC-M1-001 → TC-M1-010
"""

import pytest
import io
import json
from pathlib import Path
from PIL import Image


# ── TC-M1-001 ─────────────────────────────────────────────────────────────────

class TestConstantsImport:

    def test_constants_importable(self):
        """TC-M1-001a: core/constants.py imports cleanly."""
        from core.constants import (BG, PANEL, CARD, ACCENT, SUCCESS,
                                     TEXT, MUTED, WARN, PREVIEW_W, PREVIEW_H,
                                     HISTORY_MAX, SETTINGS_FILE, HISTORY_FILE)
        assert BG == "#0a0a10"
        assert PREVIEW_W == 320
        assert PREVIEW_H == 180
        assert HISTORY_MAX == 5

    def test_palette_values_are_hex(self):
        """TC-M1-001b: All palette constants are valid 7-char hex strings."""
        from core import constants as c
        for name in ["BG","PANEL","CARD","CARD2","BORDER","ACCENT",
                     "ACCENT2","SUCCESS","TEXT","MUTED","WARN"]:
            val = getattr(c, name)
            assert val.startswith("#") and len(val) == 7, \
                f"{name}={val!r} is not a valid hex color"


# ── TC-M1-002 / TC-M1-003 / TC-M1-004 ────────────────────────────────────────

class TestSettingsIO:

    def test_load_settings_returns_defaults_when_no_file(self, tmp_path, monkeypatch):
        """TC-M1-002: load_settings() returns DEFAULT_SETTINGS when file absent."""
        fake_path = tmp_path / ".screenwatermark_settings.json"
        monkeypatch.setattr("core.settings.SETTINGS_FILE", fake_path)
        from core.settings import load_settings, DEFAULT_SETTINGS
        cfg = load_settings()
        for key in DEFAULT_SETTINGS:
            assert key in cfg, f"Key '{key}' missing from loaded settings"

    def test_save_settings_writes_valid_json(self, tmp_path, monkeypatch):
        """TC-M1-003: save_settings() writes valid JSON file."""
        fake_path = tmp_path / ".screenwatermark_settings.json"
        monkeypatch.setattr("core.settings.SETTINGS_FILE", fake_path)
        from core.settings import save_settings, DEFAULT_SETTINGS
        result = save_settings(DEFAULT_SETTINGS.copy())
        assert result is True
        assert fake_path.exists()
        with open(fake_path) as f:
            data = json.load(f)
        assert "wm_opacity" in data

    def test_settings_round_trip(self, tmp_path, monkeypatch):
        """TC-M1-004: save then load returns identical dict."""
        fake_path = tmp_path / ".screenwatermark_settings.json"
        monkeypatch.setattr("core.settings.SETTINGS_FILE", fake_path)
        from core.settings import save_settings, load_settings, DEFAULT_SETTINGS
        cfg_in = {**DEFAULT_SETTINGS, "wm_opacity": 42, "ts_font_size": 33}
        save_settings(cfg_in)
        cfg_out = load_settings()
        assert cfg_out["wm_opacity"] == 42
        assert cfg_out["ts_font_size"] == 33

    def test_default_settings_has_language_key(self):
        """DEFAULT_SETTINGS must include 'language' key (added in M1)."""
        from core.settings import DEFAULT_SETTINGS
        assert "language" in DEFAULT_SETTINGS, \
            "DEFAULT_SETTINGS missing 'language' key — add it in core/settings.py"
        assert DEFAULT_SETTINGS["language"] == "en"


# ── TC-M1-005 / TC-M1-006 / TC-M1-007 ────────────────────────────────────────

class TestApplyWatermark:

    @pytest.fixture
    def base_img(self):
        return Image.new("RGB", (800, 600), (100, 100, 100))

    @pytest.fixture
    def wm_path(self, tmp_path):
        p = tmp_path / "test_wm.png"
        Image.new("RGBA", (200, 100), (255, 0, 0, 180)).save(p)
        return str(p)

    def test_no_wm_path_returns_original(self, base_img):
        """TC-M1-005: apply_watermark returns original when watermark_path empty."""
        from core.settings import DEFAULT_SETTINGS
        from core.render import apply_watermark
        cfg = {**DEFAULT_SETTINGS, "watermark_path": "", "wm_enabled": True}
        result = apply_watermark(base_img.copy(), cfg)
        assert result.tobytes() == base_img.convert("RGB").tobytes()

    def test_disabled_returns_original(self, base_img, wm_path):
        """TC-M1-006: apply_watermark returns original when wm_enabled=False."""
        from core.settings import DEFAULT_SETTINGS
        from core.render import apply_watermark
        cfg = {**DEFAULT_SETTINGS, "watermark_path": wm_path, "wm_enabled": False}
        result = apply_watermark(base_img.copy(), cfg)
        assert result.tobytes() == base_img.convert("RGB").tobytes()

    def test_normal_mode_modifies_image(self, base_img, wm_path):
        """TC-M1-007: apply_watermark modifies image in Normal mode."""
        from core.settings import DEFAULT_SETTINGS
        from core.render import apply_watermark
        from core.wm_cache import invalidate_wm_cache
        invalidate_wm_cache()
        cfg = {**DEFAULT_SETTINGS, "watermark_path": wm_path,
               "wm_enabled": True, "wm_mode": "normal",
               "wm_opacity": 70, "wm_scale": 20, "wm_position": "bottom-left"}
        result = apply_watermark(base_img.copy(), cfg)
        assert result.tobytes() != base_img.convert("RGB").tobytes(), \
            "apply_watermark should modify the image"


# ── TC-M1-008 / TC-M1-009 ─────────────────────────────────────────────────────

class TestApplyTimestamp:

    @pytest.fixture
    def base_img(self):
        return Image.new("RGB", (800, 600), (100, 100, 100))

    def test_outside_extends_height(self, base_img):
        """TC-M1-009: apply_timestamp extends height when enabled."""
        from core.settings import DEFAULT_SETTINGS
        from core.render import apply_timestamp
        cfg = {**DEFAULT_SETTINGS, "ts_enabled": True}
        result = apply_timestamp(base_img.copy(), cfg)
        assert result.height > base_img.height, \
            f"TS enabled: result.height={result.height} should be > {base_img.height}"

    def test_disabled_returns_original(self, base_img):
        """apply_timestamp disabled returns original unchanged."""
        from core.settings import DEFAULT_SETTINGS
        from core.render import apply_timestamp
        cfg = {**DEFAULT_SETTINGS, "ts_enabled": False}
        result = apply_timestamp(base_img.copy(), cfg)
        assert result.tobytes() == base_img.convert("RGB").tobytes()


# ── TC-M1-010 ─────────────────────────────────────────────────────────────────

class TestWmCache:

    def test_invalidate_clears_both_caches(self, tmp_path):
        """TC-M1-010: invalidate_wm_cache() empties _wm_cache and _wm_resize_cache."""
        from core.wm_cache import (invalidate_wm_cache,
                                    _wm_cache, _wm_resize_cache,
                                    _wm_cache_lock, _wm_load_failed)
        # Prime the cache with a dummy entry
        wm_path = str(tmp_path / "wm.png")
        Image.new("RGBA", (100, 50), (255, 0, 0, 180)).save(wm_path)
        with _wm_cache_lock:
            from PIL import Image as _img
            _wm_cache[wm_path] = _img.new("RGBA", (100, 50))
            _wm_resize_cache[(wm_path, 50, 25)] = _img.new("RGBA", (50, 25))
        # Invalidate
        invalidate_wm_cache()
        with _wm_cache_lock:
            assert len(_wm_cache) == 0, "wm_cache should be empty after invalidation"
            assert len(_wm_resize_cache) == 0, "resize_cache should be empty after invalidation"
            assert len(_wm_load_failed) == 0, "load_failed set should be cleared"

    def test_get_cached_watermark_returns_none_for_empty_path(self):
        """get_cached_watermark returns None when path is empty string."""
        from core.wm_cache import get_cached_watermark
        result = get_cached_watermark("")
        assert result is None

    def test_get_cached_watermark_returns_image(self, tmp_path):
        """get_cached_watermark returns PIL Image for valid path."""
        from core.wm_cache import get_cached_watermark, invalidate_wm_cache
        invalidate_wm_cache()
        wm_path = str(tmp_path / "wm.png")
        Image.new("RGBA", (100, 50), (255, 0, 0, 180)).save(wm_path)
        result = get_cached_watermark(wm_path)
        assert result is not None
        assert result.mode == "RGBA"


# ── Bonus: safe_hex_to_rgb ────────────────────────────────────────────────────

class TestUtils:

    def test_safe_hex_to_rgb_valid(self):
        from core.utils import safe_hex_to_rgb
        assert safe_hex_to_rgb("#FF0000") == (255, 0, 0)
        assert safe_hex_to_rgb("#ffffff") == (255, 255, 255)
        assert safe_hex_to_rgb("#000000") == (0, 0, 0)

    def test_safe_hex_to_rgb_invalid_returns_white(self):
        from core.utils import safe_hex_to_rgb
        assert safe_hex_to_rgb("notacolor") == (255, 255, 255)
        assert safe_hex_to_rgb("") == (255, 255, 255)
