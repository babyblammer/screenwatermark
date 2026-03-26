# ScreenWatermark Pro

A screenshot utility that applies watermarks and timestamps to captured images.
Supports fullscreen and region capture, system tray operation, and persistent history.

**Current version:** v4.0.0 (in development — tkinter → customtkinter migration)
**Stable release:** v3.9.1f HF1

---

## Project Structure

```
screenwatermark/
├── core/          Pure logic — settings, history, render, clipboard, cache
├── system/        OS coupling — hotkeys, startup, IPC, tray
├── ui/            UI layer — CTk windows and widget components
├── tests/         Automated test suite (pytest)
└── docs/          Specification and QA documents
```

Dependency rule: `core/` and `system/` never import from `ui/`.

---

## Setup

```bash
pip install -r requirements_v8.txt
python main.py
```

---

## Running Tests

```bash
# After core/ extraction (M1)
run_tests_M1.bat

# After system/ extraction (M2)
run_tests_M2.bat

# Gold Candidate — full GUI suite
run_tests_GC.bat
```

See `docs/Programmer_Test_Setup_Guide.md` for full instructions.

---

## Documentation

| Doc | Purpose |
|---|---|
| `docs/Modular_Architecture_Proposal_v8.0.md` | Why modular first, structure rationale |
| `docs/Migration_Plan_v8.0.md` | Phase plan M1–M3 + P0–P7 + GC |
| `docs/Implementation_Guideline_v8.0.md` | Step-by-step code for programmer |
| `docs/UI_UX_Spec_v8.0.md` | Widget specs, palette, layout |
| `docs/Behavior_Addendum_v8.0.md` | Accordion/scroll/history exact behavior + stubs |
| `docs/QA_TestCase_v8.0.md` | All 106 test cases |
| `docs/Automation_Test_Strategy_v8.0.md` | Coverage map, test architecture |
| `docs/Manual_QA_Tracker_v8.0.md` | 26 manual-only cases |
| `docs/Programmer_Test_Setup_Guide.md` | Where to place files, when to run which script |
| `mockup/mockup_SWPro_v8.0_R2.html` | Interactive UI mockup |

---

## Dependencies

```
pillow>=10.0
mss>=9.0
pystray>=0.19
pynput>=1.7
pywin32>=306
customtkinter>=5.2.2
pywinstyles>=1.8
```
