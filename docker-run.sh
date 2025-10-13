#!/bin/bash

# Docker로 테스트 앱 실행 (docker compose 없이)

set -e

echo "========================================"
echo "취약한 테스트 앱 시작"
echo "========================================"
echo ""

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# 기존 컨테이너 정리
echo -e "${YELLOW}[*] 기존 컨테이너 확인 중...${NC}"
if docker ps -a | grep -q "vulnerable-test-app"; then
    echo -e "${YELLOW}[*] 기존 컨테이너 제거 중...${NC}"
    docker rm -f vulnerable-test-app
fi

# 이미지 빌드
echo -e "${YELLOW}[*] Docker 이미지 빌드 중...${NC}"
docker build -t vulnerable-test-app:latest test-app
echo -e "${GREEN}✓ 이미지 빌드 완료${NC}"
echo ""

# 컨테이너 실행
echo -e "${YELLOW}[*] 컨테이너 시작 중...${NC}"
docker run -d \
    --name vulnerable-test-app \
    -p 5000:5000 \
    -e FLASK_ENV=development \
    vulnerable-test-app:latest

echo -e "${GREEN}✓ 컨테이너 시작 완료${NC}"
echo ""

# 준비 대기
echo -e "${YELLOW}[*] 앱 준비 대기 중... (5초)${NC}"
sleep 5
echo ""

# 상태 확인
echo -e "${YELLOW}[*] 컨테이너 상태:${NC}"
docker ps | grep "vulnerable-test-app"
echo ""

# 접속 테스트
echo -e "${YELLOW}[*] 접속 테스트...${NC}"
if curl -s http://localhost:5000 > /dev/null; then
    echo -e "${GREEN}✓ 테스트 앱 정상 작동${NC}"
else
    echo -e "${YELLOW}경고: 접속 테스트 실패${NC}"
fi
echo ""

echo "========================================"
echo -e "${GREEN}테스트 앱 시작 완료!${NC}"
echo "========================================"
echo ""
echo -e "${CYAN}접속 정보:${NC}"
echo "  - URL: http://localhost:5000"
echo "  - 컨테이너: vulnerable-test-app"
echo ""
echo -e "${CYAN}명령어:${NC}"
echo "  - 로그 확인: docker logs vulnerable-test-app"
echo "  - 로그 실시간: docker logs -f vulnerable-test-app"
echo "  - 상태 확인: docker ps"
echo "  - 중지: docker stop vulnerable-test-app"
echo "  - 삭제: docker rm -f vulnerable-test-app"
echo ""
