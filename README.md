# 🔍 Shadow API Scanner

웹 애플리케이션의 숨겨진/문서화되지 않은 API를 탐색하고 보안 취약점을 분석하는 모의 침투 테스트 도구

## 🎯 주요 기능

- **🌐 네트워크 트래픽 분석**: mitmproxy를 사용한 HTTP/HTTPS 트래픽 캡처
- **📜 JavaScript 정적 분석**: JS 파일에서 API 엔드포인트 자동 추출
- **📊 API 엔드포인트 수집**: 중복 제거 및 정규화된 엔드포인트 목록
- **🛡️ 보안 취약점 스캔**: OWASP Top 10 기반 취약점 탐지
  - 인증/권한 검사
  - CORS 오구성
  - 민감 데이터 노출
  - SQL Injection
  - XSS
  - Rate Limiting
- **📄 다양한 리포트 형식**: JSON, HTML, Markdown 리포트 생성

## 📦 설치

### 요구사항

- Python 3.8+
- pip

### 설치 방법

```bash
# 저장소 클론
git clone <repository-url>
cd Shadow-API

# 의존성 설치
pip install -r requirements.txt

# Playwright 브라우저 설치 (선택사항)
playwright install
```

## 🧪 테스트 환경 (권장)

취약한 테스트 웹 애플리케이션으로 도구를 테스트:

```bash
# 1. 테스트 앱 시작 (Docker)
# Windows
docker-run.bat
# Linux/Mac
chmod +x docker-run.sh && ./docker-run.sh

# 2. 빠른 테스트 (Windows)
test-scripts\run-test.bat

# 3. 빠른 테스트 (Linux/Mac)
chmod +x test-scripts/run-test.sh
./test-scripts/run-test.sh

# 4. 수동 테스트
python main.py full-scan http://localhost:5000 \
    --js-path test-app/static --scan-vulns

# 5. 정리
# Windows: docker-stop.bat
# Linux/Mac: ./docker-stop.sh
```

자세한 내용은 [TESTING.md](TESTING.md) 참조

## 🚀 사용법

### 1. 프록시 모드 - 네트워크 트래픽 캡처

```bash
python main.py proxy --host 127.0.0.1 --port 8080
```

브라우저 프록시 설정:
- 호스트: 127.0.0.1
- 포트: 8080
- HTTPS 프록시 활성화

웹 애플리케이션을 탐색하면 모든 API 호출이 자동으로 캡처됩니다.

### 2. JavaScript 분석 모드

단일 파일 분석:
```bash
python main.py analyze app.js --base-url https://example.com
```

디렉토리 분석 (재귀):
```bash
python main.py analyze ./src --base-url https://example.com --recursive
```

### 3. 전체 스캔 (권장)

```bash
python main.py full-scan https://example.com \
  --js-path ./javascript \
  --scan-vulns \
  --output ./reports
```

옵션:
- `--js-path`: JavaScript 파일/디렉토리 경로
- `--scan-vulns`: 취약점 스캔 수행 (기본: true)
- `--no-scan-vulns`: 취약점 스캔 건너뛰기
- `--output`: 리포트 출력 디렉토리

## 📊 출력 예시

### 콘솔 출력

```
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              🔍 Shadow API Scanner v1.0                  ║
║         Penetration Testing Tool for API Discovery       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

[*] 전체 스캔 시작: https://example.com

[1/3] JavaScript 분석 중...
파일 분석: 100%|████████████████████| 45/45 [00:12<00:00]
  ✓ 발견된 엔드포인트: 87개

[2/3] 보안 취약점 스캔 중...
엔드포인트 스캔: 100%|████████████████████| 87/87 [01:23<00:00]
  ✓ 발견된 취약점: 12개
    - Critical: 2개
    - High: 5개

[3/3] 리포트 생성 중...
[+] JSON report: output/full_scan_20250101_120000.json
[+] HTML report: output/full_scan_20250101_120000.html
[+] Markdown report: output/full_scan_20250101_120000.md

============================================================
[✓] 스캔 완료!

📊 결과 요약:
  • 엔드포인트: 87개
  • 취약점: 12개

📁 생성된 리포트:
  • JSON: output/full_scan_20250101_120000.json
  • HTML: output/full_scan_20250101_120000.html
  • MARKDOWN: output/full_scan_20250101_120000.md
============================================================
```

### HTML 리포트

HTML 리포트는 아름답게 포맷된 대시보드 형태로 생성됩니다:
- 📊 통계 대시보드
- 🌐 발견된 API 엔드포인트 목록
- 🛡️ 보안 취약점 상세 정보
- 💡 권장사항

## 🏗️ 프로젝트 구조

```
Shadow-API/
├── src/
│   ├── proxy/              # 프록시 서버 및 트래픽 캡처
│   │   ├── capture.py
│   │   └── __init__.py
│   ├── analyzer/           # JavaScript 정적 분석
│   │   ├── js_analyzer.py
│   │   ├── endpoint_collector.py
│   │   └── __init__.py
│   ├── scanner/            # 보안 취약점 스캐너
│   │   ├── vulnerability_scanner.py
│   │   └── __init__.py
│   ├── reporter/           # 리포트 생성
│   │   ├── report_generator.py
│   │   └── __init__.py
│   └── utils/              # 공통 유틸리티
│       ├── models.py
│       ├── config.py
│       └── __init__.py
├── config/
│   └── config.yaml         # 설정 파일
├── output/                 # 리포트 출력 디렉토리
├── tests/                  # 테스트
├── main.py                 # CLI 진입점
├── requirements.txt        # Python 의존성
└── README.md
```

## ⚙️ 설정

`config/config.yaml` 파일에서 설정을 커스터마이즈할 수 있습니다:

```yaml
# 프록시 설정
proxy:
  host: "127.0.0.1"
  port: 8080
  timeout: 30

# JavaScript 분석 패턴
js_analysis:
  patterns:
    - "fetch("
    - "axios."
    - "XMLHttpRequest"

# 취약점 스캐너 설정
scanner:
  checks:
    - authentication
    - authorization
    - cors
    - sql_injection
    - xss
  timeout: 10
  max_retries: 3

# 출력 설정
output:
  directory: "output"
  formats:
    - "json"
    - "html"
    - "markdown"
```

## 🛡️ 탐지 가능한 취약점

| 취약점 유형 | 심각도 | CWE |
|------------|--------|-----|
| Missing Authentication | HIGH | CWE-306 |
| Insecure Authentication | HIGH | CWE-319 |
| CORS Misconfiguration | HIGH/MEDIUM | CWE-942 |
| Sensitive Data Exposure | HIGH/MEDIUM | CWE-200 |
| SQL Injection | CRITICAL | CWE-89 |
| XSS (Cross-Site Scripting) | HIGH | CWE-79 |
| Missing Rate Limiting | MEDIUM | CWE-770 |

## 🔒 법적 고지사항

**⚠️ 중요: 이 도구는 방어적 보안 목적으로만 사용되어야 합니다.**

- ✅ 자신이 소유하거나 명시적 허가를 받은 시스템에만 사용
- ✅ 모의 침투 테스트 및 보안 평가 목적
- ✅ 취약점 발견 및 수정을 위한 교육적 목적
- ❌ 무단 접근, 데이터 탈취, 악의적 목적 사용 금지

사용자는 이 도구의 사용으로 인한 모든 법적 책임을 집니다.

## 🤝 기여

버그 리포트, 기능 제안, 풀 리퀘스트를 환영합니다!

## 📝 라이선스

이 프로젝트는 교육 및 보안 연구 목적으로 제공됩니다.

## 🔄 향후 계획

- [ ] URL 크롤링 기능
- [ ] WebSocket API 지원
- [ ] GraphQL 엔드포인트 분석
- [ ] API 문서 자동 생성
- [ ] CI/CD 통합
- [ ] Docker 이미지 제공
- [ ] 추가 취약점 체크 (SSRF, XXE, etc.)
- [ ] 머신러닝 기반 API 패턴 인식

## 📧 연락처

문의사항이나 보안 이슈 발견 시 제보해주세요.

---

**Shadow API Scanner** - 더 안전한 웹 애플리케이션을 위하여 🛡️
