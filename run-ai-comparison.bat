@echo off
REM AI 정확도 비교 시스템 실행 (프로젝트 루트에서)
echo.
echo ========================================
echo AI 정확도 비교 시스템
echo ========================================
echo.

REM 비교 디렉토리로 이동하여 실행
cd comparison
call run-comparison.bat

REM 다시 루트로 돌아오기
cd ..
