# ScreenWatermark Pro v8.0 — Manual QA Tracker
**Scope: Non-automatable cases only (26 total)**
**Automated tests cover 80/106 cases — see HTML reports for those results.**
Version: 2.0-SYNCED

---

## How to Use

1. Confirm M1 + M2 headless reports PASS (`tests/reports/report_M1.html`, `report_M2.html`)
2. Complete M3 smoke tests (section below) — 6 cases, manual
3. Confirm GC GUI report PASS (`tests/reports/report_GCa.html`)
4. Complete all 20 manual UI cases in this tracker
5. All 26 must PASS before release is approved

---

## Test Session Header

| Field | Value |
|---|---|
| Tester | |
| Date | |
| Build | `screenwatermark/` package — v4.0.0_GCa |
| OS | Windows [version] |
| Display | [resolution, DPI] |
| M1 headless report | PASS / FAIL |
| M2 headless report | PASS / FAIL |
| GC GUI report | PASS / FAIL |

---

## Status Key

`PASS` | `FAIL` | `SKIP` | `BLOCKED`

---

## Phase M3 — ui/ Class Isolation Smoke (6 cases)

> Run these after M3 extraction, before any CTk migration begins.
> Confirms the monolith is cleanly split into the package with zero behavior change.

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-M3-001 | App launches from `main.py` | `python main.py` | Window appears, no import errors in terminal | | |
| TC-M3-002 | Fullscreen screenshot works | Press Print Screen | Image in clipboard, history tab updates | | |
| TC-M3-003 | Settings window opens | Click ⚙ Settings | SettingsWindow appears, all cards visible | | |
| TC-M3-004 | History popup opens | Press Ctrl+F9 | HistoryPopup appears with thumbnails | | |
| TC-M3-005 | Region selector opens | Press Ctrl+Shift+F9 | Dark overlay with crosshair appears | | |
| TC-M3-006 | App exits cleanly | Tray → Keluar | Process terminates, no crash or hang | | |

---

## Phase P1 — Visual / OS (2 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P1-001 | CTk dark theme appearance | Launch app | Dark bg `#0a0a10`, no white flash on open, all elements dark | | |
| TC-P1-003 | OS titlebar color | Launch on Windows | Titlebar is dark slate (not default blue/white) via pywinstyles | | |

---

## Phase P1 — Tray (1 case)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P1-010 | App closes to tray | Click X | Window disappears, tray icon remains, no crash | | |

---

## Phase P2 — Visual Toggle (1 case)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P2-004 | Active toggle segment styling | Click Preview, then History | Active = accent purple fill, inactive = dark/muted | | |

---

## Phase P3 — File Dialog (1 case)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P3-011 | WM file picker dialog | Expand WM accordion → Choose… | OS file picker opens, filtered to image formats | | |

---

## Phase P4 — Color Pickers (2 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P4-008 | TS text color swatch | Expand TS accordion → click Color swatch | OS color picker opens; selecting updates swatch + preview | | |
| TC-P4-009 | TS BG color swatch | Click BG swatch | Same — BG color updates correctly | | |

---

## Phase P5 — Region Selector (3 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P5-003 | Region button opens selector | Click ✂ Region | Full-screen dark overlay, crosshair cursor | | |
| TC-P5-006 | Region cancel via Esc | Start selection, press Esc | Overlay closes, both shot buttons re-enable | | |
| TC-P5-008 | Hotkey region | Press Ctrl+Shift+F9 | Region selector overlay appears | | |

---

## Phase P6 — Settings Visual (2 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P6-008 | Settings scrollbar | Open Settings, scroll content | Slim 5px accent scrollbar on hover when content overflows | | |
| TC-P6-009 | Credits popup | Click Credits in footer | Credits popup opens correctly | | |

---

## Phase P7 — Language Restart Notice (1 case)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P7-006 | Restart notice shown | Open Settings → Language | "Restart required to apply language change." label visible | | |

---

## Phase P8 — Full Flow (11 cases)

| ID | Title | Steps | Expected | Status | Notes |
|---|---|---|---|---|---|
| TC-P8-002 | Region screenshot | Click ✂ Region → drag → release | Cropped screenshot with WM+TS in clipboard | | |
| TC-P8-003 | Countdown overlay visual | Set Delay=3s → click 📸 Fullscreen | Full-screen overlay shows 3…2…1 in large font | | |
| TC-P8-004 | Countdown cancel | Start countdown → press Esc | Overlay closes, both buttons re-enable, no screenshot | | |
| TC-P8-006 | Tray hide + show | Close window → double-click tray icon | Window reappears correctly | | |
| TC-P8-007 | Tray right-click screenshot menu | Right-click tray icon | Menu shows Fullscreen/Region/History; each works | | |
| TC-P8-013 | Region from minimized | Minimize app → Ctrl+Shift+F9 | Region selector appears; after shot, app stays minimized | | |

---

## Pending (no-longer-needed) — do not test

The following 3 cases from the original v1.0 tracker are removed because
they are now fully covered by the M3 smoke test above:

- ~~Old: Verify Settings has WM card~~ → covered by TC-M3-003 + TC-P6-002 auto
- ~~Old: Verify notebook tabs~~ → replaced by toggle, covered by TC-P2-001 auto
- ~~Old: btn_shot label updates~~ → replaced by split buttons, covered by TC-P5-001 auto

---

## Sign-off

| Role | Name | Signature | Date |
|---|---|---|---|
| QA Tester | | | |
| PM / Release Owner | | | |

**Release approved:** ☐ YES — all 26 manual PASS + M1/M2/GC automated PASS
**Release blocked:**  ☐ NO  — [reason]

---

## Bug Log

Next Bug ID: **B-030**

| Bug ID | TC ID | Phase | Description | Severity | Status |
|---|---|---|---|---|---|
| | | | | | |
