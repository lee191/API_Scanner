#!/bin/bash

# Shadow API Scanner 테스트 스크립트 (호스트 실행)

set -e

echo "========================================"
echo "Shadow API Scanner - 테스트 실행"
echo "========================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 1. Docker 테스트 앱 시작
echo -e "${YELLOW}[1/5] 테스트 앱 시작 중...${NC}"

# 기존 컨테이너 정리
docker rm -f vulnerable-test-app 2>/dev/null || true

# 이미지 빌드
docker build -t vulnerable-test-app:latest test-app

# 컨테이너 실행
docker run -d --name vulnerable-test-app -p 5000:5000 -e FLASK_ENV=development vulnerable-test-app:latest

echo -e "${GREEN}✓ 테스트 앱 시작 완료${NC}"
echo ""

# 2. 헬스체크 대기
echo -e "${YELLOW}[2/5] 테스트 앱 준비 대기 중...${NC}"
sleep 10
echo -e "${GREEN}✓ 테스트 앱 준비 완료${NC}"
echo ""

# 3. JavaScript 분석
echo -e "${YELLOW}[3/5] JavaScript 분석 중...${NC}"
if python main.py analyze test-app/static --base-url http://localhost:5000 --recursive; then
    echo -e "${GREEN}✓ JavaScript 분석 완료${NC}"
else
    echo -e "${YELLOW}경고: JavaScript 분석 실패${NC}"
fi
echo ""

# 4. 전체 스캔
echo -e "${YELLOW}[4/5] 전체 스캔 실행 중 (API 탐지 + 취약점 스캔)...${NC}"
if python main.py full-scan http://localhost:5000 --js-path test-app/static --scan-vulns --output output; then
    echo -e "${GREEN}✓ 전체 스캔 완료${NC}"
else
    echo -e "${YELLOW}경고: 전체 스캔 실패${NC}"
fi
echo ""

# 5. 결과 확인
echo -e "${YELLOW}[5/5] 스캔 결과 확인...${NC}"
if ls output/*.html 1> /dev/null 2>&1; then
    echo -e "${GREEN}✓ HTML 리포트 생성됨${NC}"
fi
if ls output/*.json 1> /dev/null 2>&1; then
    echo -e "${GREEN}✓ JSON 리포트 생성됨${NC}"
fi
if ls output/*.md 1> /dev/null 2>&1; then
    echo -e "${GREEN}✓ Markdown 리포트 생성됨${NC}"
fi
echo ""

echo "생성된 파일:"
ls -lh output/
echo ""

echo "========================================"
echo -e "${GREEN}테스트 완료!${NC}"
echo "========================================"
echo ""
echo -e "${CYAN}📊 결과 확인:${NC}"
echo "  - HTML 리포트: open output/*.html (Mac) 또는 xdg-open output/*.html (Linux)"
echo "  - JSON 리포트: cat output/full_scan_*.json | jq"
echo "  - Markdown: cat output/full_scan_*.md"
echo ""
echo -e "${CYAN}🌐 테스트 앱:${NC}"
echo "  - URL: http://localhost:5000"
echo "  - 로그 확인: docker logs vulnerable-test-app"
echo "  - 로그 실시간: docker logs -f vulnerable-test-app"
echo "  - 상태 확인: docker ps"
echo ""
echo -e "${CYAN}🧹 정리:${NC}"
echo "  - 테스트 앱 중지: docker stop vulnerable-test-app"
echo "  - 테스트 앱 삭제: docker rm vulnerable-test-app"
echo "  - 또는 실행: ./docker-stop.sh"
echo ""
