"""
ScreenWatermark Pro - Core Settings Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import json
import sys
from pathlib import Path
from core.constants import SETTINGS_FILE

DEFAULT_SETTINGS = {
    "watermark_path":    "",
    "wm_enabled":        True,
    "wm_mode":           "normal",
    "wm_position":       "center",
    "wm_opacity":        70,
    "wm_scale":          20,
    "wm_pattern_gap":     20,
    "ts_enabled":        True,
    "ts_format":         "%d/%m/%Y  %H:%M:%S",
    "ts_font_size":      22,
    "ts_color":          "#FFFFFF",
    "ts_bg_color":       "#000000",
    "ts_bg_opacity":     60,
    "ts_shadow":         True,
    "ts_bold":           False,
    "ts_outside_canvas": False,
    "delay_sec":         0,
    "hotkey_fullscreen": "<print_screen>",
    "hotkey_region":     "<ctrl>+<shift>+<f9>",
    "hotkey_history":    "<ctrl>+<f9>",
    "capture_mode":      "fullscreen",
    "run_at_startup":    False,
    "start_minimized":   False,
    "language":          "en",
}

def load_settings() -> dict:
    try:
        if SETTINGS_FILE.exists():
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = {**DEFAULT_SETTINGS, **data}
            if cfg["watermark_path"] and not Path(cfg["watermark_path"]).exists():
                cfg["watermark_path"] = ""
            return cfg
    except Exception as exc:
        print(f"[ScreenWatermark] Settings tidak dapat dibaca ({exc}), "
              f"menggunakan default.", file=sys.stderr)
    return DEFAULT_SETTINGS.copy()

def save_settings(cfg: dict) -> bool:
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
        return True
    except Exception as exc:
        print(f"[ScreenWatermark] Gagal menyimpan settings: {exc}", file=sys.stderr)
        return False
