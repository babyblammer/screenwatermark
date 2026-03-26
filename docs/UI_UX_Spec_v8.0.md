# ScreenWatermark Pro v8.0 — UI/UX Specification
**Migration: tkinter → customtkinter | Modular Package**
Version: 2.0-SYNCED | Supersedes v1.0

---

## 0. Module Structure (prerequisite — complete before any UI work)

This spec applies to the modular package structure produced by M1–M3.
All UI code lives in `ui/`. All imports follow this dependency rule:

```
core/    ← no UI imports ever
system/  ← no UI imports ever
ui/      ← imports from core/ and system/ freely
```

### Import convention in all ui/ files

```python
# ui/main_window.py — top of file
from core.constants  import BG, PANEL, CARD, CARD2, BORDER, ACCENT, ACCENT2
from core.constants  import SUCCESS, TEXT, MUTED, WARN, PREVIEW_W, PREVIEW_H
from core.settings   import load_settings, save_settings, DEFAULT_SETTINGS
from core.history    import save_history, load_history, _enqueue_save_history
from core.render     import apply_watermark, apply_timestamp
from core.clipboard  import copy_image_to_clipboard
from core.font_cache import load_font
from core.wm_cache   import get_cached_watermark, invalidate_wm_cache
from core.utils      import safe_hex_to_rgb, safe_strftime
from system.hotkeys  import HotkeyManager
from system.tray     import _make_tray_icon, _win_toast
from system.startup  import set_run_at_startup, get_run_at_startup
from i18n            import t
import customtkinter as ctk
import tkinter as tk
```

### Font constants (defined once in `ui/main_window.py`, passed to widgets)

```python
FONT      = "Segoe UI"
FONT_MONO = "Consolas"
```

---

## 1. Overview

### Goals
- Modern dark UI using CTk widgets natively
- WM and TS config inline in main window (accordion components)
- Preview canvas ↔ History toggle replaces Notebook tabs
- Split Fullscreen + Region shot buttons
- Settings window stripped of WM + TS cards
- Localization via `i18n.t()`
- Window size stays **620 × 580 px**, non-resizable

### Non-goals
- No logic changes to any function in `core/` or `system/`
- No new features beyond what is specified here

---

## 2. Technology Stack

| Item | Spec |
|---|---|
| UI framework | `customtkinter >= 5.2.2` |
| Python | 3.10+ |
| OS chrome tinting | `pywinstyles` (Windows) — titlebar `#0a0e1a` |
| Module location | `ui/main_window.py`, `ui/settings_window.py`, etc. |
| Widget components | `ui/widgets/accordion.py`, `panel_toggle.py`, `shot_buttons.py`, `config_rows.py` |

CTk init at top of `main.py`:
```python
import customtkinter as ctk
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")
```

---

## 3. Color Palette

Defined in `core/constants.py`. Import into all `ui/` files via `from core.constants import *`.

```python
BG      = "#0a0a10"
PANEL   = "#111118"
CARD    = "#16161f"
CARD2   = "#1c1c28"
BORDER  = "#252535"
ACCENT  = "#6c63ff"
ACCENT2 = "#ff6584"
SUCCESS = "#43e97b"
TEXT    = "#e2e2f0"
MUTED   = "#5a5a7a"
WARN    = "#f5a623"
```

---

## 4. Typography

| Use | Font | Size | Weight |
|---|---|---|---|
| App title | Segoe UI | 13 | bold |
| Card/accordion headers | Segoe UI | 11 | bold |
| Body / labels | Segoe UI | 10 | normal |
| Monospace (hotkeys, status, meta, summary) | Consolas | 9–10 | normal |
| Button labels | Segoe UI | 10–11 | bold |

---

## 5. Main Window — `ScreenWatermarkApp(ctk.CTk)` in `ui/main_window.py`

### 5.1 Geometry

```python
self.geometry("620x580")
self.minsize(620, 580)
self.maxsize(620, 580)
self.resizable(False, False)
```

### 5.2 Layout Structure

```
┌─────────────────────────────────────────────┐  h=580
│  TitleBar (OS chrome — pywinstyles)         │
├─────────────────────────────────────────────┤
│  HeaderBar                                  │  h≈44
├─────────────────────────────────────────────┤
│  CTkScrollableFrame (middle, h=484)         │
│  ├─ PanelToggle (pill: Preview | History)   │  h≈30
│  ├─ Preview Canvas OR History Panel         │  h=180 (fixed)
│  ├─ WM Accordion (open by default)          │  h≈38–120
│  └─ TS Accordion (closed by default)        │  h≈38–120
├─────────────────────────────────────────────┤
│  ActionBar                                  │  h≈52
└─────────────────────────────────────────────┘
```

Middle height: 580 − 44 − 52 = **484px** (includes 20px padding).
`CTkScrollableFrame` handles overflow — 5px accent scrollbar, overlay only.

### 5.3 HeaderBar

`CTkFrame(fg_color=PANEL, height=44, corner_radius=0)` in `ui/main_window.py`

Left → Right:
- App icon: `CTkLabel(text="📸", font=(FONT, 18))`
- App name: `CTkLabel(text=t("app_title"), font=(FONT, 13, "bold"))`
- WM badge: `CTkLabel` — updated by `_update_wm_indicator()`
- spacer
- History icon: `CTkButton(text="🕒", width=30, height=30)`
- Settings: `CTkButton(text=f"⚙ {t('settings')}", fg_color=ACCENT)`

### 5.4 Panel Toggle (component: `ui/widgets/panel_toggle.py`)

```python
class PanelToggle(ctk.CTkFrame):
    def __init__(self, parent, panels: list[tuple[str, str]], command, **kwargs):
        # panels = [("🖼 Preview", "preview"), ("🕒 History", "history")]
        ...
    def set_active(self, key: str): ...
    def set_badge(self, key: str, count: int): ...
```

- Active segment: `fg_color=ACCENT, text_color="white"`
- Inactive: `fg_color="transparent", text_color=MUTED`
- Badge: `CTkLabel(fg_color=ACCENT2)`, hidden when count = 0

### 5.5 Preview Canvas

`tk.Canvas` (no CTk equivalent — keep as-is) wrapped in `CTkFrame`:

```python
self.preview_wrap = ctk.CTkFrame(
    self.middle_frame, height=180,
    fg_color=CARD, corner_radius=10,
    border_width=1, border_color=BORDER)
self.preview_wrap.pack_propagate(False)   # LOCK height — never shrinks

self.preview_canvas = tk.Canvas(
    self.preview_wrap, width=PREVIEW_W, height=PREVIEW_H,
    bg="#0a0a12", highlightthickness=0)
```

Canvas internals (`_apply_preview`, `_refresh_live_preview`) unchanged from v3.9.1f.

### 5.6 History Panel

```python
self.history_panel_wrap = ctk.CTkFrame(
    self.middle_frame, height=180,
    fg_color=CARD, corner_radius=10,
    border_width=1, border_color=BORDER)
self.history_panel_wrap.pack_propagate(False)   # LOCK height
```

Internal: top bar + horizontal `CTkScrollableFrame` for thumbnails.
Not packed by default — `_switch_panel("history")` packs it and unpacks preview.

### 5.7 WM Accordion (component: `ui/widgets/accordion.py`)

```python
class CTkAccordion(ctk.CTkFrame):
    def __init__(self, parent, title, icon,
                 open_by_default=False, **kwargs): ...
    def set_body(self, frame: ctk.CTkFrame): ...
    def toggle(self): ...
    def set_summary(self, text: str): ...
    def scroll_into_view(self, scroll_canvas): ...
```

WM accordion: `open_by_default=True`
TS accordion: `open_by_default=False`

Both can be open simultaneously. No exclusive-close logic.

**WM body controls (Row 1):** Enable pill | Mode OptionMenu | Position OptionMenu (hidden in Full/Pattern) | Opacity slider
**WM body controls (Row 2):** Scale slider (hidden in Full) | File picker | Filename label | Clear button

**Mode visibility rules:**

| Control | Normal | Full | Pattern |
|---|---|---|---|
| Position OptionMenu | ✅ | ❌ | ❌ |
| Scale slider | ✅ | ❌ | ✅ |

### 5.8 TS Accordion

**TS body controls (Row 1):** Enable pill | Outside pill | Position OptionMenu
**TS body controls (Row 2):** Font size slider | Color swatch | BG swatch | Bold pill | Shadow pill

### 5.9 ActionBar

`CTkFrame(fg_color=PANEL, height=52, corner_radius=0)` packed `side="bottom"`.

Contents: `status_var` label (flex) | Copy button | Split shot buttons

**Split shot component (`ui/widgets/shot_buttons.py`):**

```python
class SplitShotButton(ctk.CTkFrame):
    def __init__(self, parent, on_fullscreen, on_region, **kwargs): ...
    def set_enabled(self, enabled: bool): ...
```

- Fullscreen: `fg_color=ACCENT` | Region: `fg_color="#32324e"`
- Shared `CTkFrame(corner_radius=8)` wrapper for visual join

---

## 6. Settings Window — `SettingsWindow(ctk.CTkToplevel)` in `ui/settings_window.py`

### 6.1 Geometry

```python
self.geometry("480x520")
self.resizable(False, False)
```

### 6.2 Cards Present in v8.0

| Card | Status vs v3.9.1f |
|---|---|
| Startup | ✅ kept |
| Capture (mode + delay + region + ts_format) | ✅ kept + ts_format added here |
| Hotkeys | ✅ kept (display-only) |
| Language | ✅ **new** |
| Watermark | ❌ removed → main window accordion |
| Timestamp | ❌ removed → main window accordion |

### 6.3 Language Card

```python
ctk.CTkOptionMenu(values=["English", "Indonesian"],
                  command=self._on_language_change)
ctk.CTkLabel(text=t("restart_required"))
```

### 6.4 Body Scrollbar

`CTkScrollableFrame` with `scrollbar_button_color=ACCENT`. 5px max width.

### 6.5 Footer

```
[ Credits ]  |  [ ↺ Reset to Default ]  ────  [ Close ]
```

---

## 7. Removed from SettingsWindow

Delete from `ui/settings_window.py`:

- `_build_watermark_card()` — delete entirely
- `_build_timestamp_card()` — delete entirely
- All `wm_*` and `ts_*` var traces inside SettingsWindow
- `wm_status_lbl` in header
- `_refresh_wm_status_lbl()`, `_on_wm_path_changed()`, `_on_wm_toggle()`, `_update_wm_controls_state()`, `_on_wm_mode_change()`

`ts_format` entry moves to the Capture card in Settings.

---

## 8. Overlays — `ui/overlays.py`

`CountdownOverlay` and `RegionSelector` are **never migrated to CTk**.
They use `overrideredirect(True)` which requires pure `tk.Toplevel`.

```python
# ui/overlays.py — imports
import tkinter as tk  # pure tkinter only
from core.constants import ACCENT, TEXT, MUTED
```

No `customtkinter` import in `ui/overlays.py` ever.

---

## 9. Localization

All hardcoded UI strings replaced with `t("key")` from `i18n.py`.
Language loaded from `core/settings.py` → `DEFAULT_SETTINGS["language"]` on startup.

```python
# main.py
from core.settings import load_settings
import i18n
cfg = load_settings()
i18n.set_language(cfg.get("language", "en"))
```

---

## 10. CTk Widget Mapping

| tkinter | customtkinter | Notes |
|---|---|---|
| `tk.Tk` | `ctk.CTk` | |
| `tk.Toplevel` | `ctk.CTkToplevel` | Except overlays — keep `tk.Toplevel` |
| `tk.Frame(bg=X)` | `ctk.CTkFrame(fg_color=X)` | |
| `tk.Label(bg=X, fg=Y)` | `ctk.CTkLabel(fg_color=X, text_color=Y)` | |
| `tk.Button` | `ctk.CTkButton` | |
| `tk.Checkbutton` | `ctk.CTkCheckBox` | |
| `tk.Radiobutton` | `ctk.CTkRadioButton` | |
| `ttk.Scale` | `ctk.CTkSlider` | |
| `ttk.Notebook` | Removed — `PanelToggle` component | |
| `tk.Entry` | `ctk.CTkEntry` | |
| `tk.Canvas` | **Keep as `tk.Canvas`** | Wrapped in `CTkFrame` border |
| `ttk.Scrollbar` | Built into `CTkScrollableFrame` | |

**Tkinter vars stay as-is.** `tk.StringVar`, `tk.IntVar`, `tk.BooleanVar` accepted
by CTk widgets via `variable=` kwarg — no change needed.

---

## 11. Window Sizing

Both accordions open: ~536px total content vs 464px available → ~72px scroll.
Scrollbar appears cleanly at this point. Canvas stays 180px fixed.

---

## 12. Constraints Checklist

Logic protection — these functions in `core/` and `system/` are never modified:

- [ ] `core/render.py` — `apply_watermark()`, `apply_timestamp()`
- [ ] `core/history.py` — `save_history()`, `load_history()`, IO queue
- [ ] `core/settings.py` — `load_settings()`, `save_settings()`
- [ ] `core/clipboard.py` — `copy_image_to_clipboard()`
- [ ] `core/wm_cache.py` — all cache functions
- [ ] `system/hotkeys.py` — `HotkeyManager`, `HotkeyRecorder`
- [ ] `system/ipc.py` — single-instance guard
- [ ] `ui/overlays.py` — `CountdownOverlay`, `RegionSelector` (no CTk ever)
- [ ] All `tk.StringVar` / `tk.IntVar` / `tk.BooleanVar` — unchanged
- [ ] `_refresh_snapshot()`, `_on_setting_changed()`, `_do_autosave()` — unchanged
- [ ] `_do_screenshot()`, `_start_screenshot()`, `_countdown()` — unchanged
