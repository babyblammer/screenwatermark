@echo off
REM ============================================================
REM  run_tests_M1.bat — Phase M1 Headless Tests
REM  Run after: core/ extraction complete
REM  From project root: run_tests_M1.bat
REM ============================================================

echo.
echo  ScreenWatermark Pro v8.0 — M1 Headless Tests
echo  Scope: core/ extraction verification (TC-M1-001 to TC-M1-010)
echo  Requires: NO display, NO app window
echo  =====================================================
echo.

python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] pip install pytest pytest-html pillow
    pip install pytest pytest-html pillow
)

if not exist "tests\reports" mkdir "tests\reports"

python -m pytest tests/core/ ^
    -v ^
    --tb=short ^
    -m headless ^
    --html=tests/reports/report_M1.html ^
    --self-contained-html

set EXIT_CODE=%errorlevel%
echo.
if %EXIT_CODE% == 0 (
    echo  [PASS] M1 headless tests passed. Proceed to M2.
) else (
    echo  [FAIL] M1 tests failed. Fix core/ extraction before continuing.
)
echo  Report: tests\reports\report_M1.html
exit /b %EXIT_CODE%
