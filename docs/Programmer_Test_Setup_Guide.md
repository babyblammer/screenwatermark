# ScreenWatermark Pro v8.0 — Programmer Test Setup Guide
**For: Programmer**
Version: 1.0-FINAL

---

## What Is Provided vs What You Write

| Item | Provided? | Action |
|---|---|---|
| `tests/conftest.py` | ✅ Yes — use as-is | Place in `screenwatermark/tests/` |
| `tests/core/test_m1_core.py` | ✅ Yes — use as-is | Place in `screenwatermark/tests/core/` |
| `tests/system/test_m2_system.py` | ✅ Yes — use as-is | Place in `screenwatermark/tests/system/` |
| `tests/ui/test_p1_shell.py` | ✅ Yes — use as-is | Place in `screenwatermark/tests/ui/` |
| `tests/ui/test_p2_panels.py` | ✅ Yes — use as-is | Place in `screenwatermark/tests/ui/` |
| `tests/ui/test_p3_p4_p5_combined.py` | ✅ Yes — use as-is | Place in `screenwatermark/tests/ui/` |
| `tests/ui/test_p6_p7_p8_combined.py` | ✅ Yes — use as-is | Place in `screenwatermark/tests/ui/` |
| `pytest.ini` | ✅ Yes | Place in `screenwatermark/` (project root) |
| `run_tests_M1.bat` | ✅ Yes | Place in `screenwatermark/` |
| `run_tests_M2.bat` | ✅ Yes | Place in `screenwatermark/` |
| `run_tests_GC.bat` | ✅ Yes | Place in `screenwatermark/` |
| `tests/assets/test_watermark.png` | Auto-generated | Runner script creates it |

**You do not write any test code.** You run the provided scripts at the right milestones.

---

## Step 1 — Place Files

After setting up the modular package structure (from M1–M3), your directory should look like:

```
screenwatermark/
│
├── main.py
├── pytest.ini                     ← from this delivery
├── run_tests_M1.bat               ← from this delivery
├── run_tests_M2.bat               ← from this delivery
├── run_tests_GC.bat               ← from this delivery
├── i18n.py
├── requirements_v8.txt
│
├── core/          (after M1)
├── system/        (after M2)
├── ui/            (after M3)
│
└── tests/
    ├── conftest.py                ← from this delivery
    ├── pytest.ini                 ← same as root (pytest finds either)
    ├── assets/
    │   └── test_watermark.png     ← auto-created by run_tests_GC.bat
    ├── reports/                   ← auto-created, holds HTML reports
    │
    ├── core/
    │   └── test_m1_core.py        ← from this delivery
    │
    ├── system/
    │   └── test_m2_system.py      ← from this delivery
    │
    └── ui/
        ├── test_p1_shell.py       ← from this delivery
        ├── test_p2_panels.py      ← from this delivery
        ├── test_p3_p4_p5_combined.py  ← from this delivery
        └── test_p6_p7_p8_combined.py  ← from this delivery
```

---

## Step 2 — Install Dependencies

```bash
# Core test dependencies (needed for M1/M2 headless tests)
pip install pytest pytest-html pillow

# Additional for GUI tests (M3 smoke + GC)
pip install pyautogui pywin32

# App dependencies (already in requirements_v8.txt)
pip install -r requirements_v8.txt
```

---

## Step 3 — When to Run Which Script

This is the only decision you make. Run based on what you just finished.

```
After M1 (core/ extracted)    →  run_tests_M1.bat
After M2 (system/ extracted)  →  run_tests_M2.bat
After M3 (ui/ isolated)       →  Manual smoke only (no script)
After P1–P7 complete          →  run_tests_GC.bat
```

### M1 — After extracting `core/`

```cmd
run_tests_M1.bat
```

- Runs `tests/core/test_m1_core.py` only
- Headless — no display needed, runs in <5 seconds
- Tests: TC-M1-001 → TC-M1-010
- All must PASS before starting M2

### M2 — After extracting `system/`

```cmd
run_tests_M2.bat
```

- Runs `tests/system/test_m2_system.py` only
- Headless — no display needed, runs in <5 seconds
- Tests: TC-M2-001 → TC-M2-008
- All must PASS before starting M3

### M3 — After isolating `ui/` classes

No script. Run the app manually:

```cmd
python main.py
```

Then verify TC-M3-001 → TC-M3-006 by hand (see `Manual_QA_Tracker_v8.0.md`).
The app must behave identically to the original monolith.

### GC — After P1–P7 complete

```cmd
run_tests_GC.bat
```

- Runs `tests/ui/` test suite
- Requires display — app window opens and closes automatically
- Tests: TC-P1 → TC-P8 (62 automated cases)
- All must PASS before release
- Produces HTML report at `tests/reports/report_GCa.html`

---

## Step 4 — Reading Test Results

### Pass (nothing to do)

```
========================= 10 passed in 3.21s =========================
[PASS] M1 headless tests passed. Proceed to M2.
```

### Fail (fix before continuing)

```
FAILED tests/core/test_m1_core.py::TestSettingsIO::test_round_trip
========================= 1 failed, 9 passed in 3.44s =========================
[FAIL] M1 tests failed. Fix core/ extraction before continuing.
```

Open `tests/reports/report_M1.html` in a browser for the full error trace.

**Common M1 failure causes:**
- Missing import in `core/settings.py` (e.g., forgot `from pathlib import Path`)
- Function still references a global that wasn't moved (e.g., `SETTINGS_FILE` still in monolith only)
- `DEFAULT_SETTINGS` missing the new `"language": "en"` key

**Common M2 failure causes:**
- `HotkeyManager` references `_pynput_kb` which hasn't been imported in `system/hotkeys.py`
- `_PRESET_LABEL` dict not moved alongside `_preset_label()` function

**Common GC failure causes:**
- `btn_fullscreen` / `btn_region` attribute name changed — update `_set_shot_buttons()` call
- `_wm_acc_open` flag not set in `__init__`
- Module import path wrong in `conftest.py` — check `from ui.main_window import ScreenWatermarkApp`

---

## Step 5 — If a Test Needs Updating

The only reason to modify a test file is if a **widget attribute name** changed
during implementation (e.g., you named it `self.btn_fs` instead of `self.btn_fullscreen`).

Find the attribute reference in the test and update it to match your implementation.
Do **not** change the test logic or expected behavior — that is the spec.

Example fix:
```python
# Test expects:
assert widget_is_visible(app.btn_fullscreen)

# If you named it differently in main_window.py:
assert widget_is_visible(app.btn_fs)   # ← update only the attr name
```

Report any attribute name mismatches to PM so the spec can be updated.

---

## Step 6 — Submitting Results

After GC tests pass:

1. Attach `tests/reports/report_M1.html` — M1 milestone
2. Attach `tests/reports/report_M2.html` — M2 milestone
3. Attach `tests/reports/report_GCa.html` — GC
4. Complete manual cases in `Manual_QA_Tracker_v8.0.md` (QA team handles this)
5. All three reports + manual tracker sign-off = release approved

---

## Quick Reference

```
MILESTONE    COMMAND              TESTS          DISPLAY NEEDED
─────────────────────────────────────────────────────────────
M1           run_tests_M1.bat     TC-M1-001→010  No
M2           run_tests_M2.bat     TC-M2-001→008  No
M3           python main.py       TC-M3-001→006  Yes (manual)
GC           run_tests_GC.bat     TC-P1→P8 (62)  Yes (auto)
```
