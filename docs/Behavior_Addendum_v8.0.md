# ScreenWatermark Pro v8.0 — Accordion & Window Behavior Addendum
**Addendum to: UI_UX_Spec_v8.0.md**
Version: 2.0-SYNCED | Module paths updated throughout

All code stubs reference the modular package structure from M1–M3.
File target: `ui/main_window.py` unless noted otherwise.

---

## 1. Module Imports (top of `ui/main_window.py`)

```python
from core.constants  import (BG, PANEL, CARD, CARD2, BORDER, ACCENT, ACCENT2,
                              SUCCESS, TEXT, MUTED, WARN, PREVIEW_W, PREVIEW_H,
                              HISTORY_MAX)
from core.settings   import load_settings, save_settings, DEFAULT_SETTINGS
from core.history    import (save_history, load_history,
                              _enqueue_save_history, _history_io_q)
from core.render     import apply_watermark, apply_timestamp
from core.clipboard  import copy_image_to_clipboard
from core.font_cache import load_font
from core.wm_cache   import (get_cached_watermark, invalidate_wm_cache,
                              _wm_cache, _wm_resize_cache, _wm_cache_lock)
from core.utils      import safe_hex_to_rgb, safe_strftime
from system.hotkeys  import HotkeyManager, _ensure_pynput, _pynput_kb
from system.tray     import _make_tray_icon, _win_toast
from system.startup  import set_run_at_startup, get_run_at_startup
from system.ipc      import _acquire_single_instance, _ipc_server_thread
from ui.overlays     import CountdownOverlay, RegionSelector
from ui.settings_window import SettingsWindow
from ui.history_popup   import HistoryPopup
from ui.widgets.accordion   import CTkAccordion
from ui.widgets.panel_toggle import PanelToggle
from ui.widgets.shot_buttons import SplitShotButton
from ui.widgets.config_rows  import slider_row, pill_toggle, color_swatch
from i18n import t
import customtkinter as ctk
import tkinter as tk
```

---

## 2. Accordion Behavior — Final Decisions

### 2.1 Simultaneous Open

Both WM and TS accordions can be open simultaneously. No exclusive-close logic.

```python
# ui/main_window.py
def _toggle_wm_accordion(self):
    self._wm_acc_open = not self._wm_acc_open
    if self._wm_acc_open:
        self._wm_body.pack(fill="x", padx=12, pady=(0, 12))
        self._wm_accordion.configure(border_color="#2e2e48")
        self.after(60, lambda: self._scroll_to(self._wm_accordion))
    else:
        self._wm_body.pack_forget()
        self._wm_accordion.configure(border_color=BORDER)

def _toggle_ts_accordion(self):
    self._ts_acc_open = not self._ts_acc_open
    if self._ts_acc_open:
        self._ts_body.pack(fill="x", padx=12, pady=(0, 12))
        self._ts_accordion.configure(border_color="#2e2e48")
        self.after(60, lambda: self._scroll_to(self._ts_accordion))
    else:
        self._ts_body.pack_forget()
        self._ts_accordion.configure(border_color=BORDER)
```

### 2.2 Default State on Launch

```python
# In _build_ui() after both accordions are built:
self._wm_acc_open = True    # WM open by default
self._ts_acc_open = False   # TS closed by default
# WM body already packed in _build_wm_accordion()
# TS body NOT packed (collapsed)
```

Do not persist accordion state to `core/settings.py` — always reset on launch.

### 2.3 Auto-scroll on Open

```python
# ui/main_window.py
def _scroll_to(self, widget):
    """Scroll CTkScrollableFrame to bring widget into view."""
    try:
        self.middle_frame.update_idletasks()
        canvas = self.middle_frame._parent_canvas
        y  = widget.winfo_y()
        fh = self.middle_frame.winfo_height()
        if fh > 0:
            canvas.yview_moveto(y / fh)
    except Exception:
        pass
```

---

## 3. WM Control Visibility by Mode

```python
# ui/main_window.py
def _on_wm_mode_change_inline(self):
    mode = self.wm_mode.get()
    show_pos   = (mode == "normal")
    show_scale = (mode != "full")

    if show_pos:
        self._wm_pos_label.pack(side="left", padx=(0, 3))
        self._wm_pos_menu.pack(side="left", padx=(0, 4))
    else:
        self._wm_pos_label.pack_forget()
        self._wm_pos_menu.pack_forget()

    if show_scale:
        self._wm_row2.pack(fill="x", pady=(4, 0))
    else:
        self._wm_row2.pack_forget()

    self._update_wm_summary()
```

| Control | Normal | Full | Pattern |
|---|---|---|---|
| Position OptionMenu | ✅ | ❌ | ❌ |
| Scale Row | ✅ | ❌ | ✅ |

---

## 4. Summary String Functions

### WM Summary

```python
# ui/main_window.py
def _wm_summary(self) -> str:
    if not self.wm_enabled.get():
        return t("off")
    mode  = self.wm_mode.get().capitalize()
    fname = os.path.basename(self.watermark_path.get()) or t("no_file")
    op    = f"{self.wm_opacity.get()}% op"
    if self.wm_mode.get() == "full":
        return f"{mode} · {fname} · {op}"
    sc = f"{self.wm_scale.get()}%"
    return f"{mode} · {fname} · {sc} · {op}"

def _update_wm_summary(self):
    if hasattr(self, "_wm_summary_lbl"):
        self._wm_summary_lbl.configure(text=self._wm_summary())
```

Traces (add in `__init__` after var declarations):
```python
for v in [self.wm_enabled, self.wm_mode, self.watermark_path,
          self.wm_scale, self.wm_opacity]:
    v.trace_add("write", lambda *_: self._update_wm_summary())
```

### TS Summary

```python
# ui/main_window.py
def _ts_summary(self) -> str:
    if not self.ts_enabled.get():
        return t("off")
    mode = self.ts_enable.get()
    size = f"{self.ts_font_size.get()}px"
    col  = self.ts_color.get().upper()
    return f"✓ {mode} · {size} · {col}"

def _update_ts_summary(self):
    if hasattr(self, "ts_summary"):
        self.ts_summary.configure(text=self._ts_summary())
```

Traces:
```python
for v in [self.ts_enable, self.ts_font_size, self.ts_color]:
    v.trace_add("write", lambda *_: self._update_ts_summary())
```

---

## 5. Window Scroll Behavior

### Middle Section Setup

```python
# ui/main_window.py — _build_ui()
self.middle_frame = ctk.CTkScrollableFrame(
    self,
    height=484,          # 580 - 44hdr - 52actionbar
    fg_color=BG,
    corner_radius=0,
    scrollbar_button_color=ACCENT,
    scrollbar_button_hover_color="#7d75ff",
)
self.middle_frame.pack(fill="x")
```

- Height: **484px** (580 − 44 − 52)
- Scrollbar: overlay, max 5px, accent color, appears only on overflow
- Canvas and history panel: `pack_propagate(False)` — always 180px fixed

### Height Budget

| Element | Height |
|---|---|
| PanelToggle | 34px |
| Gap | 8px |
| Canvas / History | 180px |
| Gap | 8px |
| WM accordion header | 38px |
| WM accordion body (open) | ~110px |
| Gap | 8px |
| TS accordion header | 38px |
| TS accordion body (open) | ~100px |
| Bottom spacer | 4px |
| **Total (both open)** | **~528px** |

528px > 484px → scrollbar appears. ~44px of scroll needed. Comfortable.

---

## 6. Panel Toggle Implementation

```python
# ui/main_window.py
def _build_panel_toggle(self):
    container = ctk.CTkFrame(self.middle_frame, fg_color=CARD,
                             corner_radius=9, border_width=1,
                             border_color=BORDER)
    container.pack(anchor="w", padx=12, pady=(10, 0))

    self.btn_panel_preview = ctk.CTkButton(
        container, text=f"🖼  {t('preview')}",
        fg_color=ACCENT, hover_color="#7d75ff", text_color="white",
        corner_radius=7, height=28, width=110,
        command=lambda: self._switch_panel("preview"))
    self.btn_panel_preview.pack(side="left", padx=3, pady=3)

    hist_side = ctk.CTkFrame(container, fg_color="transparent")
    hist_side.pack(side="left", padx=(0, 3))

    self.btn_panel_history = ctk.CTkButton(
        hist_side, text=f"🕒  {t('history')}",
        fg_color="transparent", hover_color=CARD2, text_color=MUTED,
        corner_radius=7, height=28, width=110,
        command=lambda: self._switch_panel("history"))
    self.btn_panel_history.pack(side="left")

    self.hist_count_badge = ctk.CTkLabel(
        hist_side, text="", fg_color=ACCENT2, text_color="white",
        corner_radius=10, font=(FONT_MONO, 8), width=0, height=14, padx=5)
    self.hist_count_badge.pack(side="left", padx=(2, 0))

def _switch_panel(self, which: str):
    self._panel_mode = which
    if which == "preview":
        self.history_panel_wrap.pack_forget()
        self.preview_wrap.pack(fill="x", padx=12, pady=(0, 8))
        self.btn_panel_preview.configure(fg_color=ACCENT, text_color="white")
        self.btn_panel_history.configure(fg_color="transparent", text_color=MUTED)
    else:
        self.preview_wrap.pack_forget()
        self.history_panel_wrap.pack(fill="x", padx=12, pady=(0, 8))
        self.btn_panel_history.configure(fg_color=ACCENT, text_color="white")
        self.btn_panel_preview.configure(fg_color="transparent", text_color=MUTED)
        self._render_history_panel()
```

---

## 7. History Panel — New Screenshot Behavior

```python
# ui/main_window.py
def _notify_history_updated(self):
    """Called after _do_screenshot() succeeds.
    Imported from: core/history.py (enqueue), called from ui/main_window.py"""
    # Refresh inline panel if on History view
    if getattr(self, "_panel_mode", "preview") == "history":
        self._render_history_panel()
        # Scroll to leftmost (newest item)
        self.after(50, lambda:
            self.hist_panel_scroll._parent_canvas.xview_moveto(0))
    # Always update badge
    self._update_history_badge()
    # Existing popup refresh — unchanged
    if self._history_popup and self._history_popup.winfo_exists():
        self._history_popup._render()

def _update_history_badge(self):
    with self._history_lock:
        count = len(self._history)
    if count == 0:
        self.hist_count_badge.configure(text="", fg_color="transparent")
    else:
        self.hist_count_badge.configure(text=str(count), fg_color=ACCENT2)
```

---

## 8. Split Shot Buttons

```python
# ui/main_window.py — _build_action_bar()
shot_frame = ctk.CTkFrame(bar, fg_color="transparent", corner_radius=8)
shot_frame.pack(side="right", padx=4, pady=10)

self.btn_fullscreen = ctk.CTkButton(
    shot_frame, text=f"📸 {t('fullscreen')}",
    width=110, height=32, fg_color=ACCENT, hover_color="#7d75ff",
    text_color="white", font=(FONT, 10, "bold"), corner_radius=0,
    command=self._trigger_fullscreen)
self.btn_fullscreen.pack(side="left")

self.btn_region = ctk.CTkButton(
    shot_frame, text=f"✂ {t('region')}",
    width=90, height=32, fg_color="#32324e", hover_color="#404060",
    text_color="white", font=(FONT, 10, "bold"), corner_radius=0,
    command=self._trigger_region)
self.btn_region.pack(side="left")

def _set_shot_buttons(self, enabled: bool):
    state = "normal" if enabled else "disabled"
    self.btn_fullscreen.configure(state=state)
    self.btn_region.configure(state=state)
```

Call `_set_shot_buttons(False)` at `_start_screenshot()` entry.
Call `_set_shot_buttons(True)` in `_do_screenshot()` finally block,
`_on_region_cancelled()`, and `_cancel_countdown()`.

---

## 9. Summary of All Confirmed Behaviors

| Behavior | Value |
|---|---|
| Accordion simultaneous open | ✅ Both open at same time |
| WM default on launch | Open |
| TS default on launch | Collapsed |
| Auto-scroll on accordion open | ✅ |
| Animation | Programmer decides |
| Window size | 620×580, locked |
| Overflow handling | Middle section scrolls (CTkScrollableFrame) |
| Scrollbar | 5px max, overlay only, accent color |
| Canvas height | Fixed 180px, `pack_propagate(False)` |
| History panel height | Fixed 180px, `pack_propagate(False)` |
| History panel config controls | ❌ Config is in accordions only |
| New screenshot on History panel | Stay on History, prepend + flash |
| `ts_format` location | Settings window → Capture card |
| WM summary format | `Mode · filename · scale · opacity op` |
| TS summary format | `✓ ↘ · 22px · #FFFFFF` |
| `CountdownOverlay` / `RegionSelector` | Pure `tk.Toplevel` always |
