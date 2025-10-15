@echo off
chcp 65001 >nul
echo ========================================
echo AI 사용/미사용 스캔 비교 도구
echo ========================================
echo.

REM Move to project root
cd ..

REM Check if test app is running
echo [1/4] 테스트 앱 확인 중...
curl -s http://localhost:5000 >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] 테스트 앱이 실행되지 않았습니다.
    echo [*] start-test-app.bat을 먼저 실행해주세요.
    pause
    exit /b 1
)
echo [OK] 테스트 앱 실행 중
echo.

REM Check ground truth file
echo [2/4] Ground Truth 파일 확인...
if not exist ground_truth.json (
    echo [!] ground_truth.json 파일이 없습니다.
    if exist ground_truth_complete.json (
        echo [*] ground_truth_complete.json을 복사합니다...
        copy ground_truth_complete.json ground_truth.json
    ) else (
        echo [ERROR] Ground Truth 파일을 찾을 수 없습니다.
        pause
        exit /b 1
    )
)
echo [OK] Ground Truth 파일 존재
echo.

REM Ask user preference
echo [3/4] 실행 모드 선택
echo.
echo 1. 자동 스캔 + 비교 (권장, 시간: ~5-10분)
echo 2. 기존 결과만 비교 (빠름, 시간: ~10초)
echo 3. 메트릭만 빠르게 확인 (가장 빠름, 시간: ~5초)
echo.
set /p mode="모드 선택 (1/2/3): "

if "%mode%"=="1" (
    echo.
    echo [4/4] AI 사용/미사용 스캔 실행 및 비교 중...
    echo [*] 이 과정은 5-10분 정도 소요됩니다.
    echo.
    python comparison\compare_ai_accuracy.py
) else if "%mode%"=="2" (
    echo.
    echo [4/4] 기존 스캔 결과 비교 중...
    python comparison\compare_ai_accuracy.py --skip-scan
) else if "%mode%"=="3" (
    echo.
    echo [4/4] 메트릭 확인 중...
    python comparison\quick_compare.py --metrics-only
) else (
    echo [!] 잘못된 선택입니다.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 완료!
echo ========================================
echo.
echo 생성된 파일:
echo - 비교 리포트: output\accuracy_comparison\comparison_report_*.json
echo - 데이터베이스: data\scanner_with_ai.db, data\scanner_without_ai.db
echo.
pause
