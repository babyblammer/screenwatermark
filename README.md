# ScreenWatermark Pro

A screenshot utility that applies watermarks and timestamps to captured images.
Supports fullscreen and region capture, system tray operation, and persistent history.

**Current version:** v4.1.0a

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

See [Test Setup](docs/Programmer_Test_Setup_Guide.md) for full instructions.

---

## Documentation

| Doc | Purpose |
|---|---|
| [Testcase QA](docs/QA_TestCase_v8.0.md) | All 106 test cases |
| [Automation Test](docs/Automation_Test_Strategy_v8.0.md) | Coverage map, test architecture |
| [Manual QA Tracker](docs/Manual_QA_Tracker_v8.0.md) | 26 manual-only cases |
| [Programmer Guide](docs/Programmer_Test_Setup_Guide.md) | Where to place files, when to run which script |

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
