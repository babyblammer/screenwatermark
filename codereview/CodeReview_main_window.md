# Code Review — `ui/main_window.py`
**Reviewer:** PM/Design via spec audit
**File reviewed:** `ui/main_window.py` (uploaded build)
**Spec references:** `main_window.md`, `UI_UX_Spec_v8.0.md`, `Behavior_Addendum_v8.0.md`

**Result: 12 bugs, 4 warnings. App will crash before rendering.**

---

## Summary

| Severity | Count |
|---|---|
| 🔴 CRITICAL | 5 |
| 🟠 HIGH | 4 |
| 🟡 MEDIUM | 3 |
| ⚠️ WARNING | 4 |

Fix all CRITICAL bugs first — the app cannot launch without them.

---

## 🔴 B1-CRITICAL — `ctk.StringVar` used instead of `tk.StringVar`

**Location:** `__init__` — every variable declaration

**Problem:**
CTk vars (`ctk.StringVar`, `ctk.BooleanVar`, `ctk.IntVar`) do not have a `.trace_add()` method. Every single trace registered in `__init__` will raise `AttributeError` and crash the app on startup.

**What programmer wrote:**
```python
self.watermark_path = ctk.StringVar(value=cfg["watermark_path"])
self.wm_enabled     = ctk.BooleanVar(value=bool(cfg.get("wm_enabled", True)))
self.wm_opacity     = ctk.IntVar(value=int(cfg["wm_opacity"]))
# ... all vars using ctk.*
```

**Fix — change every var to `tk.*`:**
```python
self.watermark_path = tk.StringVar(value=cfg["watermark_path"])
self.wm_enabled     = tk.BooleanVar(value=bool(cfg.get("wm_enabled", True)))
self.wm_opacity     = tk.IntVar(value=int(cfg["wm_opacity"]))
# ... all vars — use tk.StringVar / tk.BooleanVar / tk.IntVar
```

This applies to ALL ~25 vars AND `self.status_var` in `_build_bottom_bar()`.

---

## 🔴 B2-CRITICAL — `preview_wrap` never packed on launch

**Location:** `_build_preview_and_history()`

**Problem:**
`self.preview_wrap` is created and `pack_propagate(False)` is set, but `.pack()` is never called. On launch, the canvas is completely invisible. The middle frame shows only toggle + accordions.

**What programmer wrote:**
```python
self.preview_wrap = ctk.CTkFrame(self.middle_frame, height=180, ...)
self.preview_wrap.pack_propagate(False)
# ← .pack() missing here
```

**Fix — add pack at the end of `_build_preview_and_history()`, after building history panel:**
```python
# At the END of _build_preview_and_history(), after building both panels:

# Pack preview on launch (visible by default)
self.preview_wrap.pack(fill="x", padx=12, pady=(0, 8))

# History panel: build but DO NOT pack
# self.history_panel_wrap — NOT packed here
# _switch_panel() handles pack/unpack
```

---

## 🔴 B3-CRITICAL — `self.tabview.set()` called — tabview does not exist

**Location:** `_go_history_tab()`, `_history_smart_open()`

**Problem:**
`ttk.Notebook` was removed in v8.0. There is no `self.tabview`. Both methods crash with `AttributeError`.

**What programmer wrote:**
```python
def _go_history_tab(self):
    self.tabview.set("Riwayat")   # ← crashes

def _history_smart_open(self):
    state = "normal"
    if state == "normal":
        self.tabview.set("Riwayat")   # ← crashes, also state is hardcoded "normal"
```

**Fix:**
```python
def _go_history_tab(self):
    self._switch_panel("history")

def _history_smart_open(self):
    state = self.wm_state()
    if state == "normal":
        self.lift()
        self.focus_force()
        self._switch_panel("history")
    else:
        self._show_history_popup()
```

---

## 🔴 B4-CRITICAL — `self.btn_shot` hacked to private attribute of `SplitShotButton`

**Location:** `_build_bottom_bar()`, `_start_screenshot()`, `_do_screenshot()`, `_cancel_countdown()`

**Problem:**
Programmer added `self.btn_shot = self.shot_btn._btn_fullscreen` as a "compatibility hack". This accesses a private attribute. Worse: `_start_screenshot()`, `_do_screenshot()` finally block, and `_cancel_countdown()` all call `self.btn_shot.configure(state="normal/disabled")` — this only affects the Fullscreen button, leaving Region button in wrong state.

**What programmer wrote:**
```python
# _build_bottom_bar:
self.btn_shot = self.shot_btn._btn_fullscreen   # ← hack

# _start_screenshot:
self.btn_shot.configure(state="disabled")   # ← only disables fullscreen btn

# _do_screenshot finally:
self.after(0, lambda: self.btn_shot.configure(state="normal"))   # ← only re-enables fullscreen
```

**Fix — use `SplitShotButton.set_enabled()` everywhere:**

Delete the `self.btn_shot = ...` line entirely.

Replace every `self.btn_shot.configure(state=...)`:

```python
# Disable both buttons:
self.shot_btn.set_enabled(False)

# Enable both buttons:
self.shot_btn.set_enabled(True)
```

Locations to update:
1. `_start_screenshot()` entry → `self.shot_btn.set_enabled(False)`
2. `_do_screenshot()` finally → `self.after(0, lambda: self.shot_btn.set_enabled(True))`
3. `_on_region_cancelled()` → `self.shot_btn.set_enabled(True)`
4. `_cancel_countdown()` → `self.shot_btn.set_enabled(True)`

---

## 🔴 B5-CRITICAL — `_set_accordions_enabled()` disables accordions when switching to History

**Location:** `_switch_panel()`, `_set_accordions_enabled()`

**Problem:**
Spec says: accordions are always interactive regardless of which panel is active. User should be able to change WM/TS settings while looking at History. Disabling them on history switch breaks this.

Also, `widget.configure(state="disabled")` on a `CTkFrame` raises an error — frames don't have a `state` attribute.

**What programmer wrote:**
```python
def _switch_panel(self, which):
    if which == "preview":
        ...
        self._set_accordions_enabled(True)   # ← wrong concept
    else:
        ...
        self._set_accordions_enabled(False)  # ← wrong concept

def _set_accordions_enabled(self, enabled: bool):
    for widget in self.wm_accordion.winfo_children():
        widget.configure(state="normal")  # ← CTkFrame has no state, will crash
```

**Fix — delete `_set_accordions_enabled()` entirely. Update `_switch_panel()`:**

```python
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
    # NO accordion enable/disable — they are always active
```

---

## 🟠 B6-HIGH — `entry['time']` key does not exist

**Location:** `_render_history_panel()`

**Problem:**
History entry dict uses key `"timestamp"` (a `datetime` object), not `"time"` (a string). Causes `KeyError` when rendering history panel.

**What programmer wrote:**
```python
meta = ctk.CTkLabel(item, text=entry.get("time", "")[:16], ...)
```

**Fix:**
```python
meta = ctk.CTkLabel(item,
    text=entry["timestamp"].strftime("%H:%M  %d/%m"),
    font=(FONT_MONO, 8), text_color=MUTED, fg_color="transparent")
```

---

## 🟠 B7-HIGH — `preview_canvas.pack(padx=10, pady=10)` shrinks canvas

**Location:** `_build_preview_and_history()`

**Problem:**
20px of padding on each axis makes the canvas smaller than its frame. Canvas should fill the frame completely.

**What programmer wrote:**
```python
self.preview_canvas.pack(padx=10, pady=10)
```

**Fix:**
```python
self.preview_canvas.pack()
# Or if preview_inner frame is used:
# self.preview_canvas.place(x=0, y=0)
# Remove the preview_inner intermediate frame entirely — canvas goes directly in preview_wrap
```

Simplest fix — remove the `preview_inner` frame and pack canvas directly:
```python
self.preview_canvas = tk.Canvas(
    self.preview_wrap,
    width=PREVIEW_W, height=PREVIEW_H,
    bg="#0a0a12", highlightthickness=0)
self.preview_canvas.pack()
```

---

## 🟠 B8-HIGH — `self._panel_mode` never initialized

**Location:** `__init__` state section

**Fix — add to state section in `__init__`:**
```python
self._panel_mode = "preview"   # ADD THIS
```

---

## 🟠 B9-HIGH — `self._wm_acc_open` and `self._ts_acc_open` never set

**Location:** `__init__` state section

These flags are checked by QA tests and used by accordion toggle methods.

**Fix — add to state section in `__init__`:**
```python
self._wm_acc_open = True    # WM open by default
self._ts_acc_open = False   # TS closed by default
```

---

## 🟡 B10-MEDIUM — Header badge `wm_indicator` does not update dynamically

**Location:** `__init__` — after `all_vars` traces section

**Problem:**
`_update_wm_indicator()` is called once in `_build_header()` but never again. When user enables/disables WM or changes the file path, the badge stays stale.

**Fix — add two traces after the `all_vars` loop:**
```python
# After the for v in all_vars: v.trace_add(...) block
self.wm_enabled.trace_add("write", lambda *_: self._update_wm_indicator())
self.watermark_path.trace_add("write", lambda *_: self._update_wm_indicator())
```

---

## 🟡 B11-MEDIUM — `self.ui_language` var never declared

**Location:** `__init__`

**Problem:**
`SettingsWindow` binds a language `CTkOptionMenu` to `app.ui_language`. If not declared, Settings window crashes on open.

**Fix — add to vars section in `__init__`:**
```python
self.ui_language = tk.StringVar(value=cfg.get("language", "en"))
```

Add to `all_vars` list:
```python
all_vars = [
    ...existing vars...,
    self.ui_language,   # ADD
]
```

Add to `_refresh_snapshot()`:
```python
self._settings_snapshot = {
    ...existing keys...,
    "language": self.ui_language.get(),   # ADD
}
```

---

## 🟡 B12-MEDIUM — `_render_history()` layout wrong for horizontal scroll

**Location:** `_render_history()`

**Problem:**
`_render_history()` uses `item.pack(fill="x")` which is a vertical list layout. But `self.history_scroll` is a horizontal `CTkScrollableFrame`. Items should pack `side="left"` not `fill="x"`.

**Fix:**
```python
# In _render_history(), change item packing:
item = ctk.CTkFrame(self.history_scroll, fg_color=CARD, corner_radius=6,
                    width=120)
item.pack(side="left", padx=4, pady=2)   # ← side="left" for horizontal
item.pack_propagate(False)
```

---

## ⚠️ Warnings (fix before GC)

**W1 — `middle_frame.pack(fill="x", padx=10)`**
Remove `padx=10`. Children handle their own padding via `padx=12` on `.pack()` calls.
```python
self.middle_frame.pack(fill="x")   # no padx
```

**W2 — VERSION = "3.9.1f"**
```python
VERSION = "4.0.0"
```

**W3 — Badge text uses colon `"WM: ✓"` — spec says `"WM ✓"`**
```python
# _update_wm_indicator():
self.wm_indicator.configure(text="WM ✓", ...)   # no colon
self.wm_indicator.configure(text="WM ⚠", ...)
self.wm_indicator.configure(text="WM OFF", ...)
```

**W4 — `status_var = ctk.StringVar`**
Fixed by B1 — change to `tk.StringVar`.

---

## Fix Priority Order

Fix in this exact order to avoid cascading errors:

1. **B1** — change all ctk vars to tk vars (app cannot start without this)
2. **B2** — pack `preview_wrap` on launch (canvas invisible without this)
3. **B3** — remove `tabview` references (crashes on hotkey press)
4. **B5** — delete `_set_accordions_enabled()` (crashes on panel switch)
5. **B4** — replace `btn_shot` hack with `shot_btn.set_enabled()` (wrong state management)
6. **B6** — fix `entry["time"]` → `entry["timestamp"].strftime(...)` (crashes on history render)
7. **B7** — remove canvas padding
8. **B8, B9** — add missing state flags to `__init__`
9. **B10, B11, B12** — add missing traces, language var, layout fix
10. **W1–W4** — cleanup warnings

---

## What Was Done Well

- Screenshot flow (`_do_screenshot`, `_countdown`, `_on_region_selected/cancelled`) preserved correctly from original — no logic changes, good.
- History persistence (`_enqueue_save_history`, `_history_lock` usage) correct.
- `_refresh_snapshot()` structure correct (missing only `language` key — B11).
- `SplitShotButton` component properly imported and instantiated.
- `CTkAccordion` component used correctly for both WM and TS.
- Autosave debounce (800ms), preview debounce (350ms) preserved correctly.
- Tray, IPC, startup logic unchanged — correct.
