# 🧪 Shadow API Scanner 테스트 가이드

Shadow API Scanner를 취약한 테스트 애플리케이션으로 테스트하는 가이드입니다.

## 📋 사전 요구사항

### 호스트 시스템
- Python 3.8+
- pip

### Docker (테스트 앱용)
- Docker Desktop 설치
- Docker Compose V2+

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# Python 의존성 설치
pip install -r requirements.txt

# 테스트 앱 시작 (Docker)
# Windows:
docker-run.bat

# Linux/Mac:
chmod +x docker-run.sh
./docker-run.sh

# 테스트 앱 상태 확인
docker ps | grep vulnerable-test-app

# 로그 확인
docker logs vulnerable-test-app
```

### 2. 자동 테스트 실행

#### Windows:
```bash
test-scripts\run-test.bat
```

#### Linux/Mac:
```bash
chmod +x test-scripts/run-test.sh
./test-scripts/run-test.sh
```

### 3. 수동 테스트

#### JavaScript 분석만 실행
```bash
python main.py analyze test-app/static \
    --base-url http://localhost:5000 \
    --recursive
```

#### 전체 스캔 (JS 분석 + 취약점 스캔)
```bash
python main.py full-scan http://localhost:5000 \
    --js-path test-app/static \
    --scan-vulns \
    --output output
```

## 📊 예상 테스트 결과

### 발견될 API 엔드포인트 (10개 이상)

| 엔드포인트 | 메서드 | 소스 |
|-----------|--------|------|
| `/api/v1/users` | GET | js_analysis |
| `/api/v1/user/<id>` | GET | js_analysis |
| `/api/v1/products` | GET | js_analysis |
| `/api/v1/auth/login` | POST | js_analysis |
| `/api/v1/search` | GET | js_analysis |
| `/api/v1/upload` | POST | js_analysis |
| `/api/v1/user/delete` | POST | js_analysis |
| `/api/v1/secure/data` | GET | js_analysis |
| `/api/internal/admin/users` ⚠️ | GET | js_analysis |
| `/api/internal/debug/config` ⚠️ | GET | js_analysis |

⚠️ = Shadow API (문서화되지 않은 내부 API)

### 발견될 보안 취약점 (10개 이상)

| 취약점 유형 | 심각도 | 예상 개수 | 영향받는 엔드포인트 |
|------------|--------|-----------|-------------------|
| SQL Injection | 🔴 CRITICAL | 2+ | `/api/v1/user/<id>` |
| Missing Authentication | 🟠 HIGH | 5+ | 대부분의 엔드포인트 |
| CORS Misconfiguration | 🟠 HIGH | 1+ | 모든 엔드포인트 |
| XSS | 🟠 HIGH | 1+ | `/api/v1/search` |
| Sensitive Data Exposure | 🟠 HIGH | 3+ | `/api/v1/user/*`, `/api/internal/*` |
| Insecure Authentication | 🟠 HIGH | 1+ | `/api/v1/auth/login` |
| Missing Rate Limiting | 🟡 MEDIUM | 5+ | 모든 엔드포인트 |

## 🔍 상세 테스트 시나리오

### 시나리오 1: JavaScript 정적 분석

```bash
python main.py analyze test-app/static --base-url http://localhost:5000 --recursive
```

**검증 포인트:**
- ✅ `app.js` 파일 분석
- ✅ fetch() 패턴 탐지
- ✅ XMLHttpRequest 패턴 탐지
- ✅ axios 패턴 탐지 (주석 포함)
- ✅ 동적 URL (템플릿 리터럴) 탐지
- ✅ Shadow API 엔드포인트 발견

**예상 출력:**
```
[1/3] JavaScript 분석 중...
파일 분석: 100%|████████| 1/1
  ✓ 발견된 엔드포인트: 10-15개
```

### 시나리오 2: 취약점 스캔

```bash
python main.py full-scan http://localhost:5000 \
    --js-path test-app/static \
    --scan-vulns
```

**검증 포인트:**

**SQL Injection 탐지:**
```bash
# 수동 테스트
curl "http://localhost:5000/api/v1/user/1'"
# SQL 에러 메시지 반환 → 취약점 확인
```

**XSS 탐지:**
```bash
# 수동 테스트
curl "http://localhost:5000/api/v1/search?q=<script>alert('XSS')</script>"
# 스크립트가 그대로 반환 → 취약점 확인
```

**인증 누락 탐지:**
```bash
# 수동 테스트
curl http://localhost:5000/api/v1/users
# 인증 없이 사용자 목록 반환 → 취약점 확인
```

**민감 데이터 노출:**
```bash
# 수동 테스트
curl http://localhost:5000/api/v1/user/1
# 비밀번호, API 키 노출 → 취약점 확인
```

### 시나리오 3: 리포트 생성 및 검증

```bash
# 스캔 실행
python main.py full-scan http://localhost:5000 --js-path test-app/static --scan-vulns

# 리포트 확인
ls -lh output/

# JSON 리포트 분석
cat output/full_scan_*.json | jq '.statistics'

# 취약점 카운트 확인
cat output/full_scan_*.json | jq '.vulnerabilities | length'
```

**검증 포인트:**
- ✅ JSON, HTML, Markdown 3가지 형식 생성
- ✅ 통계 정보 정확성
- ✅ 취약점 상세 정보 포함
- ✅ 권장사항 포함

## 🛠️ 테스트 앱 API 수동 탐색

### 정상 API 호출

```bash
# 제품 목록 조회
curl http://localhost:5000/api/v1/products

# 특정 사용자 조회
curl http://localhost:5000/api/v1/user/1

# 검색
curl "http://localhost:5000/api/v1/search?q=test"
```

### 취약점 악용 테스트

**⚠️ 경고: 이 테스트는 로컬 환경에서만 수행하세요!**

```bash
# SQL Injection 테스트
curl "http://localhost:5000/api/v1/user/1 OR 1=1"

# SQL Injection으로 모든 사용자 정보 유출
curl "http://localhost:5000/api/v1/user/1' OR '1'='1"

# XSS 페이로드
curl "http://localhost:5000/api/v1/search?q=<script>alert('XSS')</script>"

# Shadow API 접근
curl http://localhost:5000/api/internal/admin/users
curl http://localhost:5000/api/internal/debug/config

# URL에 비밀번호 노출 (취약한 로그인)
curl -X POST "http://localhost:5000/api/v1/auth/login?username=admin&password=admin123"
```

## 📈 성능 벤치마크

예상 실행 시간 (로컬 환경):

| 작업 | 파일/엔드포인트 수 | 예상 시간 |
|-----|------------------|----------|
| JavaScript 분석 | 1개 파일 | < 1초 |
| 엔드포인트 수집 | 10개 | < 1초 |
| 취약점 스캔 | 10개 엔드포인트 | 30-60초 |
| 리포트 생성 | - | < 1초 |
| **전체 스캔** | **1파일 + 10엔드포인트** | **30-60초** |

## 🧹 정리

### 테스트 환경 중지

```bash
# 빠른 정리 (Windows)
docker-stop.bat

# 빠른 정리 (Linux/Mac)
chmod +x docker-stop.sh
./docker-stop.sh

# 또는 수동으로
docker stop vulnerable-test-app
docker rm vulnerable-test-app

# 이미지까지 삭제
docker rmi vulnerable-test-app:latest
```

### 출력 파일 정리

```bash
# Windows
del /Q output\*.*

# Linux/Mac
rm -rf output/*
```

## 🐛 문제 해결

### Python 의존성 오류

```bash
# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 의존성 재설치
pip install -r requirements.txt
```

### 테스트 앱 접속 불가

```bash
# 상태 확인
docker ps

# 로그 확인
docker logs vulnerable-test-app
docker logs -f vulnerable-test-app  # 실시간

# 포트 충돌 확인 (Windows)
netstat -ano | findstr :5000

# 포트 충돌 확인 (Linux/Mac)
lsof -i :5000

# 다른 포트로 실행
docker stop vulnerable-test-app
docker rm vulnerable-test-app
docker run -d --name vulnerable-test-app -p 5001:5000 -e FLASK_ENV=development vulnerable-test-app:latest
python main.py full-scan http://localhost:5001 --js-path test-app/static
```

### mitmproxy 관련 오류

mitmproxy는 프록시 모드에서만 필요합니다. 테스트 스캔에서는 사용하지 않으므로 오류가 발생해도 무시하세요.

### 취약점이 발견되지 않는 경우

```bash
# 테스트 앱이 실제로 실행 중인지 확인
curl http://localhost:5000

# 네트워크 연결 확인
ping localhost

# 상세 로그 확인 (main.py 수정)
# logging.basicConfig(level=logging.DEBUG)
```

## 📊 리포트 예시

### 콘솔 출력

```
============================================================
[✓] 스캔 완료!

📊 결과 요약:
  • 엔드포인트: 10개
  • 취약점: 15개

📁 생성된 리포트:
  • JSON: output/full_scan_20250113_120000.json
  • HTML: output/full_scan_20250113_120000.html
  • MARKDOWN: output/full_scan_20250113_120000.md
============================================================
```

### HTML 리포트 내용

- 📊 대시보드 (통계)
- 🌐 발견된 엔드포인트 목록
- 🛡️ 보안 취약점 상세
  - 심각도별 분류
  - CWE 매핑
  - 증거 및 권장사항

## ✅ 테스트 체크리스트

### 설치 및 환경
- [ ] Python 3.8+ 설치 확인
- [ ] pip 의존성 설치
- [ ] Docker 설치 및 실행 확인
- [ ] 테스트 앱 시작 확인

### JavaScript 분석
- [ ] app.js 파일 탐지
- [ ] 10개 이상 엔드포인트 발견
- [ ] Shadow API 엔드포인트 발견
- [ ] 동적 URL 패턴 인식

### 취약점 스캔
- [ ] SQL Injection 탐지
- [ ] XSS 탐지
- [ ] 인증 누락 탐지
- [ ] CORS 오구성 탐지
- [ ] 민감 데이터 노출 탐지

### 리포트 생성
- [ ] JSON 리포트 생성
- [ ] HTML 리포트 생성
- [ ] Markdown 리포트 생성
- [ ] 통계 정보 정확성

---

**테스트 완료 후 피드백 환영합니다!** 🔍🛡️
