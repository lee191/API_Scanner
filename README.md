# 🔍 Shadow API Scanner

> 웹 애플리케이션의 숨겨진 API를 탐색하고 보안 취약점을 분석하는 모의 침투 테스트 도구

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-Educational-green.svg)](LICENSE)

## 📋 개요

Shadow API Scanner는 자동화된 API 탐색 및 보안 취약점 분석 도구입니다.

- 🔍 **Shadow API 자동 발견**: JavaScript 정적 분석 + AI 기반 패턴 인식
- 🛡️ **OWASP Top 10 스캔**: SQL Injection, XSS, 인증 누락 등
- 📊 **포괄적인 리포트**: JSON/HTML/Markdown 형식
- 🌐 **현대적인 Web UI**: Next.js 기반 대시보드
- 💾 **데이터베이스 통합**: 스캔 이력 및 프로젝트 관리

## 🚀 빠른 시작

### 설치

```bash
# 저장소 클론
git clone <repository-url>
cd API_Scanner

# Python 의존성 설치
pip install -r requirements.txt

# 데이터베이스 초기화
python setup_db.py

# (선택) Web UI 설정
cd web-ui
npm install
```

### 사용 방법

#### CLI 모드
```bash
# 전체 스캔
python main.py full-scan http://localhost:5000 \
  --js-path ./static \
  --scan-vulns \
  --bruteforce
```

#### Web UI 모드
```bash
# Terminal 1: API 서버
python api_server.py

# Terminal 2: Web UI
cd web-ui
npm run dev
```

브라우저에서 http://localhost:3000 접속

## 📖 문서

**완전한 문서는 [DOCUMENTATION.md](DOCUMENTATION.md)를 참조하세요.**

포함 내용:
- 상세 설치 가이드
- 아키텍처 및 모듈 설명
- API 참조
- AI 기능 활용법
- 데이터베이스 스키마
- 테스트 가이드
- 문제 해결 방법

## 🎯 주요 기능

### API 탐색
- ✅ JavaScript 정적 분석 (Regex + AST)
- ✅ AI 기반 고급 패턴 인식 (OpenAI GPT)
- ✅ 디렉토리 브루트포싱 (Wordlist 기반)
- ✅ 네트워크 트래픽 캡처 (mitmproxy)

### 보안 취약점 스캔
- 🔴 SQL Injection (CWE-89)
- 🔴 XSS (CWE-79)
- 🟠 Missing Authentication (CWE-306)
- 🟠 CORS Misconfiguration (CWE-942)
- 🟠 Sensitive Data Exposure (CWE-200)
- 🟡 Missing Rate Limiting (CWE-770)

### 리포팅 및 PoC 생성
- 📄 JSON (구조화된 데이터)
- 📄 HTML (시각화된 대시보드)
- 📄 Markdown (문서화 친화적)
- 🎨 **선택적 PoC 코드 생성** (AI 기반 / 템플릿 기반)
  - ✨ **NEW**: Web UI에서 버튼 클릭으로 원하는 취약점만 PoC 생성
  - 💰 비용 효율적: 필요한 취약점만 선택적으로 생성
  - 🚀 빠른 생성: 개별 생성 (3-5초) 또는 일괄 생성
  - 📋 코드 복사: 생성된 PoC 즉시 복사 가능

## 🧪 테스트

```bash
# 테스트 앱 시작 (Docker)
./docker-run.sh        # Linux/Mac
docker-run.bat         # Windows

# 자동 통합 테스트
./test-scripts/run-test.sh      # Linux/Mac
test-scripts\run-test.bat       # Windows

# 수동 테스트
python main.py full-scan http://localhost:5000 \
  --js-path test-app/static \
  --scan-vulns
```

## 📊 예상 결과

테스트 앱 (test-app) 스캔 시:
- **엔드포인트**: 15+ 개 발견
- **Shadow APIs**: 5+ 개 탐지
- **취약점**: 20+ 개 발견
  - Critical: 2+ (SQL Injection)
  - High: 8+ (인증 누락, XSS 등)
  - Medium: 10+ (Rate Limiting 등)
- **실행 시간**: 60-90초

## 🏗️ 프로젝트 구조

```
API_Scanner/
├── main.py                 # CLI 진입점
├── api_server.py           # Flask API 서버
├── setup_db.py             # 데이터베이스 초기화
├── DOCUMENTATION.md        # 📖 완전한 문서
├── src/
│   ├── proxy/              # 프록시 캡처
│   ├── crawler/            # JS 수집 + 브루트포싱
│   ├── analyzer/           # JS 분석 (Regex + AI)
│   ├── scanner/            # 취약점 스캐너
│   ├── reporter/           # 리포트 생성
│   ├── database/           # DB 모델 및 Repository
│   └── utils/              # 공통 유틸리티
├── web-ui/                 # Next.js Web UI
├── test-app/               # 취약한 테스트 앱
├── test-scripts/           # 통합 테스트 스크립트
├── config/                 # 설정 파일
├── output/                 # 리포트 출력 (gitignored)
└── data/                   # 데이터베이스 파일 (gitignored)
```

## ⚙️ 설정

### 환경 변수 (.env)
```bash
# Database
DATABASE_URL=sqlite:///data/scanner.db

# OpenAI (선택)
OPENAI_API_KEY=sk-your-key-here
AI_ANALYSIS_ENABLED=true
```

### 설정 파일 (config/config.yaml)
```yaml
scanner:
  timeout: 10
  checks:
    - authentication
    - sql_injection
    - xss
    - cors
```

## 🤝 기여

버그 리포트, 기능 제안, 풀 리퀘스트를 환영합니다!

## 🔒 법적 고지사항

**⚠️ 중요: 이 도구는 방어적 보안 목적으로만 사용되어야 합니다.**

- ✅ 자신이 소유하거나 명시적 허가를 받은 시스템에만 사용
- ✅ 모의 침투 테스트 및 보안 평가 목적
- ❌ 무단 접근, 데이터 탈취, 악의적 목적 사용 금지

사용자는 이 도구의 사용으로 인한 모든 법적 책임을 집니다.

## 📧 연락처

- 📖 완전한 문서: [DOCUMENTATION.md](DOCUMENTATION.md)
- 🐛 Issues: <repository-url>/issues
- 🔒 Security: <security-email>

---

**Shadow API Scanner** - 더 안전한 웹 애플리케이션을 위하여 🛡️

**© 2024-2025 Shadow API Scanner Team**
