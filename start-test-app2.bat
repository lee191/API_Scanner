@echo off
REM Start E-Commerce vulnerable test app with Docker
REM 포트 5002에서 실행

echo ========================================
echo Starting Test App 2 (E-Commerce)
echo ========================================
echo.

REM Clean up existing container
echo [*] Cleaning up existing container...
docker rm -f vulnerable-test-app2 2>nul

REM Build image
echo [*] Building Docker image...
docker build -t vulnerable-test-app2:latest test-app2
if %errorlevel% neq 0 (
    echo [ERROR] Image build failed
    exit /b 1
)
echo [OK] Image built successfully
echo.

REM Run container
echo [*] Starting container...
docker run -d --name vulnerable-test-app2 -p 5002:5002 -e FLASK_ENV=development vulnerable-test-app2:latest
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
docker ps | findstr vulnerable-test-app2
echo.

echo ========================================
echo Test App 2 Started Successfully!
echo ========================================
echo.
echo URL: http://localhost:5002
echo Container: vulnerable-test-app2
echo Type: E-Commerce Vulnerable App
echo.
echo Endpoints:
echo   - Public API: /api/v2/orders, /api/v2/reviews, /api/v2/coupons/validate
echo   - Shadow API: /api/internal/payments/all, /api/internal/admin/*, etc.
echo.
echo Commands:
echo   - View logs: docker logs vulnerable-test-app2
echo   - Stop: docker stop vulnerable-test-app2
echo   - Remove: docker rm vulnerable-test-app2
echo.
