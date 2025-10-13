#!/bin/bash

# Docker 테스트 앱 중지 및 삭제

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "테스트 앱 중지"
echo "========================================"
echo ""

echo -e "${YELLOW}[*] 컨테이너 중지 중...${NC}"
docker stop vulnerable-test-app 2>/dev/null || echo -e "${YELLOW}경고: 컨테이너가 실행 중이 아닙니다${NC}"

echo -e "${YELLOW}[*] 컨테이너 삭제 중...${NC}"
docker rm vulnerable-test-app 2>/dev/null || echo -e "${YELLOW}경고: 컨테이너가 존재하지 않습니다${NC}"

echo ""
echo -e "${GREEN}✓ 정리 완료${NC}"
echo ""
