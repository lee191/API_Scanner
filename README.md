# Route API Discovery

HTML과 JavaScript에서 페이지 경로와 API 엔드포인트 후보를 추출하고, 접근 가능 여부까지 확인해 JSON 또는 XLSX로 정리하는 Python 도구입니다.  
CLI로 빠르게 단일 대상을 점검할 수 있고, PySide6 기반 GUI로 배치 스캔, 결과 비교, 필터링, 로그 확인까지 처리할 수 있습니다.

## 주요 기능

- HTML의 `<script src>`와 인라인 스크립트를 분석해 JS 파일을 수집
- JavaScript/HTML에서 페이지 경로와 API 엔드포인트 후보 추출
- 추출한 후보에 대해 접근 가능 여부와 상태 코드 프로브
- 접근 가능한 페이지를 기준으로 재귀 스캔 수행
- GUI에서 다중 URL 배치 실행, 로그 확인, 테이블 필터, 다크 모드 지원
- GUI 언어 전환 지원: `한국어` / `English`
- 결과를 `JSON`, `XLSX`, 또는 확장자 없는 JSON 파일로 저장

## 기술 스택

- Python 3.10+
- PySide6
- Python 표준 라이브러리 기반 구현

## 설치

```bash
python -m venv .venv
```

Windows PowerShell:

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

가장 단순한 실행:

```bash
python route_api_discovery.py https://example.com
```

출력 파일을 Excel로 저장:

```bash
python route_api_discovery.py https://example.com --output result.xlsx
```

재귀 스캔 포함:

```bash
python route_api_discovery.py https://example.com --recursive-scan --recursive-depth 2
```

서브도메인을 제외하고 정확히 같은 호스트만 대상으로 재귀 스캔:

```bash
python route_api_discovery.py https://example.com --recursive-scan --recursive-depth 2 --no-include-subdomains
```

특정 서브도메인을 제외하고 스캔:

```bash
python route_api_discovery.py https://example.com --recursive-scan --exclude-subdomains cdn.example.com,static.example.com
```

요청 수와 딜레이 조정:

```bash
python route_api_discovery.py https://example.com --max-workers 4 --request-delay 0.5
```

### GUI

다음 중 하나로 GUI를 실행할 수 있습니다.

```bash
python app.py
```

```bash
python route_api_discovery.py --gui
```

설치 후 엔트리포인트 사용:

```bash
route-api-discovery-gui
```

GUI에서는 한 줄에 하나씩 URL을 입력해 여러 대상을 한 번에 스캔할 수 있습니다.  
`탐색 옵션 > 언어`에서 `한국어` 또는 `English`를 선택할 수 있습니다.

## 주요 CLI 옵션

- `--gui`: PySide6 GUI 실행
- `--max-js-files`: 수집할 JS 파일 최대 개수
- `--max-depth`: JS 재귀 탐색 깊이
- `--timeout`: HTTP 타임아웃(초)
- `--output`: 결과 저장 경로 (`.json`, `.xlsx`, 또는 확장자 없음)
- `--skip-probe`: 추출한 경로의 접근성 확인 생략
- `--recursive-scan`: 접근 가능한 페이지(200)를 기준으로 재귀 스캔
- `--recursive-depth`: 재귀 단계 수
- `--include-subdomains` / `--no-include-subdomains`: 동일 사이트의 서브도메인 포함 여부
- `--exclude-subdomains`: 탐색에서 제외할 서브도메인 호스트 목록(쉼표로 여러 개 입력 가능)
- `--max-workers`: 동시 요청 작업 수
- `--request-delay`: 요청 시작 간 최소 딜레이(초)
- `--no-verify-ssl`: SSL 인증서 검증 비활성화
- `--debug`: 오류 발생 시 traceback 출력

주의:

- `--skip-probe`와 `--recursive-scan`은 함께 사용할 수 없습니다.
- `--no-verify-ssl`은 신뢰할 수 있는 대상에서만 사용해야 합니다.

## 출력 형식

### JSON

단일 CLI 실행 시에는 단일 결과 객체가 저장됩니다.  
GUI 배치 실행 시에는 `input_urls`, `results`, `summary`를 포함한 배치 결과가 저장됩니다.

주요 필드 예시:

- `input_url`
- `js_files`
- `all_pages`
- `all_apis`
- `accessible_pages`
- `accessible_apis`
- `summary`
- `recursive_*`

### XLSX

단일 결과 저장 시:

- `요약`
- `JS 파일`
- `페이지`
- `API`

배치 결과 저장 시:

- `배치 요약`
- `결과 목록`
- `상세 ...`

## 프로젝트 구조

- `route_api_discovery.py`: 핵심 스캔 로직과 CLI 진입점
- `route_api_discovery_qt.py`: PySide6 GUI
- `app.py`: GUI 실행용 래퍼
- `GUI/launcher.py`: GUI 런처
- `tests/`: 회귀 테스트

## 테스트

```bash
python -m unittest discover -s tests -v
```

현재 테스트에는 다음 흐름이 포함됩니다.

- 출력 형식 검증
- 스캔 취소 동작
- 코드 리뷰 반영 항목 회귀 방지
- GUI 언어 전환 동작

## 보안 및 사용 시 주의사항

- 허가받은 대상에 대해서만 사용하세요.
- 로컬호스트 및 사설 IP 대역은 차단하도록 설계되어 있습니다.
- 결과 파일에는 실제 스캔 대상 URL, 상태 코드, 오류 메시지가 포함될 수 있으므로 공유 전에 검토가 필요합니다.
- 프로브를 생략하면 접근 가능 여부 정보가 제한될 수 있습니다.

## 라이선스

라이선스는 아직 지정되지 않았습니다. 공개 배포 전 `LICENSE` 파일을 추가하는 것을 권장합니다.
