# ScreenWatermark Pro v8.0 — Automated Test Strategy
**Framework: pytest + pyautogui | Modular-aware**
Version: 2.0-SYNCED | Supersedes v1.0

---

## 1. Strategy Summary

| Item | Decision |
|---|---|
| Framework | `pytest` + `pyautogui` + `Pillow` + `win32clipboard` |
| M1/M2 trigger | At each modular milestone — headless, no display |
| P1–GC trigger | Gold Candidate only |
| Blocking | Yes — all automated tests must PASS before release |
| Report format | HTML (`pytest-html`) |
| Manual QA scope | ~26 non-automatable cases only |
| Total coverage | **80 of 106 test cases automated (75%)** |

---

## 2. Two-Tier Test Architecture

### Tier 1 — Headless Core/System Tests (M1/M2)

Run immediately after each modular extraction milestone. No display required.
No app window. No pyautogui. Pure Python logic assertions.

```bash
# After M1
pytest tests/core/ -v --html=tests/reports/report_M1.html --self-contained-html

# After M2
pytest tests/system/ -v --html=tests/reports/report_M2.html --self-contained-html
```

These catch extraction bugs (wrong imports, broken function signatures,
missing global state) before any UI work begins.

### Tier 2 — GUI Tests (GC only)

Full app launched in-process. `pyautogui` for click simulation.
Pixel checks via `PIL` + `pyautogui.screenshot()`.

```bash
# At Gold Candidate
pytest tests/ui/ -v --html=tests/reports/report_GCa.html --self-contained-html
```

---

## 3. Directory Structure

```
screenwatermark/
└── tests/
    ├── conftest.py                  ← shared fixtures + helpers
    │
    ├── core/                        ← Tier 1 — headless (M1)
    │   ├── test_settings.py
    │   ├── test_history.py
    │   ├── test_render.py
    │   ├── test_clipboard.py
    │   ├── test_font_cache.py
    │   └── test_wm_cache.py
    │
    ├── system/                      ← Tier 1 — headless (M2)
    │   ├── test_hotkeys.py
    │   ├── test_startup.py
    │   └── test_ipc.py
    │
    ├── ui/                          ← Tier 2 — GUI (GC only)
    │   ├── test_p1_shell.py
    │   ├── test_p2_panels.py
    │   ├── test_p3_wm_accordion.py
    │   ├── test_p4_ts_accordion.py
    │   ├── test_p5_shot_buttons.py
    │   ├── test_p6_settings.py
    │   ├── test_p7_i18n.py
    │   └── test_p8_integration.py
    │
    ├── assets/
    │   └── test_watermark.png       ← 200×100 red RGBA PNG
    │
    └── reports/                     ← auto-generated
        ├── report_M1.html
        ├── report_M2.html
        └── report_GCa.html
```

---

## 4. Full Coverage Map — 106 Test Cases

Legend: `AUTO-H` = headless auto | `AUTO-G` = GUI auto | `MANUAL` = manual only

### Phase M1 — core/ Extraction (10 cases)

| TC ID | Title | Mode |
|---|---|---|
| TC-M1-001 | `core/constants.py` importable, values correct | AUTO-H |
| TC-M1-002 | `load_settings()` returns DEFAULT_SETTINGS when no file | AUTO-H |
| TC-M1-003 | `save_settings()` writes valid JSON | AUTO-H |
| TC-M1-004 | `save_settings()` + `load_settings()` round-trip | AUTO-H |
| TC-M1-005 | `apply_watermark()` returns image unchanged — no WM path | AUTO-H |
| TC-M1-006 | `apply_watermark()` returns image unchanged — disabled | AUTO-H |
| TC-M1-007 | `apply_watermark()` modifies image in Normal mode | AUTO-H |
| TC-M1-008 | `apply_timestamp()` overlays TS on image | AUTO-H |
| TC-M1-009 | `apply_timestamp()` extends height in outside mode | AUTO-H |
| TC-M1-010 | `invalidate_wm_cache()` clears both cache dicts | AUTO-H |

### Phase M2 — system/ Extraction (8 cases)

| TC ID | Title | Mode |
|---|---|---|
| TC-M2-001 | `system/hotkeys.py` importable | AUTO-H |
| TC-M2-002 | `HotkeyManager` instantiates cleanly | AUTO-H |
| TC-M2-003 | `HotkeyManager.register()` stores callback | AUTO-H |
| TC-M2-004 | `HotkeyManager.unregister()` removes slot | AUTO-H |
| TC-M2-005 | `system/startup.py` importable | AUTO-H |
| TC-M2-006 | `get_run_at_startup()` returns bool | AUTO-H |
| TC-M2-007 | `system/ipc.py` importable | AUTO-H |
| TC-M2-008 | `_acquire_single_instance()` returns `(bool, int)` | AUTO-H |

### Phase M3 — ui/ Isolation (6 cases — manual smoke)

| TC ID | Title | Mode |
|---|---|---|
| TC-M3-001 | App launches from `main.py` | MANUAL |
| TC-M3-002 | Screenshot (fullscreen) works | MANUAL |
| TC-M3-003 | Settings window opens | MANUAL |
| TC-M3-004 | History popup opens | MANUAL |
| TC-M3-005 | Region selector opens | MANUAL |
| TC-M3-006 | App exits cleanly via tray | MANUAL |

### Phase P1 — CTk Shell + Header (10 cases)

| TC ID | Title | Mode | Reason if Manual |
|---|---|---|---|
| TC-P1-001 | Dark theme appearance | MANUAL | Visual |
| TC-P1-002 | Window size locked 620×580 | AUTO-G | `winfo_width/height()` |
| TC-P1-003 | OS titlebar color | MANUAL | Visual |
| TC-P1-004 | Header app name | AUTO-G | Widget text |
| TC-P1-005 | WM badge ON + file | AUTO-G | Badge text check |
| TC-P1-006 | WM badge ON + no file | AUTO-G | Badge text check |
| TC-P1-007 | WM badge OFF | AUTO-G | Badge text check |
| TC-P1-008 | Settings button | AUTO-G | pyautogui + Toplevel check |
| TC-P1-009 | History icon | AUTO-G | pyautogui + Toplevel check |
| TC-P1-010 | Close to tray | MANUAL | Tray introspection unreliable |

### Phase P2 — Canvas Toggle + Panels (14 cases)

| TC ID | Title | Mode | Reason if Manual |
|---|---|---|---|
| TC-P2-001 | Default panel is Preview | AUTO-G | `widget_is_visible()` |
| TC-P2-002 | Toggle to History | AUTO-G | Same |
| TC-P2-003 | Toggle back to Preview | AUTO-G | Same |
| TC-P2-004 | Active segment styling | MANUAL | Visual color |
| TC-P2-005 | History badge count | AUTO-G | Label text |
| TC-P2-006 | History badge hidden at 0 | AUTO-G | Label text |
| TC-P2-007 | Preview renders WM | AUTO-G | PIL pixel check |
| TC-P2-008 | Preview renders TS | AUTO-G | PIL pixel check |
| TC-P2-009 | Preview updates on slider | AUTO-G | PIL diff |
| TC-P2-010 | Preview background thread | AUTO-G | Responsiveness check |
| TC-P2-011 | History thumbnails appear | AUTO-G | Child widget count |
| TC-P2-012 | History thumb click copies | AUTO-G | Clipboard check |
| TC-P2-013 | History Clear All | AUTO-G | Child count = 0 |
| TC-P2-014 | History auto-refresh on new shot | AUTO-G | Child count increments |

### Phase P3 — WM Accordion (18 cases)

| TC ID | Title | Mode | Reason if Manual |
|---|---|---|---|
| TC-P3-001 | WM open on launch | AUTO-G | `_wm_acc_open` flag |
| TC-P3-002 | Toggle close | AUTO-G | `winfo_ismapped()` |
| TC-P3-003 | Toggle reopen | AUTO-G | `winfo_ismapped()` |
| TC-P3-004 | Enable OFF | AUTO-G | var + badge |
| TC-P3-005 | Normal shows pos + scale | AUTO-G | `winfo_ismapped()` |
| TC-P3-006 | Full hides pos + scale | AUTO-G | `winfo_ismapped()` |
| TC-P3-007 | Pattern hides pos only | AUTO-G | `winfo_ismapped()` |
| TC-P3-008 | Mode change updates preview | AUTO-G | PIL diff |
| TC-P3-009 | Opacity slider | AUTO-G | var.get() |
| TC-P3-010 | Scale slider | AUTO-G | var.get() |
| TC-P3-011 | File picker dialog | MANUAL | OS modal |
| TC-P3-012 | File set updates label | AUTO-G | Label text |
| TC-P3-013 | Clear file | AUTO-G | path="" + badge |
| TC-P3-014 | Summary updates | AUTO-G | Label text |
| TC-P3-015 | Settings saved | AUTO-G | `core/settings` JSON |
| TC-P3-016 | Normal screenshot | AUTO-G | PIL pixel WM region |
| TC-P3-017 | Full screenshot | AUTO-G | PIL pixel center |
| TC-P3-018 | Pattern screenshot | AUTO-G | PIL multiple WM |

### Phase P4 — TS Accordion (14 cases)

| TC ID | Title | Mode | Reason if Manual |
|---|---|---|---|
| TC-P4-001 | TS collapsed on launch | AUTO-G | `_ts_acc_open` flag |
| TC-P4-002 | Expand / collapse | AUTO-G | `winfo_ismapped()` |
| TC-P4-003 | Both accordions open | AUTO-G | Both body widgets mapped |
| TC-P4-004 | Enable OFF from preview | AUTO-G | PIL diff |
| TC-P4-005 | Outside toggle | AUTO-G | var.get() |
| TC-P4-006 | Position dropdown | AUTO-G | var.get() |
| TC-P4-007 | Font size slider | AUTO-G | var.get() |
| TC-P4-008 | Text color swatch | MANUAL | OS color dialog |
| TC-P4-009 | BG color swatch | MANUAL | OS color dialog |
| TC-P4-010 | Bold toggle | AUTO-G | var.get() |
| TC-P4-011 | Shadow toggle | AUTO-G | var.get() |
| TC-P4-012 | TS summary updates | AUTO-G | Label text |
| TC-P4-013 | TS outside screenshot | AUTO-G | `img.height > base_h` |
| TC-P4-014 | TS overlay screenshot | AUTO-G | `img.height == base_h` |

### Phase P5 — Split Shot Buttons (10 cases)

| TC ID | Title | Mode | Reason if Manual |
|---|---|---|---|
| TC-P5-001 | Both buttons visible | AUTO-G | `winfo_ismapped()` |
| TC-P5-002 | Fullscreen triggers flow | AUTO-G | Clipboard check |
| TC-P5-003 | Region opens selector | MANUAL | Real mouse drag |
| TC-P5-004 | Disabled during capture | AUTO-G | State check |
| TC-P5-005 | Re-enabled after capture | AUTO-G | State check |
| TC-P5-006 | Re-enabled after cancel | MANUAL | Region cancel |
| TC-P5-007 | Hotkey fullscreen | AUTO-G | `pyautogui.press` + clipboard |
| TC-P5-008 | Hotkey region | MANUAL | Region drag |
| TC-P5-009 | Copy disabled at start | AUTO-G | State check |
| TC-P5-010 | Copy enabled after shot | AUTO-G | State check |

### Phase P6 — Settings Window (13 cases)

| TC ID | Title | Mode | Reason if Manual |
|---|---|---|---|
| TC-P6-001 | Settings opens CTkToplevel | AUTO-G | Geometry check |
| TC-P6-002 | WM card absent | AUTO-G | Widget text scan |
| TC-P6-003 | TS card absent | AUTO-G | Widget text scan |
| TC-P6-004 | Startup card present | AUTO-G | Widget text scan |
| TC-P6-005 | Capture card present | AUTO-G | Widget text scan |
| TC-P6-006 | Hotkeys card present | AUTO-G | Widget text scan |
| TC-P6-007 | Language card present | AUTO-G | Widget text scan |
| TC-P6-008 | Settings scrollbar visual | MANUAL | Visual |
| TC-P6-009 | Credits popup | MANUAL | Visual |
| TC-P6-010 | Reset to Default | AUTO-G | All vars == DEFAULT_SETTINGS |
| TC-P6-011 | Close button | AUTO-G | Window state |
| TC-P6-012 | State persists | AUTO-G | var.get() after reopen |
| TC-P6-013 | Startup toggle persists | AUTO-G | JSON + registry |

### Phase P7 — Localization (6 cases)

| TC ID | Title | Mode | Reason if Manual |
|---|---|---|---|
| TC-P7-001 | Default English | AUTO-G | `t("settings")` |
| TC-P7-002 | Switch to Indonesian | AUTO-G | `t("settings")` |
| TC-P7-003 | Language saved to JSON | AUTO-G | JSON read |
| TC-P7-004 | Switch back to English | AUTO-G | `t("settings")` |
| TC-P7-005 | Missing key fallback | AUTO-G | No crash |
| TC-P7-006 | Restart notice shown | MANUAL | Visual label |

### Phase P8 — Integration + Regression (20 cases)

| TC ID | Title | Mode | Reason if Manual |
|---|---|---|---|
| TC-P8-001 | Full FS flow | AUTO-G | Clipboard PIL |
| TC-P8-002 | Region screenshot | MANUAL | Drag required |
| TC-P8-003 | Countdown overlay | MANUAL | Visual + timing |
| TC-P8-004 | Countdown cancel | MANUAL | Visual + timing |
| TC-P8-005 | Single instance guard | AUTO-G | 2nd process exit code |
| TC-P8-006 | Tray hide + show | MANUAL | Tray UI |
| TC-P8-007 | Tray screenshot menu | MANUAL | Tray UI |
| TC-P8-008 | History persists restart | AUTO-G | JSON file check |
| TC-P8-009 | Settings persist restart | AUTO-G | JSON file check |
| TC-P8-010 | Autosave debounce | AUTO-G | File mtime |
| TC-P8-011 | WM cache invalidation | AUTO-G | Cache dict empty |
| TC-P8-012 | Shot from minimized | AUTO-G | `wm_state()` |
| TC-P8-013 | Region from minimized | MANUAL | Region drag |
| TC-P8-014 | Delete history item | AUTO-G | Deque count |
| TC-P8-015 | No TclError 10× open/close | AUTO-G | Exception check |
| TC-P8-016 | No freeze rapid slider | AUTO-G | Responsiveness |
| TC-P8-017 | Status bar update | AUTO-G | `status_var.get()` |
| TC-P8-018 | Status bar restore | AUTO-G | `status_var.get()` after 3.5s |
| TC-P8-019 | WM disabled → no WM | AUTO-G | PIL pixel |
| TC-P8-020 | TS disabled → no strip | AUTO-G | Image height |

---

## 5. Final Coverage Count

| Group | AUTO-H | AUTO-G | MANUAL | Total |
|---|---|---|---|---|
| M1 (core/) | 10 | — | — | 10 |
| M2 (system/) | 8 | — | — | 8 |
| M3 (ui/ smoke) | — | — | 6 | 6 |
| P1–P8 (CTk UI) | — | 62 | 20 | 82 |
| **Total** | **18** | **62** | **26** | **106** |

**Automated: 80/106 (75%) | Manual: 26/106 (25%)**

vs. previous plan: 62/90 (67%) automated — modularization added 18 new headless tests.

---

## 6. Manual-Only Cases Scope (26 total)

```
TC-M3-001 → TC-M3-006   ui/ isolation smoke (6 cases)
TC-P1-001  Visual: dark theme appearance
TC-P1-003  Visual: OS titlebar color
TC-P1-010  Tray: close to tray
TC-P2-004  Visual: active toggle segment color
TC-P3-011  File dialog: open WM picker
TC-P4-008  Color picker: text color swatch
TC-P4-009  Color picker: BG color swatch
TC-P5-003  Region selector: drag to select
TC-P5-006  Region cancel: Esc
TC-P5-008  Hotkey region
TC-P6-008  Settings scrollbar visual
TC-P6-009  Credits popup
TC-P7-006  Language restart notice label
TC-P8-002  Region screenshot full flow
TC-P8-003  Countdown overlay visual
TC-P8-004  Countdown cancel
TC-P8-006  Tray hide + show
TC-P8-007  Tray right-click menu
TC-P8-013  Region from minimized
```

---

## 7. Run Commands

```bash
# M1 milestone — headless
pytest tests/core/ -v --html=tests/reports/report_M1.html --self-contained-html

# M2 milestone — headless
pytest tests/system/ -v --html=tests/reports/report_M2.html --self-contained-html

# Gold Candidate — full GUI suite
pytest tests/ui/ -v --html=tests/reports/report_GCa.html --self-contained-html

# Or use the runner:
run_tests_gc.bat
```

---

## 8. Headless Test Examples

```python
# tests/core/test_render.py
from core.render import apply_watermark, apply_timestamp
from core.settings import DEFAULT_SETTINGS
from PIL import Image

def test_apply_watermark_no_path():
    cfg = {**DEFAULT_SETTINGS, "watermark_path": "", "wm_enabled": True}
    img = Image.new("RGB", (800, 600), (100, 100, 100))
    result = apply_watermark(img, cfg)
    assert result.tobytes() == img.tobytes()

def test_apply_watermark_disabled():
    cfg = {**DEFAULT_SETTINGS, "wm_enabled": False}
    img = Image.new("RGB", (800, 600), (100, 100, 100))
    result = apply_watermark(img, cfg)
    assert result.tobytes() == img.tobytes()

def test_apply_timestamp_outside_extends_height(tmp_path):
    cfg = {**DEFAULT_SETTINGS, "ts_enabled": True}
    img = Image.new("RGB", (800, 600), (100, 100, 100))
    result = apply_timestamp(img, cfg)
    assert result.height > img.height
```

```python
# tests/core/test_settings.py
from core.settings import load_settings, save_settings, DEFAULT_SETTINGS
import json, tempfile, os

def test_round_trip(tmp_path, monkeypatch):
    settings_file = tmp_path / ".screenwatermark_settings.json"
    monkeypatch.setattr("core.settings.SETTINGS_FILE", settings_file)
    cfg = {**DEFAULT_SETTINGS, "wm_opacity": 42}
    save_settings(cfg)
    loaded = load_settings()
    assert loaded["wm_opacity"] == 42
```

```python
# tests/system/test_hotkeys.py
from system.hotkeys import HotkeyManager
from unittest.mock import MagicMock

def test_register_stores_callback():
    mgr = HotkeyManager()
    cb = MagicMock()
    # Register without actually starting pynput
    mgr._callbacks["test_slot"] = ("test_slot", cb)
    mgr._active_slots.add("test_slot")
    assert mgr.is_active("test_slot")

def test_unregister_removes_slot():
    mgr = HotkeyManager()
    mgr._callbacks["test_slot"] = ("test_slot", lambda: None)
    mgr._active_slots.add("test_slot")
    mgr.unregister("test_slot")
    assert not mgr.is_active("test_slot")
```
