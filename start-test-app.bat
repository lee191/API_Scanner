@echo off
REM Start vulnerable test app with Docker

echo ========================================
echo Starting Test App
echo ========================================
echo.

REM Clean up existing container
echo [*] Cleaning up existing container...
docker rm -f vulnerable-test-app 2>nul

REM Build image
echo [*] Building Docker image...
docker build -t vulnerable-test-app:latest test-app
if %errorlevel% neq 0 (
    echo [ERROR] Image build failed
    exit /b 1
)
echo [OK] Image built successfully
echo.

REM Run container
echo [*] Starting container...
docker run -d --name vulnerable-test-app -p 5000:5000 -e FLASK_ENV=development vulnerable-test-app:latest
if %errorlevel% neq 0 (
    echo [ERROR] Container start failed
    exit /b 1
)
echo [OK] Container started successfully
echo.

REM Wait for app
echo [*] Waiting for app to be ready (5 seconds)...
timeout /t 5 /nobreak > nul
echo.

REM Check status
echo [*] Container status:
docker ps | findstr vulnerable-test-app
echo.

echo ========================================
echo Test App Started Successfully!
echo ========================================
echo.
echo URL: http://localhost:5000
echo Container: vulnerable-test-app
echo.
echo Commands:
echo   - View logs: docker logs vulnerable-test-app
echo   - Stop: docker stop vulnerable-test-app
echo   - Remove: docker rm vulnerable-test-app
echo.
