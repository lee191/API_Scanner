# 🔍 Shadow API Scanner

> 웹 애플리케이션의 숨겨진 API를 탐색하고 분석하는 자동화 도구

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)
[![License](https://img.shields.io/badge/License-Educational-green.svg)](LICENSE)

## 📋 개요

Shadow API Scanner는 자동화된 API 탐색 도구입니다.

- 🔍 **Shadow API 자동 발견**: JavaScript 정적 분석 (Regex + AST 파싱) + AI 추론 (GPT-4o)
- 🤖 **AI 기반 분석**: 복잡한 패턴 인식 및 숨겨진 엔드포인트 추론
- �️ **재귀 크롤링**: 1-5단계 깊이 설정, 최대 200페이지 탐색
- 📊 **포괄적인 리포트**: JSON/HTML/Markdown 형식
- 🌐 **현대적인 Web UI**: Next.js 기반 대시보드
- 💾 **데이터베이스 통합**: 스캔 이력 및 프로젝트 관리

## 🚀 빠른 시작

### 📦 설치 가이드

**빠른 시작**: [QUICK_START.md](QUICK_START.md) (5분 가이드)  
**전체 가이드**: [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) (상세 설명 + 문제 해결)

```bash
# 1. 저장소 클론
git clone https://github.com/lee191/API_Scanner.git
cd API_Scanner

# 2. Python 가상환경 생성 (권장)
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Linux/macOS: source venv/bin/activate

# 3. Python 의존성 설치
pip install -r requirements.txt

# 4. 데이터베이스 초기화
python setup_db.py

# 5. OpenAI API 키 설정 (AI 분석 사용 시)
# Windows: $env:OPENAI_API_KEY = "sk-your-api-key"
# Linux/macOS: export OPENAI_API_KEY="sk-your-api-key"

# 6. Web UI 설정
cd web-ui
npm install
cd ..
```

### 🖥️ 서버 실행

#### Web UI 모드 (권장)
```bash
# Terminal 1: 백엔드 API 서버
python api_server.py

# Terminal 2: 프론트엔드 개발 서버
cd web-ui
npm run dev
```

브라우저에서 http://localhost:3000 접속

#### CLI 모드
```bash
# 기본 스캔
python main.py full-scan http://localhost:5000

# 고급 옵션
python main.py full-scan http://example.com \
  --ai \
  --bruteforce \
  --crawl-depth 3 \
  --max-pages 100 \
  --validate
```

## 📖 문서

| 문서 | 설명 |
|------|------|
| [🚀 QUICK_START.md](QUICK_START.md) | 5분 빠른 시작 가이드 |
| [📦 INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) | 완전한 설치 및 실행 가이드 (문제 해결 포함) |
| [📚 DOCUMENTATION.md](DOCUMENTATION.md) | 전체 프로젝트 문서 (아키텍처, API, 모듈) |
| [📊 ACCURACY_ANALYSIS_v2.md](ACCURACY_ANALYSIS_v2.md) | AI vs 정적 분석 정확도 비교 |
| [📋 PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md) | 프로젝트 개요 및 기술 스택 |

### 주요 내용
- ✅ 시스템 요구사항 및 설치 방법
- ✅ 단계별 설정 가이드 (백엔드/프론트엔드)
- ✅ 웹 UI 사용법 (프로젝트 생성 ~ 스캔 실행)
- ✅ CLI 명령어 및 옵션
- ✅ 크롤링 깊이 설정
- ✅ 테스트 앱 실행 방법
- ✅ 문제 해결 (포트 충돌, API 키, 패키지 오류 등)
- ✅ 아키텍처 및 모듈 상세 설명
- ✅ 데이터베이스 스키마
- ✅ AI 기능 활용법

## 🎯 주요 기능

### 🔍 API 탐색
- ✅ **JavaScript 정적 분석**: Regex + AST 파싱으로 엔드포인트 추출
- 🤖 **AI 기반 분석**: GPT-4o로 숨겨진 엔드포인트 추론
- 🕸️ **재귀 크롤링**: 1~5단계 깊이 설정 가능
- 🔍 **디렉토리 브루트포싱**: Wordlist 기반 숨겨진 경로 탐색
- 📡 **네트워크 트래픽 캡처**: mitmproxy 통합
- ✔️ **HTTP 검증**: 실제 엔드포인트 유효성 확인

###  리포팅 & 관리
- 📄 **다중 포맷**: JSON / HTML / Markdown
- 💾 **프로젝트 관리**: SQLite 데이터베이스
- � **통계 대시보드**: 실시간 스캔 모니터링
- � **고급 필터링**: 메서드/상태코드/탐지방법별 필터
- 📜 **스캔 히스토리**: 전체 스캔 기록 추적
- 🏷️ **AI 배지**: AI로만 발견된 엔드포인트 표시

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
  --ai
```

## 📊 예상 결과

테스트 앱 (test-app) 스캔 시:
- **엔드포인트**: 15+ 개 발견
- **Shadow APIs**: 5+ 개 탐지
- **AI 추론**: GPT-4o 기반 엔드포인트 분석
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

# OpenAI Configuration (AI 기능 사용 시 필수)
OPENAI_API_KEY=your-api-key-here

# AI Model Selection
# Options: gpt-4o (권장), gpt-4-turbo, gpt-4o-mini (비용 효율적)
AI_MODEL=gpt-4o

# AI Prompt Language
# Options: ko (한국어), en (English)
AI_PROMPT_LANGUAGE=ko
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
