@echo off
REM Stop and remove E-Commerce vulnerable test app container

echo ========================================
echo Stopping Test App 2 (E-Commerce)
echo ========================================
echo.

echo [*] Stopping container...
docker stop vulnerable-test-app2 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Container was not running
)

echo [*] Removing container...
docker rm vulnerable-test-app2 2>nul
if %errorlevel% neq 0 (
    echo [WARNING] Container does not exist
)

echo.
echo [OK] Cleanup completed
echo.
