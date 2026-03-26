# ScreenWatermark Pro v8.0 — Implementation Guideline
**For: Programmer | Reviewed by: PM/Design**
Version: 2.0-SYNCED | Base build: Screen_Watermark_3.9.1f_HF1.py

---

## Read This First

Work in strict order: **M1 → M2 → M3 → P0 → P1 → P2 → [P3+P4+P5] → P6 → P7 → GC**.

M1–M3 produce zero user-visible change. They are pure code moves.
Run the automated tests after each milestone before proceeding.

---

## Global Rules

### Never modify logic in these functions (they move to `core/` and `system/` but content stays identical)

```
apply_watermark()         apply_timestamp()
_do_screenshot()          _start_screenshot()
_countdown()              _cancel_countdown()
RegionSelector            CountdownOverlay
HotkeyManager             HotkeyRecorder
_register_all_hotkeys()   _hk_fullscreen/region/history()
save_settings()           load_settings()
save_history()            load_history()
_enqueue_save_history()   _history_io_worker()
copy_image_to_clipboard() _cb_win32/macos/linux()
_acquire_single_instance() _ipc_server_thread()
get_cached_watermark()    _get_wm_resized()
invalidate_wm_cache()     load_font()
set_run_at_startup()      get_run_at_startup()
_start_tray()             _hide_to_tray()
_quit_app()
```

### Dependency rule (enforced always)

```
core/    ← ZERO imports from ui/ or system/
system/  ← ZERO imports from ui/
ui/      ← imports from core/ and system/ freely
```

---

## Step M1 — Extract `core/`

**Target:** `screenwatermark/core/`
**Duration:** 0.5 day
**Test:** `pytest tests/core/ -v` — headless, no display

### Method (repeat for each module)

1. Create target file (e.g. `core/settings.py`)
2. Copy functions verbatim from monolith
3. Add necessary imports at top of target file
4. In the monolith, replace the original definition with `from core.settings import load_settings, save_settings`
5. Run `python Screen_Watermark_3.9.1f_HF1.py` — app must launch unchanged
6. Only then move to the next function

### core/constants.py

```python
# core/constants.py
PREVIEW_W     = 320
PREVIEW_H     = 180
HISTORY_MAX   = 5
SETTINGS_FILE = Path.home() / ".screenwatermark_settings.json"
HISTORY_FILE  = Path.home() / ".screenwatermark_history.json"

BG      = "#0a0a10"; PANEL  = "#111118"; CARD   = "#16161f"
CARD2   = "#1c1c28"; BORDER = "#252535"; ACCENT = "#6c63ff"
ACCENT2 = "#ff6584"; SUCCESS= "#43e97b"; TEXT   = "#e2e2f0"
MUTED   = "#5a5a7a"; WARN   = "#f5a623"

FONT      = "Segoe UI"
FONT_MONO = "Consolas"
```

### core/settings.py

Move verbatim: `DEFAULT_SETTINGS`, `load_settings()`, `save_settings()`.
Add `"language": "en"` to `DEFAULT_SETTINGS` here.

```python
# core/settings.py
from pathlib import Path
import json, sys
from core.constants import SETTINGS_FILE

DEFAULT_SETTINGS = { ... }  # verbatim from monolith + "language": "en"

def load_settings() -> dict: ...   # verbatim
def save_settings(cfg: dict) -> bool: ...  # verbatim
```

### core/history.py

Move: `save_history()`, `load_history()`, `_history_io_q`, `_history_io_worker()`, `_enqueue_save_history()`.

```python
# core/history.py
from core.constants import HISTORY_FILE, HISTORY_MAX
from PIL import Image
import json, io, uuid, threading, queue as _q
from datetime import datetime
from pathlib import Path
```

### core/render.py

Move: `apply_watermark()`, `apply_timestamp()`.

```python
# core/render.py
from core.constants import MUTED
from core.font_cache import load_font
from core.wm_cache   import get_cached_watermark, _get_wm_resized
from core.utils      import safe_hex_to_rgb, safe_strftime
from PIL import Image, ImageDraw
from datetime import datetime
import sys
```

### core/clipboard.py

Move: `copy_image_to_clipboard()`, `_cb_win32()`, `_cb_macos()`, `_cb_linux()`.

### core/font_cache.py

Move: `load_font()` with `@lru_cache`.

### core/wm_cache.py

Move: `_wm_cache`, `_wm_resize_cache`, `_wm_load_failed`, `_wm_cache_lock`,
`get_cached_watermark()`, `invalidate_wm_cache()`, `_get_wm_resized()`.

### core/utils.py

Move: `safe_hex_to_rgb()`, `safe_strftime()`.

### Verification

```bash
pytest tests/core/ -v --html=tests/reports/report_M1.html --self-contained-html
# All TC-M1-001 → TC-M1-010 must PASS
python Screen_Watermark_3.9.1f_HF1.py   # app unchanged
```

---

## Step M2 — Extract `system/`

**Target:** `screenwatermark/system/`
**Duration:** 0.5 day
**Test:** `pytest tests/system/ -v` — headless

### system/hotkeys.py

Move: `HotkeyManager`, `HotkeyRecorder`, `_ensure_pynput()`, `_pynput_kb`, `_HK_MOD_NAMES`, `HOTKEY_PRESETS`, `_PRESET_LABEL`, `_preset_label()`, `_preset_value()`.

```python
# system/hotkeys.py
import threading
from typing import Optional
```

### system/startup.py

Move: `_get_startup_script_path()`, `_get_pythonw_path()`, `_win_startup_approved_path()`,
`_win_build_cmd()`, `set_run_at_startup()`, `get_run_at_startup()`.

### system/ipc.py

Move: `_acquire_single_instance()`, `_ipc_server_thread()`, `_SW_IPC_SERVER`,
`_SW_LOCK_FILE`, `_SW_IPC_MAGIC`, `_SW_IPC_ACK`, `_ipc_pending_show`.

### system/tray.py

Move: `_make_tray_icon()`, `_win_toast()`, `_app_ref_notify`.

```python
# system/tray.py
from PIL import Image, ImageDraw
import pystray
```

### Verification

```bash
pytest tests/system/ -v --html=tests/reports/report_M2.html --self-contained-html
# All TC-M2-001 → TC-M2-008 must PASS
python Screen_Watermark_3.9.1f_HF1.py   # app unchanged
```

---

## Step M3 — Isolate `ui/` Classes

**Target:** `screenwatermark/ui/`
**Duration:** 0.5 day
**Test:** Manual smoke (TC-M3-001 → TC-M3-006)

### ui/overlays.py

Move verbatim: `CountdownOverlay`, `RegionSelector`.

```python
# ui/overlays.py — IMPORTANT: pure tkinter only, no customtkinter ever
import tkinter as tk
from core.constants import ACCENT, TEXT, MUTED, BORDER
from system.hotkeys import _ensure_pynput, _pynput_kb
```

### ui/history_popup.py

Move verbatim: `HistoryPopup`.

```python
# ui/history_popup.py
import tkinter as tk
from core.constants import PANEL, CARD, ACCENT, ACCENT2, SUCCESS, TEXT, MUTED, BORDER
from core.clipboard import copy_image_to_clipboard
```

### ui/settings_window.py

Move verbatim: `SettingsWindow`.

```python
# ui/settings_window.py
import tkinter as tk
from tkinter import ttk
from core.constants import BG, PANEL, CARD, ACCENT, ACCENT2, SUCCESS, TEXT, MUTED, BORDER, WARN
from core.settings  import load_settings, save_settings
from system.hotkeys import _preset_label, HOTKEY_PRESETS
from system.startup import set_run_at_startup, get_run_at_startup
```

### ui/main_window.py

Move verbatim: `ScreenWatermarkApp`.
Update all class-level imports to use module paths (see UI_UX_Spec_v8.0.md §0).

### main.py (~30 lines)

```python
# main.py
import sys
import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

from core.settings import load_settings
import i18n
cfg = load_settings()
i18n.set_language(cfg.get("language", "en"))

from system.ipc import _acquire_single_instance, _ipc_server_thread, _SW_IPC_SERVER
from ui.main_window import ScreenWatermarkApp
import threading

if __name__ == "__main__":
    _is_first, _ipc_port = _acquire_single_instance()
    if not _is_first:
        sys.exit(0)
    _app_ref = []
    if _SW_IPC_SERVER is not None:
        t = threading.Thread(
            target=_ipc_server_thread,
            args=(_SW_IPC_SERVER, _app_ref),
            daemon=True, name="ScreenWM-IPC")
        t.start()
    app = ScreenWatermarkApp()
    _app_ref.append(app)
    app.mainloop()
    try:
        from system.ipc import _SW_LOCK_FILE
        _SW_LOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass
```

### Verification

```bash
python -m screenwatermark   # or: python main.py
# TC-M3-001 → TC-M3-006 all PASS (manual smoke)
```

---

## Phase P0 — Environment + i18n + ui/widgets/

**Duration:** 1.5 days

### P0.1 Requirements

Add to `requirements_v8.txt`:
```
customtkinter>=5.2.2
pywinstyles>=1.8
```

### P0.2 i18n.py (root level)

```python
# i18n.py
_STRINGS = {
    "en": {
        "app_title": "ScreenWatermark Pro",
        "settings": "Settings", "preview": "Preview", "history": "History",
        "watermark": "Watermark", "timestamp": "Timestamp",
        "fullscreen": "Fullscreen", "region": "Region", "copy": "Copy",
        "enable": "Enable", "mode": "Mode", "opacity": "Opacity",
        "scale": "Scale", "position": "Position", "font_size": "Font Size",
        "bold": "Bold", "shadow": "Shadow", "outside": "Outside",
        "file": "File", "choose": "Choose…", "no_file": "no file",
        "startup": "Startup", "capture": "Capture", "hotkeys": "Hotkeys",
        "language": "Language", "close": "Close",
        "reset_default": "↺ Reset to Default", "credits": "Credits",
        "status_ready": "Ready", "status_copied": "✓ Screenshot copied to clipboard!",
        "status_failed": "✕ Screenshot failed.", "status_saved": "✓ Settings saved",
        "clear_all": "🗑 Clear All", "wm_on": "WM ✓", "wm_warn": "WM ⚠",
        "wm_off": "WM OFF", "on": "ON", "off": "OFF",
        "run_at_startup": "Run at system startup",
        "start_minimized": "Start minimized to tray",
        "default_mode": "Default mode", "delay": "Delay",
        "restart_required": "Restart required to apply language change.",
        "normal": "Normal", "full": "Full", "pattern": "Pattern",
    },
    "id": {
        "app_title": "ScreenWatermark Pro",
        "settings": "Pengaturan", "preview": "Pratinjau", "history": "Riwayat",
        "watermark": "Watermark", "timestamp": "Timestamp",
        "fullscreen": "Layar Penuh", "region": "Pilih Area", "copy": "Salin",
        "enable": "Aktifkan", "mode": "Mode", "opacity": "Opacity",
        "scale": "Ukuran", "position": "Posisi", "font_size": "Ukuran Font",
        "bold": "Tebal", "shadow": "Bayangan", "outside": "Di luar",
        "file": "File", "choose": "Pilih…", "no_file": "belum dipilih",
        "startup": "Startup", "capture": "Ambil Layar", "hotkeys": "Hotkey",
        "language": "Bahasa", "close": "Tutup",
        "reset_default": "↺ Reset ke Default", "credits": "Kredit",
        "status_ready": "Siap", "status_copied": "✓ Screenshot disalin ke clipboard!",
        "status_failed": "✕ Screenshot gagal.", "status_saved": "✓ Pengaturan tersimpan",
        "clear_all": "🗑 Hapus Semua", "wm_on": "WM ✓", "wm_warn": "WM ⚠",
        "wm_off": "WM OFF", "on": "ON", "off": "OFF",
        "run_at_startup": "Jalankan otomatis saat startup",
        "start_minimized": "Mulai tersembunyi di System Tray",
        "default_mode": "Mode default", "delay": "Delay",
        "restart_required": "Restart diperlukan untuk menerapkan bahasa.",
        "normal": "Normal", "full": "Full", "pattern": "Pattern",
    }
}
_lang = "en"

def set_language(lang: str):
    global _lang
    if lang in _STRINGS: _lang = lang

def t(key: str) -> str:
    return _STRINGS.get(_lang, _STRINGS["en"]).get(key, key)
```

### P0.3 ui/widgets/accordion.py

```python
# ui/widgets/accordion.py
import customtkinter as ctk
from core.constants import CARD, CARD2, BORDER, ACCENT, TEXT, MUTED, FONT, FONT_MONO

class CTkAccordion(ctk.CTkFrame):
    def __init__(self, parent, title: str, icon: str = "",
                 open_by_default: bool = False,
                 on_toggle=None, **kwargs):
        super().__init__(parent, fg_color=CARD, corner_radius=10,
                         border_width=1, border_color=BORDER, **kwargs)
        self._open = open_by_default
        self._on_toggle_cb = on_toggle

        # Header
        self._hdr = ctk.CTkFrame(self, fg_color="transparent", height=38)
        self._hdr.pack(fill="x")
        self._hdr.pack_propagate(False)
        self._hdr.bind("<Button-1>", lambda e: self.toggle())

        if icon:
            ctk.CTkLabel(self._hdr, text=icon, fg_color="transparent",
                         font=(FONT, 12)).pack(side="left", padx=(12, 6), pady=8)
        self._title_lbl = ctk.CTkLabel(
            self._hdr, text=title, font=(FONT, 11, "bold"),
            text_color=TEXT, fg_color="transparent")
        self._title_lbl.pack(side="left")
        self._summary_lbl = ctk.CTkLabel(
            self._hdr, text="", font=(FONT_MONO, 9),
            text_color=MUTED, fg_color="transparent")
        self._summary_lbl.pack(side="right", padx=(0, 8))
        self._chevron = ctk.CTkLabel(
            self._hdr, text="▲" if open_by_default else "▼",
            font=(FONT, 9), text_color=MUTED, fg_color="transparent")
        self._chevron.pack(side="right", padx=(0, 6))

        # Separator
        ctk.CTkFrame(self, fg_color=BORDER, height=1,
                     corner_radius=0).pack(fill="x")

        # Body container
        self._body = ctk.CTkFrame(self, fg_color="transparent")
        if open_by_default:
            self._body.pack(fill="x", padx=12, pady=(6, 10))

    def toggle(self):
        self._open = not self._open
        if self._open:
            self._body.pack(fill="x", padx=12, pady=(6, 10))
            self._chevron.configure(text="▲")
            self.configure(border_color="#2e2e48")
        else:
            self._body.pack_forget()
            self._chevron.configure(text="▼")
            self.configure(border_color=BORDER)
        if self._on_toggle_cb:
            self._on_toggle_cb(self._open)

    def set_summary(self, text: str):
        self._summary_lbl.configure(text=text)

    @property
    def body(self) -> ctk.CTkFrame:
        return self._body

    @property
    def is_open(self) -> bool:
        return self._open
```

### P0.4 ui/widgets/config_rows.py

```python
# ui/widgets/config_rows.py
import customtkinter as ctk
from core.constants import CARD, CARD2, BORDER, ACCENT, TEXT, MUTED, FONT, FONT_MONO

def label(parent, text: str, pack=True) -> ctk.CTkLabel:
    lbl = ctk.CTkLabel(parent, text=text, font=(FONT, 9),
                       text_color=MUTED, fg_color="transparent")
    if pack:
        lbl.pack(side="left", padx=(0, 3))
    return lbl

def sep(parent) -> ctk.CTkFrame:
    f = ctk.CTkFrame(parent, fg_color=BORDER, width=1, height=18, corner_radius=0)
    f.pack(side="left", padx=5)
    return f

def slider_row(parent, lbl_text: str, var, from_: int, to: int,
               unit: str = "", width: int = 70) -> ctk.CTkLabel:
    label(parent, lbl_text)
    val_lbl = ctk.CTkLabel(parent, text=f"{var.get()} {unit}",
                            font=(FONT_MONO, 9), text_color=ACCENT,
                            fg_color="transparent", width=36)
    ctk.CTkSlider(parent, from_=from_, to=to, variable=var, width=width, height=14,
                  command=lambda v, l=val_lbl, u=unit:
                      l.configure(text=f"{int(float(v))} {u}")
                  ).pack(side="left", padx=(0, 2))
    val_lbl.pack(side="left")
    return val_lbl

def pill_toggle(parent, values: list[str], default: str,
                command) -> ctk.CTkFrame:
    frame = ctk.CTkFrame(parent, fg_color=CARD2, corner_radius=6,
                          border_width=1, border_color=BORDER)
    frame.pack(side="left", padx=(0, 4))
    btns = {}
    def _click(v):
        for k, b in btns.items():
            b.configure(fg_color=ACCENT if k == v else "transparent",
                        text_color="white" if k == v else MUTED)
        command(v)
    for val in values:
        b = ctk.CTkButton(
            frame, text=val, width=34, height=22,
            fg_color=ACCENT if val == default else "transparent",
            hover_color=CARD2,
            text_color="white" if val == default else MUTED,
            corner_radius=5, font=(FONT, 9),
            command=lambda v=val: _click(v))
        b.pack(side="left", padx=2, pady=2)
        btns[val] = b
    return frame

def color_swatch(parent, var, label_text: str = "") -> ctk.CTkButton:
    if label_text:
        label(parent, label_text)
    btn = ctk.CTkButton(
        parent, text="", width=22, height=22, corner_radius=4,
        fg_color=var.get(), hover_color=var.get())
    btn.pack(side="left", padx=(0, 4))
    return btn
```

---

## Phases P1–P7

Identical task lists to v1.0 of this guideline. Now applied to the modular
package files (`ui/main_window.py`, `ui/settings_window.py`) instead of a monolith.

All code stubs from v1.0 remain valid. Import paths now use module imports
(see Behavior_Addendum_v8.0.md §1 for the full import block).

Key additions vs v1.0:
- Phase P3 uses `CTkAccordion` from `ui/widgets/accordion.py`
- Phase P4 uses `CTkAccordion` from `ui/widgets/accordion.py`
- Phase P5 uses `SplitShotButton` from `ui/widgets/shot_buttons.py`
- Phase P2 uses `PanelToggle` from `ui/widgets/panel_toggle.py`

---

## Gold Candidate

**Build:** `python -m screenwatermark` or `python main.py`

```bash
# Run full test suite
pytest tests/ -v --html=tests/reports/report_GCa.html --self-contained-html

# Or:
run_tests_gc.bat
```

### Delivery checklist
- [ ] `screenwatermark/` full package
- [ ] `i18n.py`
- [ ] `requirements_v8.txt`
- [ ] `ScreenWatermark_Changelog.md` updated
- [ ] `QA_Tracker_v8.0_versioned.xlsx`

---

## Quick Reference — Phase Order

```
M1 (core/)  →  M2 (system/)  →  M3 (ui/ split)
                                      ↓
                               P0 (env + i18n + widgets)
                                      ↓
                               P1 (CTk shell)
                                      ↓
                               P2 (toggle + panels)
                                      ↓
                    ┌─────────────────┼──────────────┐
                   P3 (WM)          P4 (TS)         P5 (buttons)
                    └─────────────────┼──────────────┘
                                      ↓
                               P6 (Settings)
                                      ↓
                               P7 (i18n)
                                      ↓
                               GC (full regression)
```
