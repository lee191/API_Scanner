# 🔍 Shadow API Scanner - 완전 가이드

> 웹 애플리케이션의 숨겨진/문서화되지 않은 API를 탐색하고 보안 취약점을 분석하는 모의 침투 테스트 도구

**버전**: 2.0  
**최종 업데이트**: 2025-10-14

---

## 📑 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [주요 기능](#2-주요-기능)
3. [아키텍처](#3-아키텍처)
4. [설치 및 설정](#4-설치-및-설정)
5. [사용 방법](#5-사용-방법)
6. [웹 UI](#6-웹-ui)
7. [AI 기능](#7-ai-기능)
8. [데이터베이스](#8-데이터베이스)
9. [테스트 가이드](#9-테스트-가이드)
10. [개발 가이드](#10-개발-가이드)
11. [문제 해결](#11-문제-해결)
12. [법적 고지](#12-법적-고지)

---

## 1. 프로젝트 개요

### 1.1 목적
Shadow API Scanner는 다음을 위한 방어적 보안 도구입니다:
- 📡 숨겨진(Shadow) API 엔드포인트 자동 발견
- 🛡️ OWASP Top 10 기반 보안 취약점 탐지
- 📊 포괄적인 보안 리포트 생성
- 🎯 모의 침투 테스트 및 보안 평가 지원

### 1.2 핵심 가치
- **자동화**: JavaScript 정적 분석으로 API 자동 수집
- **포괄성**: 프록시 캡처 + JS 분석 + 브루트포싱
- **정확성**: AI 기반 고급 패턴 인식
- **실용성**: CLI + Web UI 모두 지원
- **확장성**: 데이터베이스 기반 스캔 이력 관리

---

## 2. 주요 기능

### 2.1 API 탐색
- ✅ **네트워크 트래픽 분석**: mitmproxy 기반 HTTP/HTTPS 캡처
- ✅ **JavaScript 정적 분석**: fetch, axios, XMLHttpRequest 패턴 탐지
- ✅ **디렉토리 브루트포싱**: wordlist 기반 숨겨진 경로 발견
- ✅ **AI 기반 분석**: OpenAI GPT를 통한 고급 엔드포인트 추출

### 2.2 보안 취약점 스캔
| 취약점 유형 | 심각도 | CWE | 탐지 방법 |
|------------|--------|-----|----------|
| SQL Injection | 🔴 CRITICAL | CWE-89 | 에러 메시지 기반 |
| Missing Authentication | 🟠 HIGH | CWE-306 | 인증 없는 200 응답 |
| CORS Misconfiguration | 🟠 HIGH | CWE-942 | 헤더 검증 |
| XSS | 🟠 HIGH | CWE-79 | 스크립트 반사 |
| Sensitive Data Exposure | 🟠 HIGH | CWE-200 | 패턴 매칭 |
| Insecure Authentication | 🟠 HIGH | CWE-319 | URL 파라미터 검사 |
| Missing Rate Limiting | 🟡 MEDIUM | CWE-770 | 버스트 요청 |

### 2.3 리포트 생성
- 📄 **JSON**: 구조화된 데이터 (CI/CD 통합용)
- 📄 **HTML**: 시각화된 대시보드 (브라우저 표시)
- 📄 **Markdown**: 문서화 친화적 (Git, Wiki)

### 2.4 웹 인터페이스
- 🌐 Next.js 기반 현대적 UI
- 📊 실시간 스캔 진행률 표시
- 📈 통계 대시보드 및 시각화
- 🗂️ 스캔 이력 관리
- 🔄 프로젝트 단위 스캔 관리

---

## 3. 아키텍처

### 3.1 전체 구조

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Web UI    │─────▶│  Flask API   │─────▶│  Database   │
│  (Next.js)  │      │   Server     │      │ (SQLite/PG) │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  Python CLI  │
                     │    Scanner   │
                     └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
 ┌────────────┐      ┌────────────┐     ┌────────────┐
 │  Crawler   │      │  Analyzer  │     │   Scanner  │
 │  (JS수집)  │      │ (엔드포인트)│     │  (취약점)  │
 └────────────┘      └────────────┘     └────────────┘
```

### 3.2 파이프라인 플로우

```
1. Collection (수집)
   ├─ Proxy Capture (mitmproxy)
   ├─ JS File Discovery (크롤링)
   └─ Directory Bruteforcing (wordlist)
        ↓
2. Analysis (분석)
   ├─ Regex Pattern Matching
   ├─ AST Parsing (esprima)
   └─ AI Analysis (OpenAI GPT)
        ↓
3. Scanning (스캔)
   ├─ Authentication Checks
   ├─ Injection Tests (SQL, XSS)
   ├─ Configuration Tests (CORS)
   └─ Rate Limiting Tests
        ↓
4. Reporting (리포트)
   ├─ JSON Serialization
   ├─ HTML Template Rendering
   └─ Markdown Formatting
```

### 3.3 모듈 구성

```
src/
├── proxy/              # 프록시 서버 (mitmproxy)
│   └── capture.py
├── crawler/            # JS 파일 수집 및 브루트포싱
│   ├── js_collector.py
│   └── directory_bruteforcer.py
├── analyzer/           # JavaScript 분석
│   ├── js_analyzer.py        # Regex + AST 분석
│   ├── endpoint_collector.py # 엔드포인트 수집
│   └── ai_analyzer.py        # AI 기반 분석
├── scanner/            # 취약점 스캐너
│   └── vulnerability_scanner.py
├── reporter/           # 리포트 생성
│   └── report_generator.py
├── database/           # 데이터베이스 (신규)
│   ├── models.py           # SQLAlchemy 모델
│   ├── connection.py       # DB 연결 관리
│   └── repository.py       # CRUD 작업
└── utils/              # 공통 유틸리티
    ├── models.py           # Pydantic 모델
    └── config.py           # 설정 로더

api_server.py           # Flask REST API 서버
main.py                 # CLI 진입점
```

### 3.4 데이터 모델

#### Pydantic 모델 (`src/utils/models.py`)
```python
APIEndpoint:
  - url: str
  - method: HTTPMethod
  - parameters: Dict
  - headers: Dict
  - poc_code: Optional[str]  # PoC 코드
  - source: str  # 'proxy', 'js_analysis', 'bruteforce'

Vulnerability:
  - type: str
  - level: VulnerabilityLevel
  - endpoint: str
  - description: str
  - evidence: str
  - recommendation: str
  - poc_code: Optional[str]  # 악용 PoC
  - cwe_id: Optional[str]

ScanResult:
  - target: str
  - endpoints: List[APIEndpoint]
  - vulnerabilities: List[Vulnerability]
  - discovered_paths: List[Dict]  # 브루트포싱 경로
  - statistics: Dict[str, int]
```

#### SQLAlchemy 모델 (`src/database/models.py`)
```python
Project:
  - id, project_id
  - name, description
  - created_at, updated_at
  - scans (relationship)

Scan:
  - id, scan_id
  - target_url, js_path
  - status, progress, message
  - scan_vulns, ai_enabled, bruteforce_enabled
  - statistics (total_endpoints, shadow_apis, etc.)
  - output_path
  - endpoints, vulnerabilities, discovered_paths (relationships)

Endpoint:
  - id, scan_id
  - url, method, is_shadow_api
  - parameters, headers
  - poc_code

Vulnerability:
  - id, scan_id
  - type, level
  - description, evidence, recommendation
  - poc_code, cwe_id

DiscoveredPath:  # 신규
  - id, scan_id
  - path, status_code
  - content_length, content_type
```

---

## 4. 설치 및 설정

### 4.1 시스템 요구사항
- **Python**: 3.8 이상
- **Node.js**: 18 이상 (Web UI용)
- **Docker**: 테스트 환경용 (선택)
- **PostgreSQL**: 프로덕션 DB용 (선택, SQLite 기본)

### 4.2 Python 환경 설정

```bash
# 1. 저장소 클론
git clone <repository-url>
cd API_Scanner

# 2. 가상환경 생성 (권장)
python -m venv venv

# 활성화
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. Playwright 설치 (선택)
playwright install
```

### 4.3 데이터베이스 설정

```bash
# 데이터베이스 초기화
python setup_db.py

# 대화형 프롬프트:
# 1. PostgreSQL 연결 테스트 (선택)
# 2. 기존 테이블 삭제? (y/N)
# 3. 새 테이블 생성

# 마이그레이션 (discovered_paths 추가)
python migrate_discovered_paths.py
```

### 4.4 환경 변수 설정

`.env` 파일 생성:
```bash
cp .env.example .env
```

`.env` 파일 편집:
```bash
# Database (선택)
DATABASE_URL=sqlite:///data/scanner.db  # 기본
# DATABASE_URL=postgresql://user:pass@localhost:5432/shadow_api_scanner

# OpenAI API (선택)
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
AI_ANALYSIS_ENABLED=true
AI_MAX_TOKENS=8000
```

### 4.5 Web UI 설정

```bash
cd web-ui

# 의존성 설치
npm install

# 환경 변수 설정
cp .env.example .env.local

# .env.local 편집
NEXT_PUBLIC_API_URL=http://localhost:5001
```

---

## 5. 사용 방법

### 5.1 CLI 모드

#### 5.1.1 JavaScript 분석만
```bash
# 단일 파일
python main.py analyze app.js --base-url https://example.com

# 디렉토리 (재귀)
python main.py analyze ./static --base-url https://example.com --recursive
```

#### 5.1.2 전체 스캔 (JS + 취약점)
```bash
python main.py full-scan https://example.com \
  --js-path ./javascript \
  --scan-vulns \
  --output ./reports
```

**주요 옵션:**
- `--js-path`: JavaScript 파일/디렉토리 경로
- `--scan-vulns`: 취약점 스캔 수행 (기본: true)
- `--no-scan-vulns`: 취약점 스캔 건너뛰기
- `--bruteforce`: 디렉토리 브루트포싱 활성화
- `--output`: 리포트 출력 디렉토리
- `--ai-enabled`: AI 분석 활성화

#### 5.1.3 프록시 모드
```bash
python main.py proxy --host 127.0.0.1 --port 8080
```

브라우저 프록시 설정:
- 호스트: 127.0.0.1
- 포트: 8080
- HTTPS 프록시 활성화

### 5.2 API 서버 + Web UI 모드

#### 5.2.1 Flask API 서버 시작
```bash
python api_server.py
# 실행: http://localhost:5001
```

**주요 API 엔드포인트:**
```
POST   /api/scan                  # 스캔 시작
GET    /api/status/<scan_id>      # 스캔 상태/결과
GET    /api/history               # 스캔 이력
DELETE /api/scan/<scan_id>        # 스캔 삭제
GET    /api/projects              # 프로젝트 목록
POST   /api/projects              # 프로젝트 생성
GET    /api/projects/<id>         # 프로젝트 상세
```

#### 5.2.2 Web UI 시작
```bash
cd web-ui
npm run dev
# 실행: http://localhost:3000
```

**Web UI 기능:**
1. **Scan 탭**: 새 스캔 시작
2. **Projects 탭**: 프로젝트 관리
3. **History 탭**: 스캔 이력 조회
4. **Dashboard 탭**: 통계 및 요약

### 5.3 콘솔 출력 예시

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              🔍 Shadow API Scanner v2.0                  ║
║         Penetration Testing Tool for API Discovery       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

[*] 전체 스캔 시작: https://example.com

[1/4] JavaScript 파일 수집 중...
  ✓ 수집된 JS 파일: 45개

[2/4] JavaScript 분석 중...
파일 분석: 100%|████████████████████| 45/45 [00:12<00:00]
  ✓ 발견된 엔드포인트: 87개
  [AI] AI 추가 엔드포인트: 12개

[3/4] 보안 취약점 스캔 중...
엔드포인트 스캔: 100%|████████████████████| 99/99 [01:23<00:00]
  ✓ 발견된 취약점: 27개
    - Critical: 2개
    - High: 8개
    - Medium: 17개

[4/4] 리포트 생성 중...
[+] JSON report: output/full_scan_20251014_120000.json
[+] HTML report: output/full_scan_20251014_120000.html
[+] Markdown report: output/full_scan_20251014_120000.md

============================================================
[✓] 스캔 완료!

📊 결과 요약:
  • 엔드포인트: 99개
  • Shadow APIs: 15개
  • 취약점: 27개
  • 발견된 경로: 7개

📁 생성된 리포트:
  • JSON: output/full_scan_20251014_120000.json
  • HTML: output/full_scan_20251014_120000.html
  • MARKDOWN: output/full_scan_20251014_120000.md
============================================================
```

---

## 6. 웹 UI

### 6.1 주요 기능

#### 6.1.1 Scan 탭
- **Target URL**: 스캔할 웹 애플리케이션 URL
- **JS Path**: JavaScript 파일 경로 (선택)
- **Analysis Type**:
  - `js_analysis`: JavaScript 분석만
  - `full_scan`: 전체 스캔 (JS + 취약점)
- **Options**:
  - Scan Vulnerabilities: 취약점 스캔
  - Enable AI Analysis: AI 기반 분석
  - Enable Bruteforce: 디렉토리 브루트포싱

**실시간 진행 상황:**
- 진행률 바 (0-100%)
- 현재 단계 표시
- 로그 메시지

#### 6.1.2 Projects 탭
- 프로젝트 생성 및 관리
- 프로젝트별 스캔 그룹화
- 스캔 이력 조회

#### 6.1.3 History 탭
- 최근 스캔 목록
- 상태별 필터 (completed, running, failed)
- 스캔 상세 보기
- 스캔 삭제

#### 6.1.4 Dashboard 탭
- 전체 통계 요약
- 최근 발견 취약점
- Shadow API 목록

### 6.2 결과 화면

#### 통계 대시보드
```
┌───────────────┬───────────────┬───────────────┬───────────────┐
│ 엔드포인트    │ Shadow APIs   │ 취약점        │ 발견된 경로   │
│     99        │      15       │      27       │       7       │
└───────────────┴───────────────┴───────────────┴───────────────┘
```

#### 발견된 경로 (Discovered Paths)
```
🔗 http://example.com/admin
   Status: 200  Size: 12.34 KB  text/html

🔗 http://example.com/api/internal/config
   Status: 403  Size: 0.56 KB  application/json
```

#### Shadow APIs
```
🔴 GET /api/internal/admin/users
   소스: js_analysis
   [PoC 보기] [상세 정보]
```

#### 취약점
```
🔴 CRITICAL - SQL Injection
   엔드포인트: GET /api/v1/user/{id}
   설명: URL 파라미터에서 SQL 에러 메시지 감지
   증거: "sqlite3.OperationalError: unrecognized token"
   권장사항: 파라미터화된 쿼리 사용
   CWE: CWE-89
   [PoC 코드 보기]
```

---

## 7. AI 기능

### 7.1 개요
OpenAI GPT를 사용한 고급 JavaScript 분석으로 Regex 기반 분석의 한계를 극복합니다.

### 7.2 AI가 발견하는 것

#### 7.2.1 동적 URL 추출
```javascript
// Regex: ❌ 탐지 불가
const apiVersion = 'v2';
fetch(`/api/${apiVersion}/users`);

// AI: ✅ /api/v2/users 추출
```

#### 7.2.2 복잡한 패턴
```javascript
// Regex: ❌ 탐지 어려움
const endpoints = {
  users: '/api/v1/users',
  admin: '/api/internal/admin'
};
fetch(endpoints[action]);

// AI: ✅ 모든 엔드포인트 추출 + Shadow API 플래그
```

#### 7.2.3 PoC 코드 생성
```python
# AI 자동 생성 PoC 예시
import requests

# SQL Injection Test
payload = "1' OR '1'='1"
response = requests.get(
    f"http://example.com/api/v1/user/{payload}",
    timeout=10
)
print(f"Status: {response.status_code}")
print(f"Response: {response.text[:200]}")
```

### 7.3 설정 방법

```bash
# 1. OpenAI API 키 발급
# https://platform.openai.com/api-keys

# 2. .env 파일 설정
OPENAI_API_KEY=sk-your-actual-key
OPENAI_MODEL=gpt-4-turbo-preview
AI_ANALYSIS_ENABLED=true
AI_MAX_TOKENS=8000

# 3. 의존성 설치
pip install openai python-dotenv
```

### 7.4 비용 관리

#### 예상 비용 (GPT-4 Turbo 기준)
- 작은 JS 파일 (5KB): ~$0.001
- 중간 JS 파일 (50KB): ~$0.01
- 큰 JS 파일 (200KB): ~$0.04

#### 비용 절감
```bash
# 저렴한 모델 사용
OPENAI_MODEL=gpt-3.5-turbo  # 10배 저렴

# 토큰 제한
AI_MAX_TOKENS=2000

# 선택적 활성화
AI_ANALYSIS_ENABLED=false  # 기본 스캔
```

### 7.5 성능 비교

| 항목 | Regex 전용 | AI 추가 | 향상도 |
|------|----------|---------|--------|
| 단순 패턴 | 95% | 100% | +5% |
| 동적 URL | 20% | 85% | +325% |
| Shadow API | 40% | 90% | +125% |
| PoC 생성 | 0% | 100% | NEW |
| 분석 시간 | 0.5초 | 3.2초 | +540% |

---

## 8. 데이터베이스

### 8.1 지원 데이터베이스
- **SQLite**: 기본, 제로 설정
- **PostgreSQL**: 프로덕션 권장

### 8.2 스키마

```sql
-- Projects
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    project_id VARCHAR(36) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Scans
CREATE TABLE scans (
    id INTEGER PRIMARY KEY,
    scan_id VARCHAR(36) UNIQUE NOT NULL,
    project_id INTEGER REFERENCES projects(id),
    target_url VARCHAR(500) NOT NULL,
    js_path VARCHAR(500),
    status VARCHAR(20) NOT NULL,  -- pending, running, completed, failed
    progress INTEGER DEFAULT 0,
    message TEXT,
    scan_vulns BOOLEAN DEFAULT TRUE,
    ai_enabled BOOLEAN DEFAULT TRUE,
    bruteforce_enabled BOOLEAN DEFAULT FALSE,
    total_endpoints INTEGER DEFAULT 0,
    shadow_apis INTEGER DEFAULT 0,
    public_apis INTEGER DEFAULT 0,
    total_vulnerabilities INTEGER DEFAULT 0,
    created_at TIMESTAMP,
    completed_at TIMESTAMP,
    output_path VARCHAR(500)
);

-- Endpoints
CREATE TABLE endpoints (
    id INTEGER PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id),
    url VARCHAR(1000) NOT NULL,
    method VARCHAR(10) NOT NULL,
    is_shadow_api BOOLEAN DEFAULT FALSE,
    parameters JSON,
    headers JSON,
    poc_code TEXT,
    source VARCHAR(200),
    timestamp TIMESTAMP
);

-- Vulnerabilities
CREATE TABLE vulnerabilities (
    id INTEGER PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id),
    type VARCHAR(100) NOT NULL,
    level VARCHAR(20) NOT NULL,  -- critical, high, medium, low, info
    endpoint VARCHAR(1000) NOT NULL,
    method VARCHAR(10) NOT NULL,
    description TEXT NOT NULL,
    evidence TEXT,
    recommendation TEXT NOT NULL,
    poc_code TEXT,
    cwe_id VARCHAR(20),
    timestamp TIMESTAMP
);

-- Discovered Paths (신규)
CREATE TABLE discovered_paths (
    id INTEGER PRIMARY KEY,
    scan_id INTEGER REFERENCES scans(id),
    path VARCHAR(1000) NOT NULL,
    status_code INTEGER NOT NULL,
    content_length INTEGER,
    content_type VARCHAR(200),
    timestamp TIMESTAMP
);
```

### 8.3 Repository 패턴

```python
# Scan 생성
scan = ScanRepository.create_scan(
    db, scan_id="abc-123",
    target_url="http://example.com",
    scan_vulns=True, ai_enabled=True
)

# 상태 업데이트
ScanRepository.update_scan_status(
    db, scan_id="abc-123",
    status=ScanStatus.RUNNING,
    progress=50,
    message="Scanning endpoints..."
)

# 결과 저장
ScanRepository.save_scan_result(
    db, scan_id="abc-123",
    scan_result=result_object,
    output_path="output/scan_abc-123"
)

# 상세 정보 조회
result = ScanRepository.get_scan_with_details(db, "abc-123")
# 반환: scan 정보 + endpoints + vulnerabilities + discovered_paths

# 이력 조회
history = ScanRepository.get_scan_history(db, limit=10)

# 삭제
ScanRepository.delete_scan(db, "abc-123")
```

---

## 9. 테스트 가이드

### 9.1 테스트 환경 설정

#### 9.1.1 Docker로 취약한 테스트 앱 실행
```bash
# 시작
# Windows:
docker-run.bat
# Linux/Mac:
chmod +x docker-run.sh && ./docker-run.sh

# 상태 확인
docker ps | grep vulnerable-test-app

# 로그 확인
docker logs vulnerable-test-app

# 정지
# Windows:
docker-stop.bat
# Linux/Mac:
./docker-stop.sh
```

#### 9.1.2 Python으로 직접 실행
```bash
cd test-app
python app.py
# 실행: http://localhost:5000
```

### 9.2 자동 통합 테스트

```bash
# Windows
test-scripts\run-test.bat

# Linux/Mac
chmod +x test-scripts/run-test.sh
./test-scripts/run-test.sh
```

**테스트 내용:**
1. JavaScript 파일 분석
2. 엔드포인트 발견 검증
3. 취약점 스캔 실행
4. 리포트 생성 확인

### 9.3 예상 테스트 결과

#### 발견될 엔드포인트 (15개 이상)
```
✅ /api/v1/users               (GET)     - Public
✅ /api/v1/user/<id>           (GET)     - Public
✅ /api/v1/products            (GET)     - Public
✅ /api/v1/auth/login          (POST)    - Public
✅ /api/v1/search              (GET)     - Public
✅ /api/v1/upload              (POST)    - Public
⚠️ /api/internal/admin/users  (GET)     - Shadow API
⚠️ /api/internal/debug/config (GET)     - Shadow API
```

#### 발견될 취약점 (20개 이상)
| 취약점 | 심각도 | 개수 | 엔드포인트 예시 |
|--------|--------|------|----------------|
| SQL Injection | 🔴 CRITICAL | 2+ | /api/v1/user/{id} |
| Missing Authentication | 🟠 HIGH | 8+ | 대부분 |
| CORS Misconfiguration | 🟠 HIGH | 1+ | 모든 엔드포인트 |
| XSS | 🟠 HIGH | 2+ | /api/v1/search |
| Sensitive Data Exposure | 🟠 HIGH | 5+ | /api/v1/user/* |
| Missing Rate Limiting | 🟡 MEDIUM | 10+ | 모든 엔드포인트 |

### 9.4 수동 검증

```bash
# SQL Injection 테스트
curl "http://localhost:5000/api/v1/user/1'"
# 예상: SQL 에러 메시지

# XSS 테스트
curl "http://localhost:5000/api/v1/search?q=<script>alert('XSS')</script>"
# 예상: 스크립트가 그대로 반환

# 인증 누락 테스트
curl http://localhost:5000/api/v1/users
# 예상: 200 OK + 사용자 목록

# Shadow API 접근
curl http://localhost:5000/api/internal/admin/users
# 예상: 200 OK + 내부 데이터
```

### 9.5 성능 벤치마크

| 작업 | 대상 | 예상 시간 |
|------|------|----------|
| JS 분석 | 1개 파일 | < 1초 |
| JS 분석 | 45개 파일 | < 10초 |
| 엔드포인트 수집 | 15개 | < 1초 |
| 취약점 스캔 | 15개 엔드포인트 | 30-60초 |
| AI 분석 | 1개 파일 | 2-5초 |
| 브루트포싱 | 100개 경로 | 20-40초 |
| **전체 스캔** | **test-app** | **60-90초** |

---

## 10. 개발 가이드

### 10.1 코드 스타일

#### Python (PEP 8)
```python
# 네이밍
snake_case       # 함수, 변수
PascalCase       # 클래스
UPPER_SNAKE_CASE # 상수

# 들여쓰기: 4칸
def analyze_endpoint(url: str) -> APIEndpoint:
    """엔드포인트 분석"""
    endpoint = parse_url(url)
    return endpoint

# 타입 힌트 사용
def scan_endpoints(
    endpoints: List[APIEndpoint],
    timeout: int = 10
) -> List[Vulnerability]:
    pass
```

#### TypeScript (Web UI)
```typescript
// 네이밍
camelCase         // 변수, 함수
PascalCase        // 컴포넌트, 타입
UPPER_SNAKE_CASE  // 상수

// 인터페이스
interface ScanResult {
  scanId: string;
  status: ScanStatus;
  endpoints: APIEndpoint[];
}

// 함수형 컴포넌트
const ScanView: React.FC<Props> = ({ scanId }) => {
  return <div>...</div>;
};
```

### 10.2 새로운 취약점 체크 추가

```python
# src/scanner/vulnerability_scanner.py

class VulnerabilityScanner:
    def _check_new_vuln(self, endpoint: APIEndpoint) -> Optional[Vulnerability]:
        """새로운 취약점 체크"""
        try:
            # 1. 테스트 요청 생성
            response = self._send_request(
                endpoint,
                payload="test_payload"
            )
            
            # 2. 취약점 탐지 로직
            if self._is_vulnerable(response):
                return Vulnerability(
                    type="New Vulnerability Type",
                    level=VulnerabilityLevel.HIGH,
                    endpoint=endpoint.url,
                    method=endpoint.method,
                    description="상세 설명",
                    evidence=response.text[:200],
                    recommendation="권장사항",
                    cwe_id="CWE-XXX"
                )
        except Exception as e:
            logger.error(f"Check failed: {e}")
        
        return None
    
    def scan_endpoint(self, endpoint: APIEndpoint) -> List[Vulnerability]:
        """엔드포인트 스캔"""
        vulns = []
        
        # 기존 체크들
        vulns.extend(self._check_authentication(endpoint))
        vulns.extend(self._check_sql_injection(endpoint))
        # ...
        
        # 새 체크 추가
        new_vuln = self._check_new_vuln(endpoint)
        if new_vuln:
            vulns.append(new_vuln)
        
        return vulns
```

### 10.3 새로운 리포트 형식 추가

```python
# src/reporter/report_generator.py

class ReportGenerator:
    def generate_xml(self, scan_result: ScanResult, output_path: str) -> str:
        """XML 리포트 생성"""
        xml_content = self._build_xml(scan_result)
        
        xml_file = f"{output_path}/scan_report.xml"
        with open(xml_file, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        return xml_file
    
    def _build_xml(self, scan_result: ScanResult) -> str:
        """XML 구조 생성"""
        root = ET.Element("ScanResult")
        
        # 통계
        stats = ET.SubElement(root, "Statistics")
        for key, value in scan_result.statistics.items():
            stat = ET.SubElement(stats, key)
            stat.text = str(value)
        
        # 엔드포인트
        endpoints = ET.SubElement(root, "Endpoints")
        for ep in scan_result.endpoints:
            endpoint = ET.SubElement(endpoints, "Endpoint")
            ET.SubElement(endpoint, "URL").text = ep.url
            ET.SubElement(endpoint, "Method").text = ep.method.value
        
        # 취약점
        vulns = ET.SubElement(root, "Vulnerabilities")
        for vuln in scan_result.vulnerabilities:
            vulnerability = ET.SubElement(vulns, "Vulnerability")
            ET.SubElement(vulnerability, "Type").text = vuln.type
            ET.SubElement(vulnerability, "Level").text = vuln.level.value
        
        return ET.tostring(root, encoding='unicode', method='xml')
    
    def generate_all(self, scan_result: ScanResult, output_dir: str) -> Dict[str, str]:
        """모든 형식 리포트 생성"""
        reports = {}
        reports['json'] = self.generate_json(scan_result, output_dir)
        reports['html'] = self.generate_html(scan_result, output_dir)
        reports['markdown'] = self.generate_markdown(scan_result, output_dir)
        reports['xml'] = self.generate_xml(scan_result, output_dir)  # 신규
        return reports
```

### 10.4 JavaScript 분석 패턴 추가

```python
# src/analyzer/js_analyzer.py

class JSAnalyzer:
    def __init__(self):
        self.api_patterns = [
            # 기존 패턴
            r'fetch\([\'"`]([^\'"` ]+)[\'"`]',
            r'axios\.(?:get|post|put|delete)\([\'"`]([^\'"` ]+)[\'"`]',
            
            # 새 패턴 추가
            r'apiClient\.request\([\'"`]([^\'"` ]+)[\'"`]',  # 커스텀 API 클라이언트
            r'http\.(?:get|post)\([\'"`]([^\'"` ]+)[\'"`]', # http 라이브러리
            r'api\([\'"`]([^\'"` ]+)[\'"`]',                 # 일반 api 함수
        ]
```

### 10.5 테스트 작성

```python
# tests/test_scanner.py

import pytest
from src.scanner.vulnerability_scanner import VulnerabilityScanner
from src.utils.models import APIEndpoint, HTTPMethod

@pytest.fixture
def scanner():
    return VulnerabilityScanner()

@pytest.fixture
def test_endpoint():
    return APIEndpoint(
        url="http://localhost:5000/api/test",
        method=HTTPMethod.GET
    )

def test_sql_injection_detection(scanner, test_endpoint):
    """SQL Injection 탐지 테스트"""
    vulns = scanner._check_sql_injection(test_endpoint)
    
    assert len(vulns) > 0
    assert vulns[0].type == "SQL Injection"
    assert vulns[0].level == VulnerabilityLevel.CRITICAL
    assert "CWE-89" in vulns[0].cwe_id

def test_authentication_check(scanner, test_endpoint):
    """인증 체크 테스트"""
    vulns = scanner._check_authentication(test_endpoint)
    
    if vulns:
        assert vulns[0].type == "Missing Authentication"
        assert vulns[0].level == VulnerabilityLevel.HIGH

# 실행
# pytest -v tests/test_scanner.py
```

### 10.6 커밋 메시지 가이드

```
<type>: <imperative summary>

<optional body>

<optional footer>
```

**Types:**
- `feat`: 새 기능
- `fix`: 버그 수정
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `docs`: 문서 업데이트
- `chore`: 빌드/도구 설정

**예시:**
```
feat: add GraphQL endpoint detection in JSAnalyzer

- Extended regex patterns for graphql queries
- Added test cases in test-app/static/
- Updated TESTING.md expected endpoint count

Closes #123
```

---

## 11. 문제 해결

### 11.1 설치 관련

#### Python 의존성 오류
```bash
# 가상환경 재생성
rm -rf venv
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 의존성 재설치
pip install --upgrade pip
pip install -r requirements.txt
```

#### Playwright 설치 실패
```bash
# 수동 설치
pip install playwright
playwright install chromium

# 권한 문제 (Linux)
sudo playwright install-deps
```

### 11.2 실행 관련

#### "Python을 찾을 수 없음"
```bash
# Python 경로 확인
which python    # Linux/Mac
where python    # Windows

# PATH 환경변수에 추가
# Windows: 시스템 환경변수 편집
# Linux/Mac: ~/.bashrc 또는 ~/.zshrc에 추가
export PATH="/usr/local/bin/python3:$PATH"
```

#### 포트 충돌
```bash
# 사용 중인 포트 확인
# Windows:
netstat -ano | findstr :5001

# Linux/Mac:
lsof -i :5001

# 프로세스 종료
# Windows:
taskkill /PID <PID> /F

# Linux/Mac:
kill -9 <PID>

# 다른 포트 사용
PORT=5002 python api_server.py
```

#### 데이터베이스 연결 실패
```bash
# SQLite 파일 권한 확인
chmod 644 data/scanner.db

# PostgreSQL 연결 테스트
psql -h localhost -U postgres -d shadow_api_scanner

# 데이터베이스 재생성
python setup_db.py
```

### 11.3 스캔 관련

#### "Scan timeout" 오류
**원인**: 스캔이 너무 오래 걸림

**해결:**
```python
# config/config.yaml
scanner:
  timeout: 20          # 10 → 20초
  max_retries: 2       # 3 → 2회

# Web UI: src/app/page.tsx
const maxAttempts = 600;  // 300 → 600 (20분)
```

#### 취약점이 발견되지 않음
```bash
# 타겟 서버 접근 확인
curl http://localhost:5000

# 스캔 로그 상세 확인
python main.py full-scan http://localhost:5000 \
  --js-path test-app/static \
  --scan-vulns 2>&1 | tee scan.log

# 디버그 모드
# main.py 수정: logging.basicConfig(level=logging.DEBUG)
```

#### AI 분석 오류
```bash
# API 키 확인
echo $OPENAI_API_KEY

# .env 파일 확인
cat .env | grep OPENAI

# 수동 테스트
python -c "
from openai import OpenAI
client = OpenAI()
response = client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'test'}]
)
print(response.choices[0].message.content)
"
```

### 11.4 Web UI 관련

#### "Failed to check scan status"
**브라우저 콘솔 확인:**
```javascript
// F12 → Console 탭
// 다음 로그 확인:
// - Starting scan with: {...}
// - Scan started: {...}
// - Poll error: {...}
```

**API 서버 확인:**
```bash
# Flask API 서버 실행 중인지 확인
curl http://localhost:5001/health

# 로그 확인
# Terminal에서 python api_server.py 출력 확인
```

**해결 단계:**
1. API 서버 재시작: `python api_server.py`
2. Web UI 재시작: `npm run dev`
3. 브라우저 캐시 삭제 (Ctrl+Shift+Delete)
4. `.env.local` 확인: `NEXT_PUBLIC_API_URL=http://localhost:5001`

#### Next.js 빌드 오류
```bash
# 의존성 재설치
cd web-ui
rm -rf node_modules package-lock.json
npm install

# 캐시 삭제
rm -rf .next

# 재빌드
npm run build
```

#### CORS 오류
```bash
# api_server.py 확인
# flask_cors가 설치되어 있는지
pip install flask-cors

# CORS 설정 확인
# api_server.py에 다음 코드 확인:
# CORS(app, resources={r"/api/*": {"origins": "*"}})
```

### 11.5 Docker 관련

#### 테스트 앱 접속 불가
```bash
# 컨테이너 상태 확인
docker ps -a | grep vulnerable-test-app

# 로그 확인
docker logs vulnerable-test-app

# 포트 매핑 확인
docker port vulnerable-test-app

# 재시작
docker restart vulnerable-test-app

# 완전 재구성
docker stop vulnerable-test-app
docker rm vulnerable-test-app
cd test-app
docker build -t vulnerable-test-app .
docker run -d --name vulnerable-test-app -p 5000:5000 vulnerable-test-app
```

#### "Address already in use" 오류
```bash
# 기존 컨테이너 중지
docker stop $(docker ps -q --filter "expose=5000")

# 다른 포트로 실행
docker run -d --name vulnerable-test-app -p 5001:5000 vulnerable-test-app

# 스캔 시 포트 변경
python main.py full-scan http://localhost:5001 ...
```

### 11.6 진단 체크리스트

**CLI 모드:**
- [ ] Python 3.8+ 설치
- [ ] `pip install -r requirements.txt` 완료
- [ ] `config/config.yaml` 존재
- [ ] 타겟 서버 접근 가능
- [ ] `output/` 디렉토리 쓰기 권한

**Web UI 모드:**
- [ ] Flask API 서버 실행 중 (http://localhost:5001)
- [ ] Next.js 서버 실행 중 (http://localhost:3000)
- [ ] 데이터베이스 초기화 완료 (`python setup_db.py`)
- [ ] `.env` 파일 설정 (API 키, DB URL)
- [ ] `web-ui/.env.local` 파일 설정 (API_URL)
- [ ] 브라우저 콘솔 에러 없음

**테스트 환경:**
- [ ] Docker 설치 및 실행
- [ ] 테스트 앱 실행 중 (http://localhost:5000)
- [ ] 테스트 앱 API 응답 확인 (`curl http://localhost:5000/api/v1/products`)

---

## 12. 법적 고지

### 12.1 사용 제한

**⚠️ 중요: 이 도구는 방어적 보안 목적으로만 사용되어야 합니다.**

#### 허용되는 사용
✅ 자신이 소유하거나 명시적 허가를 받은 시스템  
✅ 모의 침투 테스트 및 보안 평가  
✅ 취약점 발견 및 수정을 위한 교육적 목적  
✅ 보안 연구 및 학습

#### 금지되는 사용
❌ 무단 접근 및 데이터 탈취  
❌ 악의적 목적의 취약점 악용  
❌ 허가 없는 시스템 스캔  
❌ 불법적인 침투 활동

### 12.2 책임 소재
사용자는 이 도구의 사용으로 인한 모든 법적 책임을 집니다. 개발자는 오용에 대한 책임을 지지 않습니다.

### 12.3 보안 윤리 강령
1. **허가 획득**: 스캔 전 명시적 허가
2. **데이터 보호**: 발견된 민감 정보 보호
3. **책임 공개**: 취약점 발견 시 책임있는 공개 (Responsible Disclosure)
4. **법률 준수**: 현지 법률 및 규정 준수

### 12.4 라이선스
이 프로젝트는 교육 및 보안 연구 목적으로 제공됩니다.

---

## 13. 부록

### 13.1 설정 파일 예시

#### config/config.yaml
```yaml
# 프록시 설정
proxy:
  host: "127.0.0.1"
  port: 8080
  timeout: 30

# JavaScript 분석
js_analysis:
  patterns:
    - "fetch("
    - "axios."
    - "XMLHttpRequest"
    - "$.ajax"
  shadow_api_keywords:
    - "/internal/"
    - "/admin/"
    - "/debug/"
    - "/_"
    - "/api/v0/"

# 취약점 스캐너
scanner:
  checks:
    - authentication
    - authorization
    - cors
    - sql_injection
    - xss
    - rate_limiting
    - sensitive_data
  timeout: 10
  max_retries: 3

# 브루트포싱
bruteforce:
  wordlist: "wordlists/common_directories.txt"
  timeout: 5
  max_paths: 100

# 출력
output:
  directory: "output"
  formats:
    - "json"
    - "html"
    - "markdown"
```

#### .env
```bash
# Database
DATABASE_URL=sqlite:///data/scanner.db
# DATABASE_URL=postgresql://user:password@localhost:5432/shadow_api_scanner

# OpenAI (선택)
OPENAI_API_KEY=sk-your-actual-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
AI_ANALYSIS_ENABLED=true
AI_MAX_TOKENS=8000
AI_TEMPERATURE=0.1

# Flask API Server
FLASK_ENV=development
FLASK_DEBUG=True
API_PORT=5001

# Security (프로덕션)
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-here
```

#### web-ui/.env.local
```bash
# API 서버 URL
NEXT_PUBLIC_API_URL=http://localhost:5001

# 선택적 설정
NEXT_PUBLIC_ENABLE_ANALYTICS=false
NEXT_PUBLIC_MAX_SCAN_DURATION=600000
```

### 13.2 의존성 목록

#### requirements.txt
```
# Core
requests==2.31.0
beautifulsoup4==4.12.2
pydantic==2.5.3
click==8.1.7

# Network
mitmproxy==10.1.6
urllib3==2.1.0

# JavaScript Analysis
esprima==4.0.1

# AI (Optional)
openai==1.3.8
python-dotenv==1.0.0

# Database
sqlalchemy==2.0.23
alembic==1.13.0
psycopg2-binary==2.9.9  # PostgreSQL (optional)

# API Server
flask==3.0.0
flask-cors==4.0.0

# Reporting
jinja2==3.1.2
markdown==3.5.1

# CLI
colorama==0.4.6
tqdm==4.66.1

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
```

#### web-ui/package.json
```json
{
  "dependencies": {
    "next": "14.2.33",
    "react": "^18",
    "react-dom": "^18",
    "typescript": "^5",
    "tailwindcss": "^3.4.1",
    "axios": "^1.6.5",
    "lucide-react": "^0.344.0",
    "recharts": "^2.12.0"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "eslint": "^8",
    "eslint-config-next": "14.2.33",
    "autoprefixer": "^10.0.1",
    "postcss": "^8"
  }
}
```

### 13.3 유용한 링크

#### 공식 문서
- Python: https://docs.python.org/3/
- Next.js: https://nextjs.org/docs
- SQLAlchemy: https://docs.sqlalchemy.org/
- OpenAI API: https://platform.openai.com/docs

#### 보안 참고자료
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CWE List: https://cwe.mitre.org/
- NIST NVD: https://nvd.nist.gov/

#### 커뮤니티
- GitHub Issues: <repository-url>/issues
- Security Contact: <security-email>

---

## 14. 버전 히스토리

### v2.0 (2025-10-14)
- ✨ Web UI 추가 (Next.js)
- ✨ 데이터베이스 통합 (SQLite/PostgreSQL)
- ✨ 프로젝트 관리 기능
- ✨ discovered_paths DB 저장
- 🔧 API 서버 개선
- 📝 통합 문서 작성

### v1.5 (2025-01)
- ✨ AI 기반 JavaScript 분석
- ✨ PoC 코드 자동 생성
- 🐛 디렉토리 브루트포싱 버그 수정

### v1.0 (2024-12)
- 🎉 초기 릴리스
- ✨ CLI 인터페이스
- ✨ JavaScript 정적 분석
- ✨ 취약점 스캔
- ✨ JSON/HTML/Markdown 리포트

---

## 15. 연락처

**문의사항:**
- 📧 Email: <contact-email>
- 🐛 Issues: <repository-url>/issues
- 🔒 Security: <security-email>

**기여:**
- 💡 Feature Requests: <repository-url>/issues/new
- 🐛 Bug Reports: <repository-url>/issues/new
- 🔀 Pull Requests: <repository-url>/pulls

---

**Shadow API Scanner** - 더 안전한 웹 애플리케이션을 위하여 🛡️

**© 2024-2025 Shadow API Scanner Team. All rights reserved.**
