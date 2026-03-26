@echo off
REM ============================================================
REM  run_tests_GC.bat — Gold Candidate Full Test Suite
REM  Run at GC milestone ONLY (all phases P1-P8)
REM  From project root: run_tests_GC.bat
REM
REM  Prerequisites before running this script:
REM    1. run_tests_M1.bat PASSED
REM    2. run_tests_M2.bat PASSED
REM    3. M3 smoke (manual) PASSED
REM    4. P1-P7 builds complete
REM ============================================================

echo.
echo  ScreenWatermark Pro v8.0 — Gold Candidate Test Suite
echo  Scope: TC-P1 through TC-P8 (62 automated GUI cases)
echo  Requires: Display + modular package complete
echo  =====================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH
    exit /b 1
)

python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] Installing test dependencies...
    pip install pytest pytest-html pyautogui pillow pywin32
)

if not exist "tests\reports" mkdir "tests\reports"
if not exist "tests\assets"  mkdir "tests\assets"

REM Generate test watermark asset
python -c "from PIL import Image; from pathlib import Path; p=Path('tests/assets'); p.mkdir(parents=True,exist_ok=True); img=Image.new('RGBA',(200,100),(255,0,0,180)); img.save(p/'test_watermark.png'); print('[OK] Test watermark created')"

echo.
echo [RUN] Starting GUI test suite...
echo       (App window will open and close automatically)
echo.

python -m pytest tests/ui/ ^
    -v ^
    --tb=short ^
    --html=tests/reports/report_GCa.html ^
    --self-contained-html ^
    -x

set EXIT_CODE=%errorlevel%
echo.
if %EXIT_CODE% == 0 (
    echo  [PASS] All automated GC tests passed.
    echo.
    echo  Next: Complete 26 manual cases in Manual_QA_Tracker_v8.0.md
    echo  Report: tests\reports\report_GCa.html
) else (
    echo  [FAIL] Tests failed. Release BLOCKED until fixed.
    echo  Report: tests\reports\report_GCa.html
)
exit /b %EXIT_CODE%
