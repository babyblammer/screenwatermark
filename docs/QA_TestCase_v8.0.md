# ScreenWatermark Pro v8.0 — QA Test Case Document
**Migration Phase: tkinter → customtkinter | Modular + CTk**
Version: 2.0-SYNCED | Format: versioned tracker | Next Bug ID: B-030

---

## Test Case Naming Convention

`TC-[PHASE]-[###]`

Phases:
- M1 — core/ extraction verification
- M2 — system/ extraction verification
- M3 — ui/ class isolation smoke
- P1 — CTk shell + header
- P2 — Canvas toggle + preview + history panel
- P3 — WM accordion
- P4 — TS accordion
- P5 — Split shot buttons
- P6 — Settings window stripped
- P7 — Localization
- P8 — Integration + regression

Automation trigger:
- M1/M2 tests: run at milestone (headless, no display)
- M3 tests: manual smoke
- P1–P8 tests: run at Gold Candidate

Status: `PASS` | `FAIL` | `SKIP` | `BLOCKED` | `PENDING`

---

## Phase M1 — core/ Extraction Verification (Headless)

> These run headlessly via `pytest tests/core/` immediately after M1 is complete.
> No app window required.

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-M1-001 | `core/constants.py` importable | `from core.constants import BG, ACCENT` | No ImportError; values match original | PENDING | |
| TC-M1-002 | `load_settings()` returns dict with all keys | Call `load_settings()` with no settings file | Returns `DEFAULT_SETTINGS` copy | PENDING | |
| TC-M1-003 | `save_settings()` writes valid JSON | Call `save_settings(DEFAULT_SETTINGS)` | File exists, `json.load()` succeeds | PENDING | |
| TC-M1-004 | `save_settings()` + `load_settings()` round-trip | Save then load | Loaded dict equals saved dict | PENDING | |
| TC-M1-005 | `apply_watermark()` returns image unchanged when no WM path | Call with empty `watermark_path` | Returns original image unmodified | PENDING | |
| TC-M1-006 | `apply_watermark()` returns image unchanged when disabled | Call with `wm_enabled=False` | Returns original image unmodified | PENDING | |
| TC-M1-007 | `apply_watermark()` modifies image in Normal mode | Call with valid WM file | Returned image differs from input | PENDING | |
| TC-M1-008 | `apply_timestamp()` overlays TS on image | Call with `ts_enabled=True` | Returned image differs from input | PENDING | |
| TC-M1-009 | `apply_timestamp()` extends image height in outside mode | Call with `ts_outside_canvas=True` | `result.height > input.height` | PENDING | |
| TC-M1-010 | `invalidate_wm_cache()` clears both caches | Load WM, then invalidate | `_wm_cache` and `_wm_resize_cache` both empty | PENDING | |

---

## Phase M2 — system/ Extraction Verification (Headless)

> Run via `pytest tests/system/` at M2 milestone. Pynput mocked where needed.

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-M2-001 | `system/hotkeys.py` importable | `from system.hotkeys import HotkeyManager` | No ImportError | PENDING | |
| TC-M2-002 | `HotkeyManager` instantiates | `mgr = HotkeyManager()` | No error, `mgr._callbacks == {}` | PENDING | |
| TC-M2-003 | `HotkeyManager.register()` stores callback | Register a slot | `mgr._callbacks` has the slot | PENDING | |
| TC-M2-004 | `HotkeyManager.unregister()` removes slot | Register then unregister | Slot absent from `_callbacks` | PENDING | |
| TC-M2-005 | `system/startup.py` importable | `from system.startup import get_run_at_startup` | No ImportError | PENDING | |
| TC-M2-006 | `get_run_at_startup()` returns bool | Call `get_run_at_startup()` | Returns `True` or `False`, no crash | PENDING | |
| TC-M2-007 | `system/ipc.py` importable | `from system.ipc import _acquire_single_instance` | No ImportError | PENDING | |
| TC-M2-008 | `_acquire_single_instance()` returns tuple | Call function | Returns `(bool, int)` | PENDING | |

---

## Phase M3 — ui/ Class Isolation Smoke

> Manual verification only. Run app via `python main.py` after M3.

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-M3-001 | App launches from `main.py` | `python main.py` | Window appears, no import errors | PENDING | |
| TC-M3-002 | Screenshot (fullscreen) works | Press Print Screen | Image in clipboard, history updated | PENDING | |
| TC-M3-003 | Settings window opens | Click Settings button | SettingsWindow CTkToplevel appears | PENDING | |
| TC-M3-004 | History popup opens | Press Ctrl+F9 | HistoryPopup appears with thumbnails | PENDING | |
| TC-M3-005 | Region selector opens | Press Ctrl+Shift+F9 | RegionSelector overlay appears | PENDING | |
| TC-M3-006 | App exits cleanly via tray | Tray → Keluar | Process terminates, no crash | PENDING | |

---

## Phase P1 — CTk Shell, Titlebar, Header (10 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P1-001 | App launches with CTk dark theme | Run app | Dark bg `#0a0a10`, no white flash | PENDING | Manual |
| TC-P1-002 | Window size locked 620×580 | Launch, try resize | Window stays 620×580 | PENDING | Auto |
| TC-P1-003 | OS titlebar color | Windows only | Titlebar dark slate via pywinstyles | PENDING | Manual |
| TC-P1-004 | Header app name visible | Launch | "ScreenWatermark Pro" in header | PENDING | Auto |
| TC-P1-005 | WM badge ON + file | Enable WM, set file | Badge "WM ✓" SUCCESS green | PENDING | Auto |
| TC-P1-006 | WM badge ON + no file | Enable WM, clear file | Badge "WM ⚠" WARN yellow | PENDING | Auto |
| TC-P1-007 | WM badge OFF | Disable WM | Badge "WM OFF" muted | PENDING | Auto |
| TC-P1-008 | Settings button opens window | Click ⚙ Settings | Settings CTkToplevel opens | PENDING | Auto |
| TC-P1-009 | History icon opens popup | Click 🕒 | HistoryPopup opens | PENDING | Auto |
| TC-P1-010 | App closes to tray | Click X | Window withdraws, tray icon remains | PENDING | Manual |

---

## Phase P2 — Canvas Toggle + Preview + History Panel (14 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P2-001 | Default panel is Preview | Launch | Preview visible, history hidden | PENDING | Auto |
| TC-P2-002 | Toggle to History | Click History segment | History panel visible, preview hidden | PENDING | Auto |
| TC-P2-003 | Toggle back to Preview | Click Preview | Preview visible, history hidden | PENDING | Auto |
| TC-P2-004 | Active segment styling | Toggle each | Active = ACCENT fill, inactive = muted | PENDING | Manual |
| TC-P2-005 | History badge count | Have 3 items | Badge shows "3" | PENDING | Auto |
| TC-P2-006 | History badge hidden at 0 | Clear history | Badge hidden/empty | PENDING | Auto |
| TC-P2-007 | Preview renders watermark | Set WM file | WM visible in canvas | PENDING | Auto |
| TC-P2-008 | Preview renders timestamp | Enable TS | TS text visible in canvas | PENDING | Auto |
| TC-P2-009 | Preview updates on slider | Move opacity slider | Canvas re-renders within 500ms | PENDING | Auto |
| TC-P2-010 | Preview background thread | Rapid slider moves | UI stays responsive | PENDING | Auto |
| TC-P2-011 | History thumbnails appear | Take 3 screenshots | 3 thumbs in history panel | PENDING | Auto |
| TC-P2-012 | History thumb click copies | Click a thumbnail | Image in clipboard | PENDING | Auto |
| TC-P2-013 | History Clear All | Click 🗑 Clear All | All thumbs removed | PENDING | Auto |
| TC-P2-014 | History panel auto-refresh | On History, take screenshot via hotkey | New thumb prepended, stays on History | PENDING | Auto |

---

## Phase P3 — Watermark Accordion (18 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P3-001 | WM accordion open on launch | Launch | WM body visible by default | PENDING | Auto |
| TC-P3-002 | Click header expands | Click header when closed | Body appears | PENDING | Auto |
| TC-P3-003 | Click header collapses | Click header when open | Body hidden | PENDING | Auto |
| TC-P3-004 | Enable OFF sets var + badge | Toggle OFF | `wm_enabled=False`, badge "WM OFF" | PENDING | Auto |
| TC-P3-005 | Normal mode shows pos + scale | Select Normal | Position row + Scale row visible | PENDING | Auto |
| TC-P3-006 | Full mode hides pos + scale | Select Full | Both rows hidden | PENDING | Auto |
| TC-P3-007 | Pattern hides pos only | Select Pattern | Position hidden, scale visible | PENDING | Auto |
| TC-P3-008 | Mode change updates preview | Switch mode | Canvas re-renders | PENDING | Auto |
| TC-P3-009 | Opacity slider range | Drag 0–100 | `wm_opacity.get()` matches slider | PENDING | Auto |
| TC-P3-010 | Scale slider range | Drag 5–60 | `wm_scale.get()` matches slider | PENDING | Auto |
| TC-P3-011 | Choose file opens dialog | Click Choose… | OS file picker opens | PENDING | Manual |
| TC-P3-012 | File selected updates label | `watermark_path.set(path)` | Filename label shows basename | PENDING | Auto |
| TC-P3-013 | Clear file ✕ resets path | Click ✕ | `watermark_path=""`, badge → WM ⚠ | PENDING | Auto |
| TC-P3-014 | Summary string updates | Change mode/opacity | Header summary reflects values | PENDING | Auto |
| TC-P3-015 | Settings saved on change | Change opacity, wait 900ms | `core/settings` JSON updated | PENDING | Auto |
| TC-P3-016 | WM Normal screenshot result | Normal mode, take FS shot | WM in correct position in image | PENDING | Auto |
| TC-P3-017 | WM Full screenshot result | Full mode, take shot | WM fills/covers screenshot | PENDING | Auto |
| TC-P3-018 | WM Pattern screenshot result | Pattern mode, take shot | WM tiled across screenshot | PENDING | Auto |

---

## Phase P4 — Timestamp Accordion (14 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P4-001 | TS card frame on launch | Launch | TS card visible with summary | PENDING | Auto |
| TC-P4-002 | Enable dropdown Off | Select "Off" | Controls disabled, summary "Off" | PENDING | Auto |
| TC-P4-003 | Enable dropdown Outside | Select "Outside" | Controls enabled, summary shows mode | PENDING | Auto |
| TC-P4-004 | Font size slider 10–60 | Drag slider | `ts_font_size.get()` matches, label updates | PENDING | Auto |
| TC-P4-005 | Text color swatch | Click swatch | OS color picker opens | PENDING | Manual |
| TC-P4-006 | TS controls disabled when Off | Select "Off" | Font slider, color btn disabled | PENDING | Auto |
| TC-P4-007 | TS screenshot outside mode | Outside ON, take shot | Image height > screen height | PENDING | Auto |
| TC-P4-008 | TS screenshot off mode | Off ON, take shot | No timestamp strip added | PENDING | Auto |

---

## Phase P5 — Split Shot Buttons (10 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P5-001 | Both buttons always visible | Launch | Fullscreen + Region buttons in action bar | PENDING | Auto |
| TC-P5-002 | Fullscreen button triggers flow | Click 📸 Fullscreen | App withdraws, screenshot taken | PENDING | Auto |
| TC-P5-003 | Region button opens selector | Click ✂ Region | RegionSelector overlay appears | PENDING | Manual |
| TC-P5-004 | Buttons disabled during capture | During capture | Both `state="disabled"` | PENDING | Auto |
| TC-P5-005 | Buttons re-enabled after capture | After capture | Both `state="normal"` | PENDING | Auto |
| TC-P5-006 | Buttons re-enabled after cancel | Cancel region | Both `state="normal"` | PENDING | Manual |
| TC-P5-007 | Hotkey fullscreen = button | Press Print Screen | Same result as Fullscreen button | PENDING | Auto |
| TC-P5-008 | Hotkey region | Press Ctrl+Shift+F9 | Region selector opens | PENDING | Manual |
| TC-P5-009 | Copy button disabled at start | Launch, no screenshots | Copy `state="disabled"` | PENDING | Auto |
| TC-P5-010 | Copy button enables after shot | Take screenshot | Copy `state="normal"` | PENDING | Auto |

---

## Phase P6 — Settings Window Stripped (13 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P6-001 | Settings opens as CTkToplevel | Click Settings | CTkToplevel at 480×520 | PENDING | Auto |
| TC-P6-002 | WM card absent | Open Settings, scan | No "Watermark" section | PENDING | Auto |
| TC-P6-003 | TS card absent | Open Settings, scan | No "Timestamp" section | PENDING | Auto |
| TC-P6-004 | Startup card present | Open Settings | Startup checkboxes visible | PENDING | Auto |
| TC-P6-005 | Capture card present | Open Settings | Mode + delay + region visible | PENDING | Auto |
| TC-P6-006 | Hotkeys card present | Open Settings | 3 hotkey pills visible | PENDING | Auto |
| TC-P6-007 | Language card present | Open Settings | Language dropdown visible | PENDING | Auto |
| TC-P6-008 | Settings body scrollable | Expand content | 5px accent scrollbar on overflow | PENDING | Manual |
| TC-P6-009 | Credits popup | Click Credits | Credits popup opens | PENDING | Manual |
| TC-P6-010 | Reset to Default | Click Reset, confirm | All vars reset to `DEFAULT_SETTINGS` | PENDING | Auto |
| TC-P6-011 | Close button | Click Close | Window withdraws | PENDING | Auto |
| TC-P6-012 | Settings state persists | Change mode, close, reopen | Mode persists | PENDING | Auto |
| TC-P6-013 | Startup toggle persists | Toggle startup on | JSON + registry reflect change | PENDING | Auto |

---

## Phase P7 — Localization (6 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P7-001 | Default language English | Fresh install | `t("settings")=="Settings"` | PENDING | Auto |
| TC-P7-002 | Switch to Indonesian | Set language="id", restart | All UI strings in Indonesian | PENDING | Auto |
| TC-P7-003 | Language saved to JSON | Change language | `core/settings` JSON has `"language":"id"` | PENDING | Auto |
| TC-P7-004 | Switch back to English | Set language="en" | `t("settings")=="Settings"` | PENDING | Auto |
| TC-P7-005 | Missing key fallback | `t("nonexistent")` | Returns `"nonexistent"`, no crash | PENDING | Auto |
| TC-P7-006 | Restart notice shown | Open Settings → Language | "Restart required" label visible | PENDING | Manual |

---

## Phase P8 — Integration + Full Regression (20 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P8-001 | Full FS screenshot flow | WM+TS on, take FS shot | Image with WM+TS in clipboard | PENDING | Auto |
| TC-P8-002 | Full region screenshot | Select region, take shot | Cropped image with WM+TS | PENDING | Manual |
| TC-P8-003 | Countdown overlay | Delay=3s, take shot | Overlay shows 3…2…1 | PENDING | Manual |
| TC-P8-004 | Countdown cancel (Esc) | Start countdown, Esc | Overlay closes, buttons re-enable | PENDING | Manual |
| TC-P8-005 | Single instance guard | Launch app twice | 2nd exits with code 0 | PENDING | Auto |
| TC-P8-006 | Tray hide + show | Close → tray → double-click | Window reappears | PENDING | Manual |
| TC-P8-007 | Tray screenshot menu | Right-click tray | Menu items functional | PENDING | Manual |
| TC-P8-008 | History persists restart | Take shots, restart | History file exists, items loaded | PENDING | Auto |
| TC-P8-009 | Settings persist restart | Change opacity, restart | Opacity persists in JSON | PENDING | Auto |
| TC-P8-010 | Autosave debounce | 10 rapid changes | 1 write fires 800ms after last | PENDING | Auto |
| TC-P8-011 | WM cache invalidation | Change WM path | `_wm_cache` and `_wm_resize_cache` clear | PENDING | Auto |
| TC-P8-012 | Screenshot from minimized | Minimize, hotkey | Shot taken, app stays minimized | PENDING | Auto |
| TC-P8-013 | Region from minimized | Minimize, region hotkey | Selector appears, app stays minimized | PENDING | Manual |
| TC-P8-014 | Delete history item | Click ✕ on item | Deque count decrements by 1 | PENDING | Auto |
| TC-P8-015 | No TclError on repeat open/close | Open/close Settings 10× | No exception raised | PENDING | Auto |
| TC-P8-016 | No freeze on rapid slider | Move slider 20× fast | UI event loop stays responsive | PENDING | Auto |
| TC-P8-017 | Status bar updates after shot | Take screenshot | Status shows "✓ copied" | PENDING | Auto |
| TC-P8-018 | Status bar restores after 3.5s | Wait after shot | Status shows hotkey summary | PENDING | Auto |
| TC-P8-019 | WM disabled → no watermark | WM OFF, take shot | No WM pixels in image | PENDING | Auto |
| TC-P8-020 | TS disabled → no timestamp | TS OFF, take shot | Image height == screen height | PENDING | Auto |

---

## Automation Summary

| Trigger | Phases | Cases | Type |
|---|---|---|---|
| At M1 milestone | M1 | 10 | Headless — `pytest tests/core/` |
| At M2 milestone | M2 | 8 | Headless — `pytest tests/system/` |
| Manual at M3 | M3 | 6 | Smoke — human tester |
| At Gold Candidate | P1–P8 | 62 AUTO cases | pyautogui + app fixture |

**Total test cases: 106** (16 new M1/M2/M3 + 90 original)
**Automated: 80** (75%) | **Manual: 26** (25%)

---

## Bug Log (carry-forward from HF1)

Next Bug ID: **B-030**

| Bug ID | Phase | Description | Severity | Status |
|---|---|---|---|---|
| B-001 → B-029 | — | Resolved in v3.9.1f HF1 | — | CLOSED |
