# ScreenWatermark Pro v8.0 — Migration Plan
**tkinter → customtkinter | Modular + Phased Delivery**
Version: 2.0-SYNCED | Supersedes v1.0

---

## Overview

Migration runs in two tracks:

**Track A — Modularization (M1–M3):** Split the 3,799-line monolith into a clean
package. Zero user-visible change. Zero UI touch. Pure extraction and import rewiring.

**Track B — CTk Migration (P0–P7):** Rebuild the UI layer on customtkinter.
Only starts after Track A is complete and verified.

This order is mandatory. See `Modular_Architecture_Proposal_v8.0.md` for full reasoning.

---

## Phase Summary

### Track A — Modularization

| Phase | Scope | Milestone | QA |
|---|---|---|---|
| M1 | Extract `core/` | `screenwatermark/core/` populated | TC-M1-001→010 (headless) |
| M2 | Extract `system/` | `screenwatermark/system/` populated | TC-M2-001→008 (headless) |
| M3 | Isolate `ui/` classes | `screenwatermark/ui/` populated | TC-M3-001→006 (smoke) |

### Track B — CTk Migration

| Phase | Scope | Build file | QA |
|---|---|---|---|
| P0 | Env + i18n + `ui/widgets/` | setup only | — |
| P1 | CTk shell: window, titlebar, header | `_P1_shell.py` | TC-P1-001→010 |
| P2 | Canvas toggle + preview + history panel | `_P2_canvas.py` | TC-P2-001→014 |
| P3 | WM accordion inline | `_P3_wm.py` | TC-P3-001→018 |
| P4 | TS accordion inline | `_P4_ts.py` | TC-P4-001→014 |
| P5 | Split shot buttons | `_P5_shot.py` | TC-P5-001→010 |
| P6 | Settings window stripped + rebuilt | `_P6_settings.py` | TC-P6-001→013 |
| P7 | Localization (i18n) | `_P7_i18n.py` | TC-P7-001→006 |
| GC | Full integration + regression | `4.0.0_GCa.py` | TC-P8-001→020 |

---

## Target Package Structure (after M1–M3)

```
screenwatermark/
│
├── main.py                        ← entry point only (~30 lines)
│
├── core/
│   ├── __init__.py
│   ├── constants.py               ← BG, PANEL, CARD, palette, PREVIEW_W/H
│   ├── settings.py                ← load_settings(), save_settings(), DEFAULT_SETTINGS
│   ├── history.py                 ← save_history(), load_history(), IO queue
│   ├── render.py                  ← apply_watermark(), apply_timestamp()
│   ├── clipboard.py               ← copy_image_to_clipboard()
│   ├── font_cache.py              ← load_font(), @lru_cache
│   ├── wm_cache.py                ← get_cached_watermark(), invalidate_wm_cache()
│   └── utils.py                   ← safe_hex_to_rgb(), safe_strftime()
│
├── system/
│   ├── __init__.py
│   ├── hotkeys.py                 ← HotkeyManager, HotkeyRecorder, _ensure_pynput()
│   ├── startup.py                 ← set_run_at_startup(), get_run_at_startup()
│   ├── ipc.py                     ← _acquire_single_instance(), _ipc_server_thread()
│   └── tray.py                    ← _make_tray_icon(), _win_toast()
│
├── ui/
│   ├── __init__.py
│   ├── main_window.py             ← ScreenWatermarkApp (CTk after P1)
│   ├── settings_window.py         ← SettingsWindow (CTkToplevel after P6)
│   ├── history_popup.py           ← HistoryPopup (CTkToplevel after P2)
│   ├── overlays.py                ← CountdownOverlay, RegionSelector (pure tk forever)
│   └── widgets/
│       ├── __init__.py
│       ├── accordion.py           ← CTkAccordion reusable component
│       ├── panel_toggle.py        ← PanelToggle pill component
│       ├── shot_buttons.py        ← SplitShotButton component
│       └── config_rows.py         ← slider_row, pill_toggle, color_swatch helpers
│
└── i18n.py
```

---

## Phase M1 — Extract `core/`

**Goal:** Move all pure-logic, zero-UI functions. App runs identically after.

**Rule:** Copy function verbatim → add import in monolith → run app → verify.

| What | Source lines | Target |
|---|---|---|
| Palette + dimension constants | 144–223 | `core/constants.py` |
| `DEFAULT_SETTINGS`, `load_settings()`, `save_settings()` | 224–248 | `core/settings.py` |
| `save_history()`, `load_history()`, IO queue | 249–515 | `core/history.py` |
| `copy_image_to_clipboard()` + platform helpers | 333–390 | `core/clipboard.py` |
| `load_font()` | 391–411 | `core/font_cache.py` |
| `get_cached_watermark()`, `_get_wm_resized()`, `invalidate_wm_cache()` | 412–486 | `core/wm_cache.py` |
| `apply_watermark()`, `apply_timestamp()` | 1139–1317 | `core/render.py` |
| `safe_hex_to_rgb()`, `safe_strftime()` | 762–774 | `core/utils.py` |

**Automation:** `pytest tests/core/` — headless, no display required, runs at M1.

---

## Phase M2 — Extract `system/`

**Goal:** Move all OS-coupling code. Still no UI change.

| What | Source lines | Target |
|---|---|---|
| `HotkeyManager`, `HotkeyRecorder`, `_ensure_pynput()` | 775–865, 1318–1657 | `system/hotkeys.py` |
| `set_run_at_startup()`, `get_run_at_startup()` + helpers | 516–737 | `system/startup.py` |
| `_acquire_single_instance()`, `_ipc_server_thread()` | 3605–3762 | `system/ipc.py` |
| `_make_tray_icon()`, `_win_toast()` | 738–760 | `system/tray.py` |

**Automation:** `pytest tests/system/` — headless with mocked pynput, runs at M2.

---

## Phase M3 — Isolate `ui/` Classes

**Goal:** Each UI class gets its own file. Still tkinter. Zero behavior change.

| What | Source lines | Target |
|---|---|---|
| `SettingsWindow` | 1658–2264 | `ui/settings_window.py` |
| `HistoryPopup` | 2265–2410 | `ui/history_popup.py` |
| `CountdownOverlay` | 866–977 | `ui/overlays.py` |
| `RegionSelector` | 978–1138 | `ui/overlays.py` (append) |
| `ScreenWatermarkApp` | 2411–3604 | `ui/main_window.py` |

**Verification:** Full manual smoke test — screenshot, tray, settings, history functional.
`main.py` is now ~30 lines of imports + `ScreenWatermarkApp().mainloop()`.

---

## Phase P0 — Environment + i18n + Widgets Foundation

1. Add `customtkinter>=5.2.2`, `pywinstyles>=1.8` to `requirements_v8.txt`.
2. Create `i18n.py` (English + Indonesian — see `Implementation_Guideline_v8.0.md §i18n`).
3. Add `"language": "en"` to `DEFAULT_SETTINGS` in `core/settings.py`.
4. Build `ui/widgets/accordion.py` — standalone CTk component.
5. Build `ui/widgets/panel_toggle.py` — standalone.
6. Build `ui/widgets/shot_buttons.py` — standalone.
7. Build `ui/widgets/config_rows.py` — helper functions.

**Critical:** Widgets have zero app state dependency. Accept vars + callbacks as args.
Can be tested with a bare `ctk.CTk()` window.

---

## Phases P1–P7

Identical scope to the previous plan. Now applied to the modular package files
(`ui/main_window.py`, `ui/settings_window.py`) instead of a monolith.
See `Implementation_Guideline_v8.0.md` for step-by-step code per phase.

---

## Gold Candidate

**Entry criteria:**
- M1 + M2 headless tests: all PASS
- M3 smoke test: all functional
- P1–P7 UI automated tests: all PASS
- No B-030+ CRITICAL bugs open

**Delivery:**
- [ ] Full `screenwatermark/` package
- [ ] `i18n.py`
- [ ] `requirements_v8.txt`
- [ ] `ScreenWatermark_Changelog.md` updated
- [ ] `QA_Tracker_v8.0_versioned.xlsx`

**Release naming:**
```
screenwatermark/  (package dir)  ← Gold Candidate
v4.0.0_GCa                      ← first GC tag
v4.0.0                           ← Gold (all GC tests pass)
v4.0.1_HF1                       ← Hotfix 1 if needed
```

---

## Parallel Work Map

```
M1 → M2 → M3  (sequential — each depends on prior)
              ↓
             P0  (env + i18n + widgets)
              ↓
             P1  (CTk shell)
              ↓
             P2  (toggle + panels)
              ↓
    ┌─────────┼─────────┐
   P3        P4        P5    ← parallel
    └─────────┼─────────┘
              ↓
             P6  (Settings)
              ↓
             P7  (i18n)
              ↓
             GC
```

M1/M2 headless tests run immediately at their milestone — no need to wait for GC.

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| M1 extraction breaks import chain | Low | Medium | One import at a time, run app after each |
| M3 circular import between `ui/` and `core/` | Low | High | Dependency rule: `core/` and `system/` never import `ui/` |
| CTk `CTkScrollableFrame` height overflow | Medium | Medium | Test both accordions open simultaneously |
| `tk.Canvas` inside `CTkFrame` misaligned | Low | Low | `padx=0, pady=0` on inner frame |
| `RegionSelector` / `CountdownOverlay` break | Low | High | Keep as pure `tk.Toplevel` — never migrate |
| pywinstyles older Windows incompatibility | Low | Low | `try/except`, silent fail |
| i18n missing key crashes | Low | High | `t()` returns key name fallback, never raises |

---

## Effort Estimate

| Phase | Effort | Risk |
|---|---|---|
| M1 — Extract core/ | 0.5 day | Very Low |
| M2 — Extract system/ | 0.5 day | Very Low |
| M3 — Isolate ui/ | 0.5 day | Low |
| P0 — Env + widgets | 1.5 days | Low |
| P1 — CTk shell | 0.5 day | Low |
| P2 — Toggle + panels | 1.0 day | Low |
| P3 + P4 + P5 (parallel) | 2.0 days | Medium |
| P6 — Settings | 1.0 day | Low |
| P7 — i18n | 0.5 day | Low |
| GC | 1.0 day | Low |
| **Total** | **~9 days** | |

M1–M3 (1.5 days) reduce risk of remaining 7.5 days by ~60%.
