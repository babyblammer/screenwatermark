"""
ScreenWatermark Pro - Core Clipboard Module
Extracted from Screen Watermark_3.9.1f_HF1.py
"""

import io
import os
import subprocess
import sys
import tempfile

def copy_image_to_clipboard(img: "Image.Image"):
    if sys.platform == "win32":    _cb_win32(img)
    elif sys.platform == "darwin": _cb_macos(img)
    else:                          _cb_linux(img)

def _cb_win32(img):
    import win32clipboard, win32con, time
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "BMP")
    data = buf.getvalue()[14:]
    last_err = None
    for attempt in range(5):
        try:
            win32clipboard.OpenClipboard(None)
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32con.CF_DIB, data)
            finally:
                win32clipboard.CloseClipboard()
            return
        except Exception as e:
            last_err = e
            time.sleep(0.05)
    raise last_err

def _cb_macos(img):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f.name, "PNG"); tmp = f.name
        subprocess.run(["osascript", "-e",
            f'set the clipboard to (read (POSIX file "{tmp}") as \u00abclass PNGf\u00bb)'],
            check=True, timeout=10)
    finally:
        if tmp and os.path.exists(tmp): os.unlink(tmp)

def _cb_linux(img):
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f.name, "PNG"); tmp = f.name
        r = subprocess.run(["xclip", "-selection", "clipboard",
                             "-t", "image/png", "-i", tmp], timeout=10)
        if r.returncode != 0:
            raise RuntimeError("xclip gagal. sudo apt install xclip")
    except FileNotFoundError:
        raise RuntimeError("xclip tidak ditemukan. Install dengan: sudo apt install xclip")
    finally:
        if tmp and os.path.exists(tmp): os.unlink(tmp)
