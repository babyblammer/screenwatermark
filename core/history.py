"""
ScreenWatermark Pro - Core History Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import base64 as _b64
import io as _io
import json
import queue as _q
import threading
import uuid
import warnings
from datetime import datetime
from pathlib import Path
from PIL import Image

from core.constants import HISTORY_FILE, HISTORY_MAX

_history_io_q: "_q.Queue" = _q.Queue()

def _safe_image_open(source: "_io.BytesIO") -> "Image.Image | None":
    """Open image, suppress DecompressionBombWarning for corrupted/ oversized data."""
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=Image.DecompressionBombWarning)
        try:
            return Image.open(source)
        except Exception:
            return None

def _history_io_worker():
    """Worker tunggal: proses task I/O history secara serial (FIFO)."""
    while True:
        task = _history_io_q.get()
        try:
            if task is None:
                break
            fn, args, kwargs = task
            fn(*args, **kwargs)
        except Exception as exc:
            print(f"[HistoryIO] {exc}", file=sys.stderr)
        finally:
            _history_io_q.task_done()

_history_io_thread = threading.Thread(
    target=_history_io_worker, daemon=True, name="ScreenWM-HistoryIO")
_history_io_thread.start()

def _enqueue_save_history(history_deque, history_lock=None):
    """[R2] Antri save_history ke worker serial - thread-safe."""
    _history_io_q.put((save_history, (history_deque,), {"history_lock": history_lock}))

def save_history(history_deque, history_lock=None) -> bool:
    """Simpan riwayat screenshot ke HISTORY_FILE."""
    try:
        if history_lock is not None:
            with history_lock:
                snapshot = list(history_deque)
        else:
            snapshot = list(history_deque)
        entries = []
        for e in snapshot:
            try:
                _full_img = Image.open(_io.BytesIO(e["full_bytes"]))
                _jpeg_buf = _io.BytesIO()
                _full_img.convert("RGB").save(_jpeg_buf, "JPEG", quality=90, optimize=True)
                full_data = _b64.b64encode(_jpeg_buf.getvalue()).decode("ascii")
                full_fmt  = "jpeg"
            except Exception:
                full_data = _b64.b64encode(e["full_bytes"]).decode("ascii")
                full_fmt  = "png"
            entries.append({
                "entry_id":    e["entry_id"],
                "thumb_b64":   _b64.b64encode(e["thumb_bytes"]).decode("ascii"),
                "full_b64":    full_data,
                "full_fmt":    full_fmt,
                "timestamp":   e["timestamp"].isoformat(),
                "width":       e["width"],
                "height":      e["height"],
            })
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f)
        return True
    except Exception as exc:
        print(f"[ScreenWatermark] Gagal simpan history: {exc}", file=sys.stderr)
        return False

def load_history() -> list:
    """Muat riwayat screenshot dari HISTORY_FILE. Return list dict siap masuk deque."""
    try:
        if not HISTORY_FILE.exists():
            return []
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        entries = []
        for e in raw[-HISTORY_MAX:]:
            raw_full = _b64.b64decode(e["full_b64"])
            if e.get("full_fmt", "png") == "jpeg":
                try:
                    _img = _safe_image_open(_io.BytesIO(raw_full))
                    if _img:
                        _png_buf = _io.BytesIO()
                        _img.save(_png_buf, "PNG", optimize=True, compress_level=6)
                        full_bytes = _png_buf.getvalue()
                    else:
                        full_bytes = raw_full
                except Exception:
                    full_bytes = raw_full
            else:
                full_bytes = raw_full
            entries.append({
                "entry_id":    e.get("entry_id", str(uuid.uuid4())),
                "thumb_bytes": _b64.b64decode(e["thumb_b64"]),
                "full_bytes":  full_bytes,
                "timestamp":   datetime.fromisoformat(e["timestamp"]),
                "width":       int(e["width"]),
                "height":      int(e["height"]),
            })
        return entries
    except Exception as exc:
        print(f"[ScreenWatermark] Gagal muat history: {exc}, mulai dari kosong.", file=sys.stderr)
        return []
