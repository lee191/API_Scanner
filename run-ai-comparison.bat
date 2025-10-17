@echo off
chcp 65001 >nul
echo ============================================================
echo AI 사용/미사용 정확도 비교 실행
echo ============================================================
echo.

echo [1/3] 환경 확인 중...
echo   - Target URL: http://localhost:5000
echo   - Ground Truth: test-app\ground_truth.json
echo   - JS Path: test-app\static
echo.

echo [2/3] 비교 스크립트 실행 중...
python scripts\compare_ai_accuracy.py ^
    --target http://localhost:5000 ^
    --ground-truth test-app\ground_truth.json ^
    --js-path test-app\static

if errorlevel 1 (
    echo.
    echo [ERROR] 비교 실행 실패
    pause
    exit /b 1
)

echo.
echo [3/3] 완료!
echo 보고서 파일이 생성되었습니다: ai_accuracy_report_*.json
echo.
pause
