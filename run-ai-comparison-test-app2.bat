@echo off
REM AI 정확도 비교 - test-app2 (E-Commerce)
REM 정적 분석, AI 분석, 정적+AI 분석의 정확도를 Ground Truth와 비교

echo ========================================
echo AI Accuracy Comparison - test-app2
echo ========================================
echo.

REM 환경 확인
echo [*] Checking environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH
    exit /b 1
)

echo [*] Target: http://localhost:5002
echo [*] Ground Truth: test-app2\ground_truth.json
echo [*] JS Path: test-app2\static
echo.

REM 서버 실행 확인
echo [*] Checking if test-app2 is running on port 5002...
curl -s http://localhost:5002 >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [WARNING] test-app2 is not running on port 5002!
    echo [INFO] Please start test-app2 first:
    echo [INFO]   start-test-app2.bat
    echo.
    choice /C YN /M "Do you want to continue anyway"
    if errorlevel 2 exit /b 1
)

echo.
echo ========================================
echo Starting AI Accuracy Comparison
echo ========================================
echo.

REM 비교 실행
python scripts\compare_ai_accuracy.py ^
  --target http://localhost:5002 ^
  --ground-truth test-app2\ground_truth.json ^
  --js-path test-app2\static

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Comparison failed
    exit /b 1
)

echo.
echo ========================================
echo Comparison Completed Successfully!
echo ========================================
echo.
echo Results saved to: ai_accuracy_report_[timestamp].json
echo.

pause
