@echo off
REM Shadow API Scanner Test Script

echo ========================================
echo Shadow API Scanner - Test Execution
echo ========================================
echo.

echo [*] Preparing test environment...
echo.

REM 1. Start Docker test app
echo [1/5] Starting test app...

REM Clean up existing container
docker rm -f vulnerable-test-app 2>nul

REM Build image
docker build -t vulnerable-test-app:latest test-app
if %errorlevel% neq 0 (
    echo [ERROR] Docker image build failed
    exit /b 1
)

REM Run container
docker run -d --name vulnerable-test-app -p 5000:5000 -e FLASK_ENV=development vulnerable-test-app:latest
if %errorlevel% neq 0 (
    echo [ERROR] Docker container start failed
    exit /b 1
)
echo [OK] Test app started
echo.

REM 2. Wait for health check
echo [2/5] Waiting for test app to be ready...
timeout /t 10 /nobreak > nul
echo [OK] Test app ready
echo.

REM 3. JavaScript analysis
echo [3/5] Running JavaScript analysis...
python main.py analyze test-app\static --base-url http://localhost:5000 --recursive
if %errorlevel% neq 0 (
    echo [WARNING] JavaScript analysis failed
) else (
    echo [OK] JavaScript analysis completed
)
echo.

REM 4. Full scan
echo [4/5] Running full scan (API detection + vulnerability scan)...
python main.py full-scan http://localhost:5000 --js-path test-app\static --scan-vulns --output output
if %errorlevel% neq 0 (
    echo [WARNING] Full scan failed
) else (
    echo [OK] Full scan completed
)
echo.

REM 5. Check results
echo [5/5] Checking scan results...
if exist output\*.html (
    echo [OK] HTML report generated
)
if exist output\*.json (
    echo [OK] JSON report generated
)
if exist output\*.md (
    echo [OK] Markdown report generated
)
echo.

echo Generated files:
dir output\*.* /b
echo.

echo ========================================
echo Test Completed!
echo ========================================
echo.
echo Check Results:
echo   - HTML report: Open .html file in output\ folder
echo   - JSON report: type output\full_scan_*.json
echo   - Markdown: type output\full_scan_*.md
echo.
echo Test App:
echo   - URL: http://localhost:5000
echo   - View logs: docker logs vulnerable-test-app
echo   - Check status: docker ps
echo.
echo Cleanup:
echo   - Stop app: docker stop vulnerable-test-app
echo   - Remove app: docker rm vulnerable-test-app
echo   - Or run: stop-test-app.bat
echo.
pause
