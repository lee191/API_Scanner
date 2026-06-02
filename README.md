# 🔍 Route API Discovery

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/lee191/API_Scanner/actions/workflows/tests.yml/badge.svg)](https://github.com/lee191/API_Scanner/actions)

**웹 애플리케이션의 숨겨진 경로, API 엔드포인트, 민감정보를 자동으로 탐색하는 보안 분석 도구**

[기능](#-주요-기능) • [설치](#-설치) • [사용법](#-사용법) • [문서](#-문서)

</div>

---

## 📖 개요

Route API Discovery는 웹 애플리케이션 보안 분석을 위한 자동화 도구로, HTML과 JavaScript 소스 코드를 심층 분석하여 다음을 탐색합니다:

- 🔗 **페이지 경로 & API 엔드포인트** - 숨겨진 URL과 API 경로 발견
- 🔐 **민감정보 탐지** - 하드코딩된 토큰, 비밀번호, API 키, 개인정보 식별
- 🌐 **동적 분석** - 실제 브라우저에서 실행되는 네트워크 요청 캡처
- 📊 **다양한 출력 형식** - JSON, XLSX, HTML 리포트 생성

### 주요 특징

✅ **정적 분석** - JavaScript 코드에서 경로 패턴 추출  
✅ **동적 분석** - Playwright 기반 브라우저 자동화  
✅ **재귀 스캔** - 발견된 페이지를 자동으로 추가 탐색  
✅ **민감정보 탐지** - 이메일, 전화번호, 토큰, 개인정보 등 12가지 카테고리  
✅ **GUI & CLI** - 사용자 친화적인 인터페이스와 자동화 가능한 CLI  
✅ **다국어 지원** - 한국어/영어 UI
✅ **신뢰도 등급** - 모든 경로/API 후보에 high/medium/low confidence 부여, 정렬·필터 지원
✅ **well-known 탐색** - robots.txt / sitemap.xml에서 추가 경로 자동 수집

---

## 🎯 주요 기능


### 🔍 정적 분석

- **JavaScript 소스 분석**
  - 외부 `<script src>` 및 인라인 `<script>` 코드 수집
  - `fetch()`, `axios`, `XMLHttpRequest` 패턴 탐지
  - 동적 `import()` 및 `baseURL` 설정 추적
  - 문자열 리터럴에서 경로 패턴 추출

### 🌐 동적 분석 (Playwright)

- **실시간 브라우저 분석**
  - 네트워크 요청/응답 캡처
  - JavaScript 파일 본문 분석
  - 렌더링 후 DOM 검사
  - SPA 라우터 URL 감지
  
- **자동 상호작용** (옵션)
  - 자동 스크롤로 지연 로딩 콘텐츠 탐색
  - 링크, 버튼, 탭 자동 클릭
  - 제한된 액션 수로 안전한 탐색

### 🔐 민감정보 탐지

다음 카테고리의 민감정보를 자동으로 탐지합니다:

| 카테고리 | 예시 |
|---------|------|
| 🔑 토큰 | GitHub PAT, Stripe API Key, JWT |
| 🔒 자격증명 | password, api_key, secret_key |
| 📧 이메일 | user@example.com |
| 📱 전화번호 | 010-1234-5678 (한국) |
| 👤 이름 | 홍길동 (한글), John Doe |
| 🆔 계정 ID | ACCT-1234, usr_abc123 |
| 🔢 사용자 ID | user123, uid_456 |

### 🚀 고급 기능

- **재귀 스캔** - 발견된 페이지를 자동으로 추가 탐색 (깊이 제한 가능)
- **서브도메인 제어** - 특정 서브도메인 포함/제외
- **프록시 지원** - Burp Suite, OWASP ZAP 등과 연동
- **SSL 검증 우회** - 자체 서명 인증서 환경 지원
- **요청 제어** - 동시성, 지연 시간, 타임아웃 조정
- **배치 스캔** - 여러 URL 동시 분석

---

## 📋 요구 사항


### 시스템 요구사항

- **Python**: 3.10 이상
- **운영체제**: Windows, macOS, Linux
- **네트워크**: 대상 URL 접근 가능한 환경

### 필수 패키지

- `customtkinter>=5.2` - GUI 프레임워크
- `playwright>=1.44` - 브라우저 자동화
- `PySide6>=6.8` - Qt 기반 GUI (레거시)

---

## 🚀 설치

### 1. 저장소 클론

```bash
git clone https://github.com/lee191/API_Scanner.git
cd API_Scanner
```

### 2. 가상환경 생성 및 활성화

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. 패키지 설치

```bash
pip install -e .
```

### 4. Playwright 브라우저 설치

```bash
python -m playwright install chromium
```

---

## 💻 사용법

### CLI 기본 사용

```bash
# 기본 스캔
python route_api_discovery.py https://example.com

# JSON 출력
python route_api_discovery.py https://example.com --output result.json

# XLSX 출력
python route_api_discovery.py https://example.com --output result.xlsx

# HTML 리포트
python route_api_discovery.py https://example.com --output result.html
```

### 고급 스캔 옵션

```bash
# 재귀 스캔 (2단계 깊이)
python route_api_discovery.py https://example.com \
  --recursive-scan \
  --recursive-depth 2

# 동적 분석 활성화
python route_api_discovery.py https://example.com \
  --dynamic-analysis \
  --dynamic-wait 5 \
  --dynamic-actions

# 프록시 사용
python route_api_discovery.py https://example.com \
  --proxy http://127.0.0.1:8080

# JavaScript 파일 저장
python route_api_discovery.py https://example.com \
  --save-js-dir ./js-files

# SSL 검증 비활성화
python route_api_discovery.py https://example.com \
  --no-verify-ssl
```

### GUI 실행

```bash
# 방법 1: app.py 직접 실행
python app.py

# 방법 2: CLI 플래그
python route_api_discovery.py --gui

# 방법 3: 설치된 명령어
route-api-discovery-gui
```

---

## 🎨 GUI 사용 가이드

### 메인 화면 구성

1. **대상 URL 입력** - 한 줄에 하나씩 입력 (배치 스캔 가능)
2. **탐색 옵션**
   - 프록시 설정
   - 재귀 스캔 옵션
   - SSL 검증 설정
   - 요청 지연 조정
3. **동적 분석 설정**
   - Playwright 활성화
   - 자동 액션 제어
   - 대기 시간 설정
4. **결과 필터링**
   - 카테고리별 필터
   - 심각도 필터
   - 텍스트 검색

### 커스텀 헤더 설정

```
Authorization: Bearer token123
X-Custom-Header: value
Cookie: session=abc123
```

**주의**: 커스텀 헤더는 입력 URL과 동일한 오리진에만 전달됩니다.

### 언어 전환

GUI 우측 상단의 언어 메뉴에서 한국어/English 전환 가능

---

## 📊 출력 형식

### JSON 구조

```json
{
  "input_url": "https://example.com",
  "scanned_at": "2026-06-02T09:00:00+09:00",
  "summary": {
    "js_fetched": 15,
    "page_count": 42,
    "api_count": 28,
    "sensitive_total": 8,
    "sensitive_high_or_above": 3
  },
  "js_files": [...],
  "accessible_pages": [...],
  "accessible_apis": [...],
  "sensitive_findings": [
    {
      "category": "token",
      "field_name": "api_key",
      "value": "sk_live_...",
      "masked_value": "sk_...xyz",
      "severity": "critical",
      "source_url": "https://example.com/app.js",
      "line": 42,
      "context": "const apiKey = 'sk_live_...'"
    }
  ]
}
```

### XLSX 시트 구성

**단일 스캔:**
- 📋 요약
- 📄 JS 파일
- 🔄 동적 분석
- 🌐 페이지
- 🔌 API
- 🔐 민감정보

**배치 스캔:**
- 📊 배치 요약
- 📑 결과 목록
- 🔍 URL별 상세 시트 (최대 253개)

### HTML 리포트

브라우저에서 열 수 있는 인터랙티브 리포트:
- 요약 카드
- 필터링 가능한 테이블
- 민감정보 하이라이팅
- 다크/라이트 테마

---

## ⚙️ 주요 옵션

### 기본 옵션

| 옵션 | 설명 | 기본값 |
|-----|------|-------|
| `--output` | 출력 파일 경로 (.json/.xlsx/.html) | stdout |
| `--timeout` | HTTP 요청 타임아웃 (초) | 10 |
| `--max-workers` | 동시 요청 수 | 5 |
| `--request-delay` | 요청 간 지연 (초) | 0.0 |
| `--max-js-files` | 최대 JS 파일 수 | 100 |
| `--max-depth` | JS 재귀 탐색 깊이 | 3 |

### 재귀 스캔

| 옵션 | 설명 | 기본값 |
|-----|------|-------|
| `--recursive-scan` | 재귀 스캔 활성화 | False |
| `--recursive-depth` | 재귀 탐색 깊이 | 1 |
| `--include-subdomains` | 서브도메인 포함 | True |
| `--exclude-subdomains` | 제외할 서브도메인 (쉼표 구분) | - |

### 동적 분석

| 옵션 | 설명 | 기본값 |
|-----|------|-------|
| `--dynamic-analysis` | 동적 분석 활성화 | False |
| `--dynamic-wait` | 페이지 로드 후 대기 시간 (초) | 3 |
| `--dynamic-actions` | 자동 액션 활성화 | False |
| `--dynamic-action-limit` | 최대 액션 수 | 10 |
| `--dynamic-scroll-steps` | 스크롤 횟수 | 3 |
| `--dynamic-max-events` | 최대 네트워크 이벤트 수 | 500 |

### 프록시 & 보안

| 옵션 | 설명 | 기본값 |
|-----|------|-------|
| `--proxy` | 프록시 URL | - |
| `--no-verify-ssl` | SSL 검증 비활성화 | False |
| `--skip-probe` | 경로 접근성 확인 생략 | False |

### Well-Known & 신뢰도

| 옵션 | 설명 | 기본값 |
|-----|------|-------|
| `--scan-well-known` / `--no-scan-well-known` | robots.txt/sitemap.xml 경로 탐색 | 활성 |
| `--min-confidence {low,medium,high}` | 지정 신뢰도 미만 경로/API 제외 | low |

---

## 🧪 테스트

전체 테스트 스위트 실행:

```bash
python -m unittest discover -s tests -v
```

특정 테스트만 실행:

```bash
python -m unittest tests.test_route_api_discovery -v
```

### 테스트 커버리지

- ✅ 정적 분석 로직
- ✅ 동적 분석 통합
- ✅ 민감정보 탐지 정확도
- ✅ URL 스코프 검증
- ✅ 출력 형식 검증
- ✅ GUI 로직

---

## 📁 프로젝트 구조

```
API_Scanner/
├── route_api_discovery.py      # 핵심 스캔 엔진 & CLI
├── route_api_discovery_ctk.py  # CustomTkinter GUI
├── route_api_discovery_qt.py   # PySide6 GUI (레거시)
├── app.py                       # GUI 진입점
├── pyproject.toml               # 프로젝트 설정
├── GUI/
│   ├── launcher.py              # GUI 런처 헬퍼
│   └── __init__.py
├── tests/
│   ├── test_route_api_discovery.py
│   ├── test_code_review_alignment.py
│   ├── test_output_validation.py
│   └── ...
├── .github/
│   └── workflows/
│       └── tests.yml            # GitHub Actions CI
└── README.md
```

---

## ⚠️ 보안 및 윤리적 사용

### 중요 사항

⚠️ **이 도구는 반드시 허가된 대상에만 사용해야 합니다.**

### 사용 시 주의사항

1. **권한 확인**
   - 본인이 소유한 웹사이트
   - 명시적 허가를 받은 대상
   - 취약점 제보 프로그램 참여 시

2. **결과 파일 관리**
   - 민감정보 원문이 포함될 수 있음
   - 암호화된 저장소에 보관
   - 공유 시 마스킹 처리 필수

3. **동적 액션 주의**
   - `--dynamic-actions`는 상태 변경 가능
   - 프로덕션 환경에서는 비활성화 권장
   - 테스트 환경에서만 제한적 사용

4. **프록시 & SSL**
   - `--proxy`와 `--no-verify-ssl`은 신뢰 환경에서만
   - 중간자 공격 위험 인지
   - 민감한 정보 전송 시 주의

### 법적 책임

- 사용자는 해당 도구의 사용에 대한 모든 책임을 집니다
- 무단 접근, 데이터 수집은 법적 처벌 대상입니다
- 저작권 및 개인정보 보호 법규 준수 필수

---

## 🤝 기여하기

기여는 언제나 환영합니다!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### 개발 환경 설정

```bash
git clone https://github.com/lee191/API_Scanner.git
cd API_Scanner
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -e .
python -m playwright install chromium
python -m unittest discover -s tests -v
```

---

## 📝 라이선스

이 프로젝트는 [MIT License](LICENSE)를 따릅니다.

```
MIT License

Copyright (c) 2026 Codex

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
```

---

## 📞 지원 & 문의

- **이슈 제보**: [GitHub Issues](https://github.com/lee191/API_Scanner/issues)
- **보안 취약점**: 이슈 트래커가 아닌 비공개로 제보해주세요

---

<div align="center">

**Made with ❤️ for Security Researchers**

⭐ Star this repository if you find it useful!

</div>
