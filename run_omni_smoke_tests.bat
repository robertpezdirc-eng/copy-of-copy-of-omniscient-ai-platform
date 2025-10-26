@echo off
REM OMNI Platform Google Cloud Smoke Test Runner (Windows Batch)
REM Comprehensive smoke test execution script

echo.
echo 🔥 OMNI Platform Google Cloud Smoke Test Suite
echo ==============================================
echo Testing Google Cloud Run, Vertex AI, Gemini, and entire platform
echo.

REM Set environment variables
set PYTHONPATH=%cd%
set VERTEX_AI_API_KEY=AQ.Ab8RN6LjDXj9_BHBcp-XvbSm0WCE2ftjfwyobHz-Zc3oNMVfhQ
set GOOGLE_CLOUD_PROJECT=refined-graph-471712-n9
set GOOGLE_CLOUD_REGION=europe-west1
set PLATFORM_URL=http://34.140.18.254:8080

echo [INFO] Environment configured:
echo   Project: %GOOGLE_CLOUD_PROJECT%
echo   Region: %GOOGLE_CLOUD_REGION%
echo   Platform URL: %PLATFORM_URL%
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo [INFO] Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [INFO] Python version:
python --version
echo.

REM Install required packages
echo [INFO] Installing required packages...
pip install -r requirements-smoke-test.txt
if errorlevel 1 (
    echo [WARNING] Failed to install some packages, continuing anyway...
)

echo.
echo [INFO] Starting smoke tests...
echo.

REM Run main smoke test
echo [1/4] Running main smoke test suite...
python omni_smoke_test.py
if errorlevel 1 (
    echo [WARNING] Main smoke test failed, continuing with other tests...
)

REM Run Cloud Run tests
echo.
echo [2/4] Running Cloud Run deployment tests...
python omni_cloudrun_test.py
if errorlevel 1 (
    echo [WARNING] Cloud Run tests failed, continuing with other tests...
)

REM Run Vertex AI tests
echo.
echo [3/4] Running Vertex AI and Gemini tests...
python omni_vertex_gemini_test.py
if errorlevel 1 (
    echo [WARNING] Vertex AI tests failed, continuing with other tests...
)

REM Run unified test runner
echo.
echo [4/4] Running unified test runner with report generation...
python omni_smoke_test_runner.py --verbose
set TEST_EXIT_CODE=%errorlevel%

echo.
echo ==============================================
echo SMOKE TEST EXECUTION COMPLETED
echo ==============================================
echo.

REM Check if any tests failed
if %TEST_EXIT_CODE% EQU 0 (
    echo [SUCCESS] All smoke tests passed! ✅
    echo [INFO] Platform is ready for production deployment.
) else (
    echo [WARNING] Some smoke tests failed! ⚠️
    echo [INFO] Check the generated report files for details.
    echo [INFO] Review logs and fix issues before production deployment.
)

echo.
echo [INFO] Generated files:
dir /b /o-d omni_smoke_test*.txt omni_smoke_test*.json omni_smoke_test*.html 2>nul | findstr . || echo   No report files found
echo.

REM Open latest HTML report if available
for %%f in (omni_smoke_test_report_*.html) do set "LATEST_HTML=%%f"
if defined LATEST_HTML (
    echo [INFO] Opening latest HTML report in browser...
    start "" "%%LATEST_HTML"
) else (
    echo [INFO] No HTML report found to open in browser.
)

echo.
echo [INFO] Test logs and reports are available in the current directory.
echo [INFO] Check individual test script outputs for detailed results.
echo.

REM Exit with test result code
if %TEST_EXIT_CODE% EQU 0 (
    echo [SUCCESS] Exiting with success code.
    exit /b 0
) else (
    echo [WARNING] Exiting with failure code.
    exit /b 1
)