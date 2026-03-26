@echo off
REM ============================================================
REM  run_tests_M2.bat — Phase M2 Headless Tests
REM  Run after: system/ extraction complete
REM  From project root: run_tests_M2.bat
REM ============================================================

echo.
echo  ScreenWatermark Pro v8.0 — M2 Headless Tests
echo  Scope: system/ extraction verification (TC-M2-001 to TC-M2-008)
echo  Requires: NO display, NO app window
echo  =====================================================
echo.

python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo [INSTALL] pip install pytest pytest-html
    pip install pytest pytest-html
)

if not exist "tests\reports" mkdir "tests\reports"

python -m pytest tests/system/ ^
    -v ^
    --tb=short ^
    -m headless ^
    --html=tests/reports/report_M2.html ^
    --self-contained-html

set EXIT_CODE=%errorlevel%
echo.
if %EXIT_CODE% == 0 (
    echo  [PASS] M2 headless tests passed. Proceed to M3.
) else (
    echo  [FAIL] M2 tests failed. Fix system/ extraction before continuing.
)
echo  Report: tests\reports\report_M2.html
exit /b %EXIT_CODE%
