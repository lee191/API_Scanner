# 🔍 Shadow API Scanner - 프로젝트 문서

> 웹 애플리케이션의 숨겨진 API를 탐색하고 보안 취약점을 분석하는 모의 침투 테스트 도구

**버전**: 2.0  
**최종 업데이트**: 2025-10-14  
**라이선스**: Educational Use Only

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [빠른 시작](#빠른-시작)
3. [주요 기능](#주요-기능)
4. [아키텍처](#아키텍처)
5. [취약점 탐지 방식](#취약점-탐지-방식)
6. [PoC 생성 가이드](#poc-생성-가이드)
7. [한국 시간대 지원](#한국-시간대-지원)
8. [API 문서](#api-문서)
9. [설정](#설정)
10. [테스트](#테스트)
11. [문제 해결](#문제-해결)
12. [최근 변경사항](#최근-변경사항)
13. [법적 고지사항](#법적-고지사항)

---

## 프로젝트 개요

Shadow API Scanner는 JavaScript 정적 분석, AI 기반 패턴 인식, 자동화된 보안 스캔을 통해 웹 애플리케이션의 숨겨진 API와 보안 취약점을 발견하는 도구입니다.

### 핵심 기능

#### 🔍 API 탐색
- **JavaScript 정적 분석**: Regex 및 AST 기반 엔드포인트 추출
- **AI 기반 분석**: OpenAI GPT를 활용한 고급 패턴 인식
- **디렉토리 브루트포싱**: Wordlist 기반 숨겨진 경로 탐색
- **네트워크 캡처**: mitmproxy를 통한 실시간 트래픽 분석

#### 🛡️ 보안 취약점 스캔
- **SQL Injection** (CWE-89): Error-based + Boolean-based Blind SQLi
- **Cross-Site Scripting** (CWE-79): Reflected XSS
- **Missing Authentication** (CWE-306): 인증 없는 엔드포인트 접근
- **CORS Misconfiguration** (CWE-942): 출처 검증 오류
- **Sensitive Data Exposure** (CWE-200): 민감 정보 노출
- **Missing Rate Limiting** (CWE-770): 무제한 요청 허용

#### 📊 리포팅 및 분석
- **다양한 형식**: JSON, HTML, Markdown
- **AI 기반 PoC 생성**: 선택적 Proof of Concept 코드 생성
- **Web UI 대시보드**: 실시간 스캔 모니터링 및 결과 분석
- **데이터베이스 통합**: 스캔 이력 및 프로젝트 관리

### 기술 스택

**백엔드**:
- Python 3.8+
- Flask 3.0.0 (API 서버)
- SQLAlchemy (ORM)
- OpenAI GPT-4-turbo-preview (AI 분석)
- mitmproxy (네트워크 캡처)

**프론트엔드**:
- Next.js 14.2.33
- React 18
- TypeScript 5
- Tailwind CSS
- Recharts (차트)

**데이터베이스**:
- SQLite 3 (기본)
- PostgreSQL/MySQL 지원 가능

---

## 빠른 시작

### 사전 요구사항

- Python 3.8 이상
- Node.js 16 이상 (Web UI 사용 시)
- OpenAI API 키 (AI 기능 사용 시)

### 설치

```bash
# 1. 저장소 클론
git clone <repository-url>
cd API_Scanner

# 2. Python 의존성 설치
pip install -r requirements.txt

# 3. 환경 변수 설정
cp .env.example .env
# .env 파일을 편집하여 OpenAI API 키 설정

# 4. 데이터베이스 초기화
python setup_db.py

# 5. Web UI 설정 (선택사항)
cd web-ui
npm install
cd ..
```

### 실행

#### CLI 모드

```bash
# 전체 스캔 (JavaScript 분석 + 취약점 스캔)
python main.py full-scan http://localhost:5000 \
  --js-path ./static \
  --scan-vulns \
  --bruteforce

# JavaScript 분석만
python main.py analyze-js ./static http://localhost:5000

# 디렉토리 브루트포싱
python main.py bruteforce http://localhost:5000 \
  --wordlist wordlists/common_directories.txt
```

#### Web UI 모드

```bash
# Terminal 1: API 서버 시작
python api_server.py

# Terminal 2: Web UI 시작 (새 터미널)
cd web-ui
npm run dev
```

브라우저에서 `http://localhost:3000` 접속

---

## 주요 기능

### 1. Shadow API 자동 발견

#### JavaScript 정적 분석
```javascript
// 자동으로 감지되는 패턴:
fetch('/api/admin/users')
axios.get('/api/internal/config')
$.ajax({ url: '/api/v1/data' })
```

#### 탐지 가능한 API 패턴
- RESTful API: `/api/v1/users`, `/api/products/{id}`
- GraphQL: `/graphql`, `/api/graphql`
- Internal API: `/internal/*`, `/admin/api/*`
- Legacy API: `/legacy/*`, `/old-api/*`

### 2. 취약점 스캔

#### SQL Injection 탐지 (Enhanced)

**Error-based Detection** (18+ payloads):
```python
payloads = [
    "'",
    "1' OR '1'='1",
    "'; DROP TABLE users--",
    "admin'--",
    "1' UNION SELECT NULL--",
    # ... 총 18개
]
```

**Boolean-based Blind SQLi**:
```python
# TRUE 조건
"1' AND '1'='1"
"1' AND 1=1--"

# FALSE 조건  
"1' AND '1'='2"
"1' AND 1=0--"

# 응답 길이 비교 알고리즘
if (baseline_true_diff < 100 and true_false_diff > 100):
    # 취약점 발견!
```

#### XSS 탐지
```python
payload = "<script>alert('XSS')</script>"
# 반사된 입력 값 검증
if payload in response.text:
    # XSS 취약점 발견
```

### 3. AI 기반 PoC 생성

**선택적 생성 시스템**:
- ✅ **개별 생성**: 필요한 취약점만 선택적으로 PoC 생성
- ✅ **일괄 생성**: 모든 취약점에 대한 PoC 한 번에 생성
- ✅ **비용 효율**: 필요한 경우에만 API 호출
- ✅ **품질 보장**: AI 기반 전문적인 PoC 코드

**생성 프로세스**:
1. 취약점 정보 수집 (타입, 엔드포인트, 증거)
2. OpenAI GPT-4에 컨텍스트 전달
3. 실행 가능한 Python/JavaScript 코드 생성
4. 데이터베이스에 저장 및 Web UI에 표시

### 4. Web UI 대시보드

**주요 기능**:
- **실시간 스캔 모니터링**: 진행률 및 로그 표시
- **프로젝트 관리**: 여러 프로젝트 및 스캔 이력 관리
- **통계 대시보드**: 
  - 최근 30일 스캔 활동 차트
  - 취약점 심각도 분포
  - 상위 취약 엔드포인트 Top 10
- **취약점 상세 정보**: 
  - 한글화된 설명, 증거, 권장사항
  - 클릭 가능한 엔드포인트 목록
  - PoC 코드 생성 및 복사

---

## 아키텍처

### 시스템 구조

```
┌─────────────────────────────────────────────────────────┐
│                      Web UI (Next.js)                   │
│  - 프로젝트 관리  - 스캔 실행  - 결과 분석                   │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP REST API
┌─────────────────────▼───────────────────────────────────┐
│                API Server (Flask)                       │
│  - 스캔 관리  - 취약점 분석  - PoC 생성                     │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────┐
        │             │             │              │
┌───────▼──────┐  ┌───▼────┐  ┌─────▼──────┐ ┌─────▼──────┐
│  JS Analyzer │  │Scanner │  │AI Analyzer │ │  Database  │
│              │  │        │  │  (OpenAI)  │ │  (SQLite)  │
└──────────────┘  └────────┘  └────────────┘ └────────────┘
```

### 모듈 구조

```
src/
├── proxy/              # 네트워크 트래픽 캡처
│   └── capture.py      # mitmproxy 통합
│
├── crawler/            # 웹 크롤링 및 리소스 수집
│   ├── js_collector.py # JavaScript 파일 수집
│   └── directory_bruteforcer.py  # 경로 브루트포싱
│
├── analyzer/           # 코드 분석 및 AI 통합
│   ├── js_analyzer.py  # JavaScript 정적 분석
│   ├── ai_analyzer.py  # AI 기반 분석 및 PoC 생성
│   └── endpoint_collector.py  # 엔드포인트 통합
│
├── scanner/            # 보안 취약점 스캐너
│   └── vulnerability_scanner.py  # 6가지 취약점 검사
│
├── reporter/           # 리포트 생성
│   └── report_generator.py  # JSON/HTML/MD 리포트
│
├── database/           # 데이터베이스 레이어
│   ├── models.py       # SQLAlchemy 모델
│   ├── repository.py   # CRUD 작업
│   └── connection.py   # DB 연결 관리
│
└── utils/              # 공통 유틸리티
    ├── config.py       # 설정 관리
    └── models.py       # Pydantic 모델
```

---

## 취약점 탐지 방식

### 스캔 프로세스

```python
def scan_endpoint(endpoint: APIEndpoint) -> List[Vulnerability]:
    vulnerabilities = []
    
    # 1. 인증 검사
    vulnerabilities.extend(check_authentication(endpoint))
    
    # 2. CORS 설정 검사
    vulnerabilities.extend(check_cors(endpoint))
    
    # 3. 민감 데이터 노출 검사
    vulnerabilities.extend(check_sensitive_data(endpoint))
    
    # 4. Rate Limiting 검사
    vulnerabilities.extend(check_rate_limiting(endpoint))
    
    # 5. SQL Injection 검사 (Enhanced)
    vulnerabilities.extend(check_sql_injection(endpoint))
    
    # 6. XSS 검사
    vulnerabilities.extend(check_xss(endpoint))
    
    return vulnerabilities
```

### 1. 인증 누락 (Missing Authentication)

**심각도**: HIGH | **CWE**: CWE-306

**탐지 방법**:
```python
# 인증 정보 없이 요청 전송
response = requests.get(endpoint.url)

if response.status_code == 200:
    # 취약점 발견: 인증 없이 접근 가능
    vulnerability = {
        'type': 'Missing Authentication',
        'description': '인증 없이 API 엔드포인트에 접근 가능합니다',
        'recommendation': '인증 메커니즘을 구현하세요 (OAuth2, JWT, API Key 등)'
    }
```

**권장 대응**:
- OAuth2, JWT, API Key 인증 구현
- 민감한 엔드포인트는 반드시 인증 필요

### 2. CORS 설정 오류 (CORS Misconfiguration)

**심각도**: HIGH/MEDIUM | **CWE**: CWE-942

**탐지 방법**:
```python
# 악의적인 Origin 헤더 전송
headers = {'Origin': 'https://evil.com'}
response = requests.get(endpoint.url, headers=headers)

acao = response.headers.get('Access-Control-Allow-Origin')
acac = response.headers.get('Access-Control-Allow-Credentials')

if acao == '*' and acac == 'true':
    # 취약점 발견: 모든 출처 허용 + 자격증명 허용
    vulnerability = {
        'type': 'CORS Misconfiguration',
        'description': 'CORS가 자격 증명과 함께 모든 출처를 허용합니다',
        'recommendation': '허용된 출처를 명시적으로 지정하세요'
    }
```

### 3. SQL Injection

**심각도**: CRITICAL | **CWE**: CWE-89

#### Error-based Detection
```python
error_payloads = [
    "'", "\"", "1' OR '1'='1", "admin'--",
    "' UNION SELECT NULL--", "1' AND SLEEP(5)--",
    # ... 총 18개 페이로드
]

sql_errors = [
    'sql syntax', 'mysql_fetch', 'ora-', 'postgresql',
    'sqlite_', 'microsoft sql', 'odbc', 'jdbc',
    # ... 총 25개 에러 패턴
]

for payload in error_payloads:
    response = requests.get(f"{endpoint.url}?id={payload}")
    
    if any(error in response.text.lower() for error in sql_errors):
        # 취약점 발견: SQL 오류 메시지 노출
```

#### Boolean-based Blind SQLi
```python
# 1. Baseline 응답
baseline = requests.get(f"{url}?id=1")

# 2. TRUE 조건
true_response = requests.get(f"{url}?id=1' AND '1'='1")

# 3. FALSE 조건
false_response = requests.get(f"{url}?id=1' AND '1'='2")

# 4. 응답 길이 비교
true_length = len(true_response.text)
false_length = len(false_response.text)

if abs(true_length - false_length) > 100:
    # 취약점 발견: 불린 기반 블라인드 SQLi
```

### 4. Cross-Site Scripting (XSS)

**심각도**: HIGH | **CWE**: CWE-79

```python
xss_payload = "<script>alert('XSS')</script>"
response = requests.get(f"{endpoint.url}?input={xss_payload}")

if xss_payload in response.text:
    # 취약점 발견: 사용자 입력이 살균 처리 없이 반영됨
```

### 5. 민감 데이터 노출 (Sensitive Data Exposure)

**심각도**: HIGH/MEDIUM | **CWE**: CWE-200

```python
sensitive_patterns = [
    r'password', r'api[_-]?key', r'secret', 
    r'token', r'ssn', r'credit[_-]?card'
]

# URL에서 민감 패턴 검사
for pattern in sensitive_patterns:
    if re.search(pattern, endpoint.url, re.I):
        # 취약점 발견: URL에 민감 정보 포함
        
# 응답에서 민감 패턴 검사
for pattern in sensitive_patterns:
    if re.search(pattern, response.text, re.I):
        # 취약점 발견: 응답에 민감 정보 포함
```

### 6. Rate Limiting 누락

**심각도**: MEDIUM | **CWE**: CWE-770

```python
# 5회 빠른 연속 요청
responses = []
for i in range(5):
    response = requests.get(endpoint.url)
    responses.append(response.status_code)

# Rate limit 헤더 확인
has_rate_limit = any(
    header in response.headers
    for header in ['X-RateLimit-Limit', 'X-Rate-Limit']
)

if all(code == 200 for code in responses) and not has_rate_limit:
    # 취약점 발견: Rate Limiting 미구현
```

---

## PoC 생성 가이드

### 선택적 PoC 생성 시스템

#### 변경 사항 (2025-10-14)

**이전**: 
- 스캔 완료 후 자동으로 모든 취약점의 PoC 생성
- 비용 증가 및 불필요한 API 호출

**현재**:
- 사용자가 필요한 취약점만 선택하여 PoC 생성
- 개별 생성 또는 일괄 생성 선택 가능
- 비용 효율적이고 빠른 생성

### Web UI에서 사용

#### 개별 PoC 생성 (권장)

1. **스캔 완료 후** "기록" 탭에서 스캔 선택
2. **취약점 탭** 클릭하여 취약점 목록 확인
3. 원하는 취약점 카드를 클릭하여 **확장**
4. 하단의 **"PoC 생성"** 버튼 클릭
5. 생성 완료 후 **PoC 코드 확인 및 복사**

#### 전체 PoC 일괄 생성

1. 취약점 탭 상단의 **"전체 PoC 생성"** 버튼 클릭
2. 확인 대화상자에서 **확인**
3. 모든 취약점의 PoC 생성 완료 대기
4. 완료 메시지 확인

### API 엔드포인트

#### 개별 PoC 생성
```http
POST /api/vulnerability/{vuln_id}/generate-poc
```

**Response**:
```json
{
  "vulnerability_id": "123",
  "poc_code": "import requests\n\nurl = '...'\n...",
  "message": "PoC generated successfully"
}
```

#### 일괄 PoC 생성
```http
POST /api/scan/{scan_id}/generate-all-pocs
```

**Response**:
```json
{
  "scan_id": "abc-123",
  "generated": 15,
  "skipped": 3,
  "errors": 0,
  "message": "PoC generation completed"
}
```

### PoC 생성 로직

```python
# 1. AI 기반 생성 (OpenAI GPT-4)
try:
    poc_code = ai_analyzer.generate_vulnerability_poc([vulnerability])
    return poc_code
except OpenAIError:
    return "AI PoC generation failed"
```

### 비용 정보

**OpenAI API 비용** (GPT-4 기준):
- 개별 PoC 생성: $0.03 ~ $0.06
- 일괄 생성 (20개): $0.60 ~ $1.20

**권장사항**:
- 중요한 취약점만 선택적으로 생성
- 테스트 환경에서는 gpt-3.5-turbo 사용 고려

---

## 한국 시간대 지원

### 변경사항 (2025-10-14)

모든 시간 기록이 **한국 표준시 (KST, UTC+9)**로 저장 및 표시됩니다.

### 구현 세부사항

#### 1. 데이터베이스 모델
```python
from datetime import datetime, timezone, timedelta

# Korea Standard Time
KST = timezone(timedelta(hours=9))

def get_kst_now():
    """Get current time in KST"""
    return datetime.now(KST)

# 모델에서 사용
class Project(Base):
    created_at = Column(DateTime, default=get_kst_now, nullable=False)
    updated_at = Column(DateTime, default=get_kst_now, onupdate=get_kst_now)
```

#### 2. 적용된 파일
- ✅ `src/database/models.py` - DB 모델 (Project, Scan, Endpoint, Vulnerability)
- ✅ `src/database/repository.py` - Repository 레이어
- ✅ `src/utils/models.py` - Pydantic 모델
- ✅ `main.py` - CLI 진입점

#### 3. 프론트엔드 표시
```typescript
// Web UI에서 한국 시간으로 표시
new Date(timestamp).toLocaleString('ko-KR')
// 예: "2025. 10. 14. 오후 3:45:30"
```

### 마이그레이션

**기존 데이터**:
- 기존 UTC 시간 데이터는 그대로 유지됨
- 새로운 데이터부터 KST로 저장됨
- 필요시 수동으로 +9시간 조정 가능

---

## API 문서

### 프로젝트 관리

#### 프로젝트 생성
```http
POST /api/projects
Content-Type: application/json

{
  "name": "My Web App",
  "description": "Production API security scan"
}
```

#### 프로젝트 목록 조회
```http
GET /api/projects
```

#### 프로젝트 상세 조회
```http
GET /api/projects/{project_id}
```

#### 프로젝트 통계
```http
GET /api/projects/{project_id}/statistics
```

**Response**:
```json
{
  "project_id": "uuid",
  "name": "My Project",
  "total_scans": 5,
  "total_endpoints": 46,
  "total_vulnerabilities": 43,
  "vulnerability_distribution": {
    "critical": 2,
    "high": 15,
    "medium": 20,
    "low": 6
  },
  "recent_activity": {
    "last_scan": "2025-10-14T15:30:00+09:00",
    "scans_last_7_days": 3
  },
  "top_vulnerable_endpoints": [
    {
      "endpoint": "/api/admin/users",
      "vulnerability_count": 5,
      "max_severity": "critical"
    }
  ],
  "scan_history": [...]
}
```

### 스캔 관리

#### 스캔 시작
```http
POST /api/scans
Content-Type: application/json

{
  "project_id": "uuid",
  "target_url": "http://example.com",
  "js_path": "/path/to/js",
  "scan_vulns": true,
  "ai_enabled": true,
  "bruteforce_enabled": false
}
```

#### 스캔 상태 조회
```http
GET /api/scans/{scan_id}
```

#### 스캔 결과 조회
```http
GET /api/scans/{scan_id}/result
```

### 취약점 관리

#### 취약점 목록 조회
```http
GET /api/scans/{scan_id}/vulnerabilities
```

#### PoC 생성
```http
POST /api/vulnerability/{vuln_id}/generate-poc
```

#### 전체 PoC 생성
```http
POST /api/scan/{scan_id}/generate-all-pocs
```

---

## 설정

### 환경 변수 (.env)

```bash
# Database
DATABASE_URL=sqlite:///data/scanner.db

# OpenAI API (필수 - AI 기능 사용 시)
OPENAI_API_KEY=sk-your-api-key-here

# AI Settings
AI_ANALYSIS_ENABLED=true
AI_MODEL=gpt-4-turbo-preview
AI_MAX_TOKENS=3000
AI_TEMPERATURE=0.3

# API Server
API_HOST=0.0.0.0
API_PORT=5001
DEBUG=true

# Security
SECRET_KEY=your-secret-key-here
```

### 설정 파일 (config/config.yaml)

```yaml
# Scanner Configuration
scanner:
  timeout: 10
  max_retries: 3
  delay_between_requests: 0.5
  
  # 검사할 취약점 유형
  checks:
    - authentication
    - cors
    - sensitive_data
    - rate_limiting
    - sql_injection
    - xss

# OpenAI Configuration
openai:
  api_key: ${OPENAI_API_KEY}
  model: "gpt-4-turbo-preview"
  max_tokens: 3000
  temperature: 0.3
  
# Database Configuration
database:
  url: "sqlite:///data/scanner.db"
  echo: false
  
# Report Configuration
report:
  output_dir: "output"
  formats:
    - json
    - html
    - markdown
  
# Bruteforce Configuration  
bruteforce:
  default_wordlist: "wordlists/common_directories.txt"
  max_threads: 10
  timeout: 5
```

---

## 테스트

### 테스트 앱 실행

#### Docker 사용
```bash
# 시작
./docker-run.sh        # Linux/Mac
docker-run.bat         # Windows

# 중지
./docker-stop.sh       # Linux/Mac
docker-stop.bat        # Windows
```

#### 수동 실행
```bash
cd test-app
pip install -r requirements.txt
python app_realistic.py
```

테스트 앱이 http://localhost:5000에서 실행됩니다.

### 자동 통합 테스트

```bash
# Linux/Mac
./test-scripts/run-test.sh

# Windows
test-scripts\run-test.bat
```

**테스트 내용**:
1. 테스트 앱 시작 확인
2. 전체 스캔 실행
3. 결과 검증
4. 리포트 생성 확인

### 예상 결과

테스트 앱 스캔 시:
- **발견된 엔드포인트**: 15+ 개
- **Shadow API**: 5+ 개
- **취약점 총 개수**: 20+ 개
  - Critical: 2+ (SQL Injection)
  - High: 8+ (Missing Auth, XSS)
  - Medium: 10+ (CORS, Rate Limiting)
- **실행 시간**: 60-90초

### 수동 테스트

```bash
# JavaScript 분석
python main.py analyze-js test-app/static http://localhost:5000

# 취약점 스캔
python main.py full-scan http://localhost:5000 \
  --js-path test-app/static \
  --scan-vulns

# 브루트포싱 포함
python main.py full-scan http://localhost:5000 \
  --js-path test-app/static \
  --scan-vulns \
  --bruteforce \
  --wordlist wordlists/common_directories.txt
```

---

## 문제 해결

### 일반적인 문제

#### 1. OpenAI API 오류

**증상**: PoC 생성 시 503 또는 500 에러

**해결**:
```bash
# .env 파일 확인
OPENAI_API_KEY=sk-your-valid-key

# API 키 테스트
python test_openai_connection.py
```

#### 2. 데이터베이스 오류

**증상**: "Database locked" 또는 연결 오류

**해결**:
```bash
# 데이터베이스 재초기화
python setup_db.py

# 또는 마이그레이션
python migrate_db.py
```

#### 3. Web UI 연결 실패

**증상**: "Failed to fetch" 또는 CORS 오류

**해결**:
```bash
# API 서버가 실행 중인지 확인
curl http://localhost:5001/api/health

# API 서버 재시작
python api_server.py
```

#### 4. 시간대 문제

**증상**: 시간이 9시간 차이남

**해결**:
- 이 문서의 [한국 시간대 지원](#한국-시간대-지원) 섹션 참조
- 최신 코드로 업데이트되어 자동으로 KST 사용

### 로그 확인

```bash
# API 서버 로그
python api_server.py
# 터미널 출력에서 오류 확인

# 스캔 로그
python main.py full-scan ... --verbose

# Web UI 콘솔
# 브라우저 개발자 도구 (F12) → Console 탭
```

### 성능 최적화

#### 스캔 속도 향상
```yaml
# config/config.yaml
scanner:
  timeout: 5          # 기본 10초 → 5초로 감소
  delay_between_requests: 0.1  # 딜레이 감소
```

#### 메모리 사용 감소
```python
# 큰 파일 스캔 시 청크 단위 처리
# analyzer/js_analyzer.py에서 자동 처리됨
```

---

## 최근 변경사항

### v2.0 (2025-10-14)

#### 🎯 주요 변경사항

1. **한국 시간대 지원**
   - 모든 시간 기록이 KST (UTC+9)로 저장
   - DB 모델, Repository, Utils 전체 적용
   - 프론트엔드도 한국 시간으로 표시

2. **취약점 메시지 한글화**
   - 모든 취약점의 description, evidence, recommendation 한글화
   - 6가지 취약점 유형 전체 적용
   - 사용자 친화적인 메시지

3. **SQL Injection 강화**
   - Error-based: 18개 페이로드
   - Boolean-based Blind: 12개 페이로드 (TRUE 6 + FALSE 6)
   - 25개 SQL 에러 패턴 감지
   - 응답 길이 비교 알고리즘

4. **대시보드 개선**
   - 클릭 가능한 상위 취약 엔드포인트 목록
   - 엔드포인트별 취약점 상세 정보 모달
   - 실시간 통계 및 차트

5. **PoC 생성 시스템 개선**
   - 선택적 PoC 생성 (개별/일괄)
   - 비용 효율적 운영
   - Web UI에서 즉시 복사 가능

### v1.5 (2025-10-13)

1. **템플릿 PoC 제거**
   - 829라인의 템플릿 코드 제거
   - AI 전용 PoC 생성으로 전환
   - 코드 간소화 및 품질 향상

2. **데이터베이스 스키마 수정**
   - Project.id (integer) 추가
   - Project.project_id (UUID) 유지
   - Scan.project_id FK 수정

### v1.0 (2025-10-01)

- 초기 릴리스
- 기본 기능 구현

---

## 법적 고지사항

### ⚠️ 중요: 책임 있는 사용

이 도구는 **교육 및 방어적 보안 목적**으로만 사용되어야 합니다.

#### ✅ 허용되는 사용

- 자신이 소유한 시스템 테스트
- 명시적 서면 허가를 받은 시스템 평가
- 보안 연구 및 교육 목적
- 모의 침투 테스트 (사전 승인 필요)

#### ❌ 금지되는 사용

- 무단 접근 시도
- 데이터 탈취 또는 파괴
- 서비스 거부 (DoS) 공격
- 악의적 목적의 취약점 악용
- 법적 허가 없는 제3자 시스템 스캔

### 법적 책임

- 사용자는 이 도구 사용에 따른 모든 법적 책임을 집니다
- 개발자는 도구의 오용으로 인한 피해에 대해 책임지지 않습니다
- 각 국가의 컴퓨터 범죄 관련 법규를 준수해야 합니다

### 한국 관련 법규

- **정보통신망법**: 무단 접근 금지
- **정보통신기반보호법**: 중요 시스템 보호
- **개인정보보호법**: 개인정보 처리 제한

### 권장사항

1. 스캔 전 **서면 허가** 확보
2. 스캔 범위 및 시간 **명확히 합의**
3. 발견된 취약점은 **책임있게 보고**
4. 관련 법규 및 규정 **철저히 준수**

---

## 기여

버그 리포트, 기능 제안, 풀 리퀘스트를 환영합니다!

### 기여 방법

1. 이 저장소를 Fork
2. Feature 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 Push (`git push origin feature/AmazingFeature`)
5. Pull Request 생성

### 코드 스타일

- Python: PEP 8
- TypeScript/React: ESLint + Prettier
- 커밋 메시지: Conventional Commits

---

## 라이선스 및 크레딧

**© 2024-2025 Shadow API Scanner Team**

**라이선스**: Educational Use Only

**사용 기술**:
- Flask, SQLAlchemy, OpenAI
- Next.js, React, Tailwind CSS
- mitmproxy, requests, beautifulsoup4

---

## 연락처 및 지원

- 📖 **완전한 문서**: 이 파일
- 🐛 **Issues**: GitHub Issues
- 📧 **보안 문제**: security@example.com
- 💬 **토론**: GitHub Discussions

---

**Shadow API Scanner** - 더 안전한 웹 애플리케이션을 위하여 🛡️

**마지막 업데이트**: 2025-10-14
