# ScreenWatermark Pro v8.0 — Modular Architecture Proposal
**Role: UI/UX Senior Developer**
**Base: Screen_Watermark_3.9.1f_HF1.py (3,799 lines)**

---

## The Core Question: Migrate UI First or Modularize First?

**Answer: Modularize first. Always.**

Here is why, based on what the codebase actually looks like.

---

## 1. Current State — What the Monolith Looks Like

The live build is a single 3,799-line file with 18 logical sections. Here is the size
breakdown and coupling reality:

```
Section                                        Lines     %
------------------------------------------------------------
Dependency check                                  17   0.4%
Constants + Palette                               80   2.1%
Settings I/O                                      25   0.7%
History I/O                                       84   2.2%
Clipboard                                         58   1.5%
Font + WM Cache                                   96   2.5%
History IO Queue                                  29   0.8%
Startup registry                                 222   5.8%
Notification + Tray + Utils                       37   1.0%
HotkeyManager                                     91   2.4%
CountdownOverlay                                 112   2.9%
RegionSelector                                   161   4.2%
Render (apply_watermark, apply_timestamp)        179   4.7%
HotkeyRecorder                                   340   8.9%
SettingsWindow                                   607  16.0%   ← big
HistoryPopup                                     146   3.8%
ScreenWatermarkApp                              1194  31.4%   ← biggest
IPC + Entry point                                195   5.1%
------------------------------------------------------------
TOTAL                                           3799  100%
```

`ScreenWatermarkApp` (1,194 lines, 31%) is the god object. It directly calls:
- `HotkeyManager` ×7
- `RegionSelector` ×9
- `SettingsWindow` ×8
- `HistoryPopup` ×6
- `CountdownOverlay` ×6
- `apply_watermark`, `apply_timestamp` ×3 each
- `save_settings`, `load_settings`, `save_history`, `load_history`
- `_enqueue_save_history`, `get_cached_watermark`, `invalidate_wm_cache`
- `load_font`, `copy_image_to_clipboard`

If you migrate to CTk first inside this monolith, every widget change touches the
god object. You are doing surgery on a patient without isolating the organs first.
Bugs from a UI swap will be impossible to isolate. Test failures will be ambiguous.
Rollback will be a diff nightmare.

---

## 2. Proposed Module Structure

Split by **responsibility boundary**, not by file size.

```
screenwatermark/
│
├── main.py                    ← entry point only (~30 lines)
│
├── core/
│   ├── __init__.py
│   ├── constants.py           ← BG, PANEL, CARD, ACCENT, palette, PREVIEW_W/H
│   ├── settings.py            ← load_settings(), save_settings(), DEFAULT_SETTINGS
│   ├── history.py             ← save_history(), load_history(), serial IO queue
│   ├── render.py              ← apply_watermark(), apply_timestamp()
│   ├── clipboard.py           ← copy_image_to_clipboard(), _cb_win32/macos/linux
│   ├── font_cache.py          ← load_font(), @lru_cache
│   └── wm_cache.py            ← get_cached_watermark(), _get_wm_resized(), invalidate
│
├── system/
│   ├── __init__.py
│   ├── startup.py             ← set_run_at_startup(), get_run_at_startup()
│   ├── ipc.py                 ← _acquire_single_instance(), _ipc_server_thread()
│   ├── tray.py                ← _make_tray_icon(), _start_tray(), _hide_to_tray()
│   └── hotkeys.py             ← HotkeyManager, HotkeyRecorder, _ensure_pynput()
│
├── ui/
│   ├── __init__.py
│   ├── theme.py               ← i18n.py, font constants, color helpers
│   ├── main_window.py         ← ScreenWatermarkApp (CTk)
│   ├── settings_window.py     ← SettingsWindow (CTkToplevel)
│   ├── history_popup.py       ← HistoryPopup (CTkToplevel)
│   ├── overlays.py            ← CountdownOverlay, RegionSelector (pure tk.Toplevel)
│   └── widgets/
│       ├── __init__.py
│       ├── accordion.py       ← reusable CTk accordion component
│       ├── panel_toggle.py    ← Preview/History pill toggle
│       ├── shot_buttons.py    ← split Fullscreen + Region button group
│       └── config_rows.py     ← slider_row, pill_toggle, color_swatch helpers
│
└── i18n.py                    ← localization (already planned)
```

---

## 3. Dependency Graph (clean after split)

```
main.py
  └── ui/main_window.py
        ├── core/settings.py
        ├── core/history.py
        ├── core/render.py          (apply_watermark, apply_timestamp)
        ├── core/clipboard.py
        ├── core/wm_cache.py
        ├── system/hotkeys.py       (HotkeyManager)
        ├── system/tray.py
        ├── system/ipc.py
        ├── ui/settings_window.py
        │     ├── core/settings.py
        │     └── system/startup.py
        ├── ui/history_popup.py
        │     └── core/history.py
        └── ui/overlays.py
              (zero imports from core — pure UI)
```

No circular imports. `core/` has zero UI imports. `system/` has zero UI imports.
`ui/` imports from both but never the reverse.

---

## 4. Why Modularize Before UI Migration

### Reason 1 — Blast radius control

When you do `ScreenWatermarkApp(tk.Tk)` → `ScreenWatermarkApp(ctk.CTk)` in a
monolith, a bug in the WM cache can look like a CTk rendering bug. With modules,
`core/wm_cache.py` has its own test. You know the bug is in `ui/main_window.py`.

### Reason 2 — Each module can be tested in isolation

`core/render.py` has no UI dependency. You can run `test_render.py` headlessly.
`core/settings.py` has no UI dependency. `test_settings.py` runs in CI without
a display. Currently, these are untestable without spawning the whole app.

### Reason 3 — CTk migration becomes mechanical

Once `ScreenWatermarkApp` is isolated in `ui/main_window.py`, the CTk swap is
just: change the class declaration + rebuild `_build_ui()`. Nothing in `core/`
or `system/` needs to know or care.

### Reason 4 — `ui/widgets/` components are reusable

The accordion, pill toggle, and shot button group you designed for v8.0 become
proper components in `ui/widgets/`. The programmer builds them once, tests them
once, and they drop into `main_window.py`, `settings_window.py`, or anywhere else.

### Reason 5 — Parallel work becomes real

Today, one programmer owns the whole file. After modularization:
- Programmer A owns `core/` — no UI knowledge needed
- Programmer B owns `ui/` — imports from core, no need to understand hotkeys
- QA can test `core/` immediately, before UI is touched

---

## 5. Recommended Build Sequence

```
STEP 1 — Extract core/ (no behavior change, no UI change)
STEP 2 — Extract system/ (no behavior change, no UI change)
STEP 3 — Isolate ui/ classes into separate files (no behavior change)
STEP 4 — Build ui/widgets/ components (new CTk widgets, tested standalone)
STEP 5 — Migrate main_window.py to CTk (behavior-preserving UI swap)
STEP 6 — Migrate settings_window.py to CTk
STEP 7 — Apply i18n
STEP 8 — Integration + GC
```

Steps 1–3 = modularization (zero user-visible change, fully regression-safe).
Steps 4–7 = CTk migration (UI changes, covered by your test suite).
Steps 1–3 can be done in 1–2 days. They de-risk everything after.

---

## 6. Step-by-Step Extraction Plan

### Step 1 — Extract `core/` (safest, start here)

These are pure functions with zero UI coupling. Extract exactly as-is.

| What | Source lines | Target |
|---|---|---|
| `BG, PANEL, CARD...` constants | 218–223 | `core/constants.py` |
| `DEFAULT_SETTINGS`, `load_settings()`, `save_settings()` | 144–248 | `core/settings.py` |
| `save_history()`, `load_history()` | 249–332 | `core/history.py` |
| `copy_image_to_clipboard()` + platform helpers | 333–390 | `core/clipboard.py` |
| `load_font()` | 391–411 | `core/font_cache.py` |
| `get_cached_watermark()`, `_get_wm_resized()`, `invalidate_wm_cache()` | 412–486 | `core/wm_cache.py` |
| `apply_watermark()`, `apply_timestamp()` | 1139–1317 | `core/render.py` |
| `safe_hex_to_rgb()`, `safe_strftime()` | 762–774 | `core/utils.py` |

**Rule:** copy the function verbatim. Add one import line at the top of the
source file: `from core.X import Y`. Run existing app. It must behave identically.
This is a pure refactor — no logic change.

Verification: `python Screen_Watermark_3.9.1f_HF1.py` launches and functions
exactly as before.

### Step 2 — Extract `system/`

Still no UI coupling. These talk to OS APIs only.

| What | Source lines | Target |
|---|---|---|
| `_history_io_worker()`, `_enqueue_save_history()`, `_history_io_q` | 487–515 | `core/history.py` (append) |
| `set_run_at_startup()`, `get_run_at_startup()` + helpers | 516–737 | `system/startup.py` |
| `_acquire_single_instance()`, `_ipc_server_thread()` | 3605–3762 | `system/ipc.py` |
| `HotkeyManager`, `HotkeyRecorder`, `_ensure_pynput()` | 775–865, 1318–1657 | `system/hotkeys.py` |
| `_make_tray_icon()`, `_win_toast()` | 738–760 | `system/tray.py` |

**Rule:** same as Step 1. Verbatim extraction, add imports, verify app unchanged.

### Step 3 — Isolate `ui/` classes

Move classes into their own files. Still `tkinter`, no CTk yet.

| What | Target |
|---|---|
| `SettingsWindow` (607 lines) | `ui/settings_window.py` |
| `HistoryPopup` (146 lines) | `ui/history_popup.py` |
| `CountdownOverlay` (112 lines) | `ui/overlays.py` |
| `RegionSelector` (161 lines) | `ui/overlays.py` (append) |
| `ScreenWatermarkApp` (1194 lines) | `ui/main_window.py` |

Each file just needs imports from `core/` and `system/`. No logic change.

Verification: full manual smoke test — screenshot, history, settings, tray.

### Step 4 — Build `ui/widgets/` (new code, CTk)

Now you write new code for the first time. These are pure UI components with no
dependency on app state — they accept vars and callbacks as constructor arguments.

```python
# ui/widgets/accordion.py
class CTkAccordion(ctk.CTkFrame):
    def __init__(self, parent, title, icon, open_by_default=False, **kwargs):
        ...
    def set_body(self, build_fn):
        ...
    def toggle(self):
        ...
    def set_summary(self, text: str):
        ...
```

```python
# ui/widgets/panel_toggle.py
class PanelToggle(ctk.CTkFrame):
    def __init__(self, parent, panels: list[tuple[str,str]], command, **kwargs):
        # panels = [("🖼 Preview", "preview"), ("🕒 History", "history")]
        ...
    def set_active(self, key: str):
        ...
    def set_badge(self, key: str, count: int):
        ...
```

```python
# ui/widgets/shot_buttons.py
class SplitShotButton(ctk.CTkFrame):
    def __init__(self, parent, on_fullscreen, on_region, **kwargs):
        ...
    def set_enabled(self, enabled: bool):
        ...
```

These can be developed and tested completely independently. No app needed.

### Step 5–7 — CTk migration

At this point the migration is mechanical. `ui/main_window.py` is a clean,
isolated file. Swap `tk.Tk` → `ctk.CTk`, rebuild `_build_ui()` using the
widget components from Step 4. Your Implementation_Guideline_v8.0.md is the
exact playbook.

---

## 7. Risk Comparison

| Approach | Risk | If a bug appears |
|---|---|---|
| Migrate UI first (monolith) | High | Impossible to tell if bug is CTk, logic, or coupling |
| Modularize first, then migrate | Low | Bug is in exactly one file, testable in isolation |
| Modularize + migrate simultaneously | Very High | Never do this |

---

## 8. Effort Estimate

| Step | Effort | Risk |
|---|---|---|
| Step 1 — Extract core/ | 0.5 day | Very Low (copy + import) |
| Step 2 — Extract system/ | 0.5 day | Very Low |
| Step 3 — Isolate ui/ classes | 0.5 day | Low |
| Step 4 — Build ui/widgets/ | 1.5 days | Low (new code, isolated) |
| Step 5–6 — CTk migration | 2–3 days | Medium (covered by test suite) |
| Step 7 — i18n | 0.5 day | Low |
| Step 8 — Integration GC | 1 day | Low |
| **Total** | **~7 days** | |

Steps 1–3 alone (1.5 days) reduce the risk of Steps 4–8 by roughly 60%.
They are the cheapest insurance you can buy on this project.

---

## 9. File Count After Modularization

```
core/          8 files   ~850 lines total
system/        4 files   ~650 lines total
ui/            5 files   ~1,900 lines total
ui/widgets/    5 files   ~400 lines total (new)
i18n.py        1 file    ~150 lines
main.py        1 file    ~30 lines
--------------------------------------------
Total          24 files  ~3,980 lines
```

Compared to 1 file × 3,799 lines now. Each file averages ~166 lines.
Every file has a single clear responsibility.

---

## 10. Summary Answer

**Modularize first. Then migrate.**

Not because it is the textbook answer — because of what this specific codebase
looks like. `ScreenWatermarkApp` at 1,194 lines already holds 31% of the code
and touches every other system. `SettingsWindow` at 607 lines is tightly coupled
to app vars through traces. Doing a CTk swap inside this tangled state means
any breakage could be anywhere. After modularization, breakage is exactly where
you can find it.

Steps 1–3 are zero-risk extractions. They produce no user-visible change.
They create the foundation that makes Steps 5–7 safe, fast, and testable.
