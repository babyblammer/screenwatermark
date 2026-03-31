# UPD40 Bug Fixes Log
**Date:** 2026-03-31
**Version:** 4.1.0a
**Source:** `issues/UPD40_4.0.0_bug report.txt`

---

## COMPLETE CHANGE LOG SINCE 4.0.0b

### MAJOR UI RESTRUCTURING

---

## 1. WM Config Card Layout (Replaced Accordion)
**Status:** COMPLETED ✅

**Problem:** WM accordion had too many pills and buttons.

**Changes:**
- Replaced WM accordion with simple card frame
- Mode: Pills → Dropdown (Off, Normal, Full Screen, Pattern)
- Position: 5 icon buttons → Dropdown (Bottom-Left, Bottom-Right, Top-Left, Top-Right, Center)
- Added config summary in title area
- Opacity/Scale disabled when Mode=Off
- Scale only enabled for Normal/Pattern modes
- Position dropdown enabled only for Normal mode

**New Features:**
- Pattern Gap slider (NEW - only for Pattern mode)
- Path label replaces path entry (click to browse)

**Files Modified:** `ui/main_window.py`

---

## 2. TS Config Card Layout (Replaced Accordion)
**Status:** COMPLETED ✅

**Problem:** TS accordion had too many options.

**Changes:**
- Replaced TS accordion with simple card frame
- Enable: Pills → Dropdown (Off, Outside)
- Font Size: Slider + Label
- Text Color: Color button
- TS Format: Dropdown (DD/MM/YYYY HH:MM:SS, ISO) - MOVED FROM Settings
- Removed: Position, Bold, BG, Shadow options

**New Methods:**
- `_sync_ts_enable_var()` - Syncs dropdown value with StringVar
- `_on_ts_enable_change()` - Handles dropdown changes
- `_on_ts_format_change()` - Handles format dropdown changes
- `_refresh_ts_controls()` - Enables/disables controls based on mode
- `_update_ts_summary()` - Updates config summary text
- `_update_ts_color_btn()` - Syncs color button with variable

**Files Modified:** `ui/main_window.py`

---

## 3. Accordion Widget Removal
**Status:** COMPLETED ✅

**Changes:**
- Deleted `ui/widgets/accordion.py` - no longer needed
- All accordion references removed

---

## 4. TS Position Config Removal
**Status:** COMPLETED ✅

**Problem:** TS position caused strip at top instead of bottom.

**Changes:**
- Removed `ts_position` variable
- Removed `ts_position` from settings snapshot and traces
- Removed `ts_position` key from DEFAULT_SETTINGS
- Simplified `apply_timestamp()` in render.py:
  - Removed overlay mode (else branch)
  - Strip always placed at bottom (right-aligned)
  - Removed all position-related logic

**Files Modified:**
- `ui/main_window.py`
- `core/settings.py`
- `core/render.py`
- `tests/conftest.py`
- `tests/ui/test_p3_p4_p5.py`
- `tests/core/test_m1_core.py`

---

## 5. Settings Window Restructuring
**Status:** COMPLETED ✅

**Removed:**
- `_build_removed_notice()` method and call
- Default Mode dropdown
- TS Format entry + preset buttons (moved to Main Window)
- Region row + reset button

**Kept:**
- Delay slider

**Styling Updates:**
- Language dropdown styled to match Main Window (button_color=BORDER)
- Delay slider styled to match Main Window (fg_color=BORDER)

---

## 6. Bottom Bar Restructuring
**Status:** COMPLETED ✅

**Changes:**
- Removed btn_riwayat (history button) - redundant with panel tabs
- Added btn_settings to bottom bar
- Layout: [Settings] [Fullscreen] [Region]

---

## 7. Header Settings Button Removal
**Status:** COMPLETED ✅

**Changes:**
- Removed header btn_settings (now in bottom bar)

---

## 8. Panel Toggle Alignment
**Status:** COMPLETED ✅

**Changes:**
- Fixed `padx=0` → `padx=12` to align with WM/TS cards

---

### BUG FIXES

---

## 9. WM Mode Not Synced with wm_enabled (CRITICAL)
**Status:** FIXED ✅

**Problem:** Watermark not displayed in all modes.

**Fix:**
- Added `self.wm_enabled.set(mode != "Off")` in `_on_wm_mode_change()`
- Added sync in `_sync_wm_mode_var()` for startup
- Removed duplicate `_on_wm_mode_change` method

**Files Modified:** `ui/main_window.py`

---

## 10. WM Fullscreen/Pattern Not Displaying (CRITICAL)
**Status:** FIXED ✅

**Problem:** wm_mode stored as display values ("Full Screen") but render.py expected lowercase ("full").

**Fix:**
- In `_refresh_snapshot()`, convert wm_mode to lowercase:
```python
wm_mode_val = self.wm_mode.get().lower()
if wm_mode_val == "full screen":
    wm_mode_val = "full"
```

---

## 11. TS Mode Not Working (CRITICAL)
**Status:** FIXED ✅

**Problem:** TS dropdown not syncing with ts_enabled/ts_outside_canvas.

**Fix:**
- `_on_ts_enable_change()` now updates ts_enabled and ts_outside_canvas
- Added `self._on_setting_changed()` call to refresh preview

---

## 12. Preview Not Showing TS Outside
**Status:** FIXED ✅

**Problem:** Preview canvas not updating when TS Enable changed.

**Fix:**
- `_on_ts_enable_change()` calls `_on_setting_changed()` before refresh controls

---

## 13. TS Strip Position Fix
**Status:** FIXED ✅

**Problem:** TS displayed at bottom-left instead of bottom-right.

**Fix:**
- Changed `tx = pad + 10` to `tx = w - tw - pad - 10` in render.py

---

## 14. Scale Disabled for Fullscreen/Pattern
**Status:** FIXED ✅

**Problem:** Scale was disabled for Fullscreen/Pattern modes.

**Fix:**
- Changed `_refresh_wm_controls()` to only disable when Mode=Off
- Scale enabled for Normal and Pattern modes

---

## 15. Region Reset to Fullscreen
**Status:** FIXED ✅

**Problem:** After region capture (select or cancel), mode stayed as "region".

**Fix:**
- Added `capture_mode.set("fullscreen")` + `_on_mode_change()` to:
  - `_on_region_selected()`
  - `_on_region_cancelled()`

---

## 16. Delay Reset After Screenshot
**Status:** FIXED ✅

**Problem:** Delay persisted for all subsequent screenshots.

**Fix:**
- In `_do_screenshot()` finally block:
```python
if self.delay_sec.get() > 0:
    self.delay_sec.set(0)
    self._refresh_snapshot()
    if self._settings_win and self._settings_win.winfo_exists():
        try:
            self._settings_win.delay_val_lbl.configure(text="0 s")
        except: pass
```

---

## 17. Delay Reset on ESC/Cancel
**Status:** FIXED ✅

**Problem:** Delay not reset when countdown cancelled with ESC.

**Fix:**
- Added same reset logic to `_cancel_countdown()`

---

## 18. Settings Window Delay Label Update
**Status:** FIXED ✅

**Problem:** Settings window delay label not updating when reset.

**Fix:**
- Stored delay label as instance variable `self.delay_val_lbl`
- Added check `if var == self.app.delay_sec` in `_slider_row()`

---

## 19. Path Label Width Match Dropdown
**Status:** FIXED ✅

**Problem:** Path label width didn't match dropdown width.

**Fix:**
- Wrapped path label in frame with `pack_propagate(False)` and `width=DROPDOWN_W, height=DROPDOWN_H`

---

### NEW FEATURES

---

## 20. Pattern Gap Slider (NEW)
**Status:** COMPLETED ✅

**Changes:**
- Added `wm_pattern_gap` IntVar (default: 20, range: 5-100)
- Added Pattern Gap slider row (only enabled for Pattern mode)
- Updated `render.py` to use configurable gap
- Summary shows gap value for Pattern mode
- Added to DEFAULT_SETTINGS

**Files Modified:**
- `ui/main_window.py`
- `core/settings.py`
- `core/render.py`

---

## 21. DROPDOWN_W/H Constants (NEW)
**Status:** COMPLETED ✅

**Changes:**
- Added `DROPDOWN_W = 130` and `DROPDOWN_H = 28` to constants.py
- All dropdowns now use these constants
- Path label frame uses DROPDOWN_W/H for width matching

**Files Modified:**
- `core/constants.py`
- `ui/main_window.py`

---

## 22. TS Format Dropdown (NEW in Main Window)
**Status:** COMPLETED ✅

**Changes:**
- Added `ts_format_display` StringVar for dropdown display
- Added TS Format dropdown to TS config card
- Added `_sync_ts_format_display()` and `_on_ts_format_change()` methods
- Removed from Settings window

---

## 23. UI Consistency - Slider Styling
**Status:** COMPLETED ✅

**Changes:**
- Settings delay slider now matches main window style:
  - `fg_color=BORDER`
  - `progress_color=ACCENT`
  - Removed `button_color` and `button_hover_color`

---

## 24. UI Consistency - Language Dropdown
**Status:** COMPLETED ✅

**Changes:**
- Language dropdown styled to match main window:
  - `button_color=BORDER`
  - `button_hover_color=ACCENT`
  - `dropdown_fg_color=PANEL`
  - `text_color=TEXT`

---

### SUMMARY

| Category | Items |
|----------|-------|
| Major UI Restructuring | 8 |
| Bug Fixes | 11 |
| New Features | 4 |
| UI Consistency | 2 |

**Total: 25 change items since 4.0.0b**

---

## Version Bump Analysis

Based on `docs/VERSIONING_RULES.md`:

| Change Type | Description |
|-------------|-------------|
| **NEW FEATURES** | Pattern Gap slider, TS Format dropdown, DROPDOWN_W/H constants |
| Bug Fixes | 11 critical/major/minor fixes |
| UI Restructuring | Settings cleanup, accordion removal, dropdown unification |

**Per Rules:** Y (Update) increases when there are "penambahan fitur baru atau perubahan fungsionalitas yang cukup signifikan"

**Recommendation:** Since we have NEW FEATURES → Bump Y

```
Current: 4.1.0a ✅ (Applied)
```

---

## Files Modified (Complete List)

| File | Changes |
|------|---------|
| `ui/main_window.py` | ~150 lines |
| `ui/settings_window.py` | ~30 lines |
| `core/constants.py` | +DROPDOWN_W, DROPDOWN_H |
| `core/settings.py` | -ts_position, +wm_pattern_gap |
| `core/render.py` | Simplified apply_timestamp(), +pattern_gap |
| `tests/conftest.py` | Removed ts_position |
| `tests/ui/test_p3_p4_p5.py` | Updated tests |
| `tests/core/test_m1_core.py` | Updated tests |

**Deleted:**
- `ui/widgets/accordion.py`

---

## Test Status

```
Core tests (M1): 17/17 PASS ✅
System tests (M2): 16/16 PASS ✅
UI tests: Pass when run with GUI
```

---

## Verification

```bash
cd D:\Master\Vibecoding 2\screenwatermark
python -m pytest tests/core/ tests/system/ -v
```
