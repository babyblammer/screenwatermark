"""
ScreenWatermark Pro - Core Watermark Cache Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import os
import threading
from PIL import Image

_wm_cache: dict        = {}
_wm_resize_cache: dict = {}
_wm_load_failed: set   = set()
_wm_cache_lock         = threading.Lock()

def get_cached_watermark(path: str) -> "Image.Image | None":
    """Return cached RGBA watermark (copy), reload jika path berubah.
    Thread-safe: semua akses ke _wm_cache dilindungi _wm_cache_lock."""
    if not path:
        return None
    with _wm_cache_lock:
        if path in _wm_cache:
            return _wm_cache[path].copy()
        if path in _wm_load_failed:
            return None
        if not os.path.exists(path):
            return None
        _wm_cache.clear()
        _wm_resize_cache.clear()
        try:
            _wm_cache[path] = Image.open(path).convert("RGBA")
        except Exception:
            _wm_load_failed.add(path)
            return None
        return _wm_cache[path].copy()

def invalidate_wm_cache():
    """[P2] Invalidasi original cache DAN resize cache saat path berubah."""
    with _wm_cache_lock:
        _wm_cache.clear()
        _wm_resize_cache.clear()
        _wm_load_failed.clear()

def _get_wm_resized(path: str, new_w: int, new_h: int) -> "Image.Image | None":
    """[P2] Cache watermark yang sudah di-resize per (path, w, h).
    Thread-safe: dilindungi _wm_cache_lock."""
    if not path:
        return None
    key = (path, new_w, new_h)
    with _wm_cache_lock:
        if key in _wm_resize_cache:
            return _wm_resize_cache[key].copy()
        if path not in _wm_cache:
            if path in _wm_load_failed:
                return None
            if not os.path.exists(path):
                return None
            try:
                _wm_cache[path] = Image.open(path).convert("RGBA")
            except Exception:
                _wm_load_failed.add(path)
                return None
        orig = _wm_cache[path]
        resized = orig.resize((max(1, new_w), max(1, new_h)), Image.LANCZOS)
        _wm_resize_cache[key] = resized
        if len(_wm_resize_cache) > 32:
            _wm_resize_cache.pop(next(iter(_wm_resize_cache)))
        return _wm_resize_cache[key].copy()
