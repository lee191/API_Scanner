# Route API Discovery

`Route API Discovery`는 대상 URL의 HTML과 JavaScript를 분석해 페이지 경로, API 엔드포인트, 하드코딩된 민감 정보 후보를 찾아내는 도구입니다. CLI와 PySide6 GUI를 제공하며 결과를 JSON, XLSX, HTML 형식으로 저장할 수 있습니다.

## 주요 기능

- HTML의 외부 `<script src>`와 인라인 `<script>` 분석
- JavaScript 문자열, `fetch`, `axios`, `baseURL`, `import()` 패턴에서 경로와 API 후보 추출
- 페이지/API 후보 접근성 프로브
- 재귀 스캔, 서브도메인 포함/제외, 제외 서브도메인 설정
- 이메일, 전화번호, 이름, 계정 ID, 사용자 ID, 비밀번호, 토큰 등 민감 정보 후보 탐지
- 프록시, SSL 검증 비활성화, 요청 지연, 동시 요청 수 조정
- GUI의 다중 URL 배치 스캔, 요청 헤더 입력, 결과 필터링, 한국어/영어 전환, 다크 모드

## 요구 사항

- Python 3.10 이상
- PySide6
- 대상 URL에 접근 가능한 네트워크 환경

## 설치

```bash
git clone <REPO_URL>
cd <REPO_DIR>
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e .
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -e .
```

## 빠른 시작

### CLI

```bash
python route_api_discovery.py https://example.com
python route_api_discovery.py https://example.com --output result.json
python route_api_discovery.py https://example.com --output result.xlsx
python route_api_discovery.py https://example.com --output result.html
python route_api_discovery.py https://example.com --recursive-scan --recursive-depth 2
python route_api_discovery.py https://example.com --proxy http://127.0.0.1:8080
python route_api_discovery.py https://example.com --save-js-dir js-files
python route_api_discovery.py https://example.com --no-verify-ssl
```

`--recursive-scan`과 `--skip-probe`는 함께 사용할 수 없습니다.

### GUI

```bash
python app.py
python route_api_discovery.py --gui
route-api-discovery-gui
```

GUI 사용:

- 대상 URL은 한 줄에 하나씩 입력합니다.
- 요청 헤더는 `Header-Name: value` 형식으로 입력합니다.
- 탐색 옵션에서 프록시, 재귀 스캔, SSL 검증, 요청 지연 등을 조정할 수 있습니다.
- 언어 메뉴에서 한국어와 영어를 전환할 수 있습니다.

## 주요 옵션

- `--max-js-files`: 가져올 JS 파일의 최대 개수
- `--max-depth`: JS 재귀 탐색 깊이
- `--timeout`: HTTP 타임아웃(초)
- `--output`: 결과 파일 경로. `.json`, `.xlsx`, `.html` 또는 확장자 없음 지원
- `--recursive-scan`: 접근 가능한 페이지를 대상으로 재귀 탐색
- `--recursive-depth`: 재귀 탐색 단계 수
- `--include-subdomains` / `--no-include-subdomains`: 서브도메인 포함 여부
- `--exclude-subdomains`: 탐색에서 제외할 서브도메인 목록
- `--max-workers`: 동시 요청 작업 수
- `--request-delay`: 요청 시작 간 최소 지연 시간(초)
- `--proxy`: 프록시 URL
- `--save-js-dir`: 가져온 JS 파일 본문을 저장할 디렉터리
- `--no-verify-ssl`: SSL 인증서 검증 비활성화
- `--skip-probe`: 후보 경로 접근성 확인 생략
- `--debug`: 오류 발생 시 traceback 출력

## 출력 형식

### JSON

단일 스캔 결과에는 다음 정보가 포함됩니다.

- `input_url`
- `scanned_at`
- `js_files`
- `js_discovered_urls`
- `accessible_pages`
- `accessible_apis`
- `all_pages`
- `all_apis`
- `hardcoded_findings`
- `sensitive_findings`
- `summary`
- `recursive_*`

GUI 배치 스캔 결과는 `results` 배열과 전체 `summary`를 포함합니다.

### XLSX

단일 스캔:

- `요약`
- `JS 파일`
- `페이지`
- `API`
- `민감정보`

배치 스캔:

- `배치 요약`
- `결과 목록`
- URL별 상세 시트

### HTML

HTML 출력은 브라우저에서 열어 확인할 수 있는 리포트입니다.

## 프로젝트 구조

- `route_api_discovery.py`: 핵심 스캔 로직과 CLI
- `route_api_discovery_qt.py`: PySide6 GUI
- `app.py`: GUI 실행 진입점
- `GUI/launcher.py`: GUI 런처 헬퍼
- `tests/`: 단위 테스트 코드

## 테스트

```bash
python -m unittest discover -s tests -v
```

GitHub Actions에서도 컴파일 검증과 단위 테스트를 실행합니다.

## 사용 시 주의

- 반드시 허가된 대상에만 사용하세요.
- 결과 파일에는 실제 URL과 민감 정보 후보가 포함될 수 있으므로 공유에 주의하세요.
- `--proxy`와 `--no-verify-ssl`은 신뢰할 수 있는 환경에서만 사용하세요.
- `--recursive-scan`과 `--skip-probe`는 함께 사용할 수 없습니다.

## 라이선스

이 프로젝트는 [MIT License](LICENSE)를 따릅니다.
