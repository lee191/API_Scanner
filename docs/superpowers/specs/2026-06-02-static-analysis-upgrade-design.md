# 정적 분석 로직 업그레이드 설계

- **작성일**: 2026-06-02
- **대상 모듈**: `route_api_discovery.py`, `route_api_discovery_ctk.py`, `tests/`
- **목표**: 경로/API 엔드포인트 탐지 강화 (넓은 프레임워크/패턴 커버리지) + confidence 레벨 기반 정렬·필터

---

## 1. 배경 및 목표

현재 정적 분석은 평면 정규식 튜플(`API_PATTERN_RE_LIST`)과 `QUOTED_PATH_RE`, axios 객체 추출로 구성되어 있다. 커버하는 패턴은 `fetch`, `axios.*`, `url:`, `.open()`, `baseURL`, `/api|graphql|rest/`, WebSocket/EventSource, `ws://`/`wss://`, import 패턴이다.

`Candidate`는 `url, path, kind, sources` 필드만 가지며 탐지 신뢰도 개념이 없다.

**업그레이드 목표**:
1. 전통 웹·모던 SPA·프레임워크 메타데이터를 넓게 커버하는 신규 디텍터 추가
2. 모든 후보에 confidence 레벨(high/medium/low) 부여 — 모두 탐지하되 등급으로 구분
3. confidence를 출력(JSON/XLSX/HTML)과 GUI에서 정렬·필터 가능하게 노출
4. well-known 리소스(`/robots.txt`, `/sitemap.xml`) 디스커버리 추가

**비목표 (YAGNI)**:
- 외부 설정 파일 기반 플러그형 분석 프레임워크
- 디텍터 로직의 별도 모듈 분리 (기존 단일 모듈 패턴 유지)

---

## 2. 아키텍처: 구조화된 디텍터 레지스트리

### 2.1 Detector 데이터클래스

```python
@dataclass(frozen=True)
class Detector:
    name: str                     # "fetch", "jquery_ajax", "next_data"
    confidence: str               # "high" | "medium" | "low"
    kind: str                     # "api" | "page" | "auto" (auto → classify_candidate)
    pattern: Optional[Pattern] = None      # 단순 정규식 디텍터
    extractor: Optional[Callable] = None   # 복잡 추출기 (jQuery 객체, GraphQL, JSON blob)
```

- 단순 패턴 디텍터는 `pattern`에 컴파일된 정규식을 두고 `value` 그룹을 추출한다.
- 복잡 디텍터는 `extractor(text, base_url, *, allow_disallowed_host) -> List[str]` 시그니처의 함수를 둔다.
- 디텍터당 정확히 하나(`pattern` 또는 `extractor`)만 설정한다.

### 2.2 레지스트리

```python
DETECTOR_REGISTRY: Tuple[Detector, ...] = (...)
```

`collect_path_candidates`는 기존 개별 루프 대신 레지스트리를 순회한다. 각 디텍터에 대해:
1. 매치/추출로 raw value 수집
2. `_resolve_candidate_for_detection`으로 절대 URL 해석
3. `url_matches_scope`, static asset, MIME 필터 적용
4. `kind == "auto"`면 `classify_candidate`로 분류, 아니면 디텍터의 `kind` 사용
5. `add_candidate_with_confidence(bucket, url, source, kind, confidence, detector_name)` 호출

### 2.3 Candidate 확장

```python
@dataclass
class Candidate:
    url: str
    path: str
    kind: str
    sources: Set[str] = field(default_factory=set)
    confidence: str = "low"               # 신규
    detectors: Set[str] = field(default_factory=set)  # 신규
```

- `sources`: 어느 파일/HTML에서 왔는지 (기존)
- `detectors`: 어떤 디텍터 패턴이 잡았는지 (신규)

### 2.4 병합 규칙

같은 URL을 여러 디텍터가 탐지하면:
- `confidence = max(기존, 신규)` — 등급 순위 `high(3) > medium(2) > low(1)`
- `detectors`는 합집합, `sources`도 합집합 (기존 동작)

헬퍼:
```python
CONFIDENCE_RANK = {"low": 1, "medium": 2, "high": 3}

def merge_confidence(current: str, incoming: str) -> str:
    return incoming if CONFIDENCE_RANK[incoming] > CONFIDENCE_RANK[current] else current
```

### 2.5 Confidence 등급 기준

- **high**: 명시적 HTTP 호출 + 리터럴 URL
  (fetch, axios.*, jQuery ajax/get/post, XHR `.open()`, WebSocket/EventSource, HTMX 속성, 서비스 클라이언트, OpenAPI paths, sitemap `<loc>`)
- **medium**: 프레임워크 라우트 설정, GraphQL, 프레임워크 데이터 blob, form action, socket.io, robots.txt 경로, Next.js 데이터
- **low**: 범용 경로 휴리스틱(`QUOTED_PATH_RE`), 임의 JSON state(`__INITIAL_STATE__` 등)에서 추출한 URL

---

## 3. 신규 디텍터 카탈로그

기존 high 신뢰도 패턴은 그대로 유지하고 다음을 추가한다.

### 3.1 전통 웹

| 디텍터 | confidence | kind | 방식 |
|-------|-----------|------|------|
| `jquery_ajax` | high | auto | extractor — `$.ajax({url:...})` 객체 파싱 |
| `jquery_shorthand` | high | auto | pattern — `$.get/post/getJSON/load("...")` |
| `htmx_attr` | high | auto | pattern — `hx-get/post/put/patch/delete="..."` |
| `form_action` | medium | page | pattern — `<form ... action="...">` |

### 3.2 모던 SPA

| 디텍터 | confidence | kind | 방식 |
|-------|-----------|------|------|
| `service_client` | high | api | pattern — `got/ky/superagent/request/node-fetch("...")`, `useSWR("...")` |
| `socket_io` | medium | api | pattern — `io("...")`, `io.connect("...")` |
| `react_router` | medium | page | pattern — `<Route path="...">`, route 객체 `path: "..."` |
| `vue_router` | medium | page | extractor — routes 배열의 `path: "..."` |
| `graphql_gql` | medium | api | extractor — `` gql`...` `` operation/필드 추출 |

### 3.3 프레임워크 메타데이터

| 디텍터 | confidence | kind | 방식 |
|-------|-----------|------|------|
| `openapi_paths` | high | api | extractor — `"paths": { "/...": {...} }` JSON |
| `next_data` | medium | auto | extractor — `__NEXT_DATA__`, `/_next/data/...` |
| `state_blob` | low | auto | extractor — `__INITIAL_STATE__`, `__NUXT__`, `__APOLLO_STATE__` 내 URL |

### 3.4 기존 패턴 confidence 매핑

- `fetch`, `axios.*`, `.open()`, WebSocket, `ws://`/`wss://`, `/api|graphql|rest/` → **high**
- `url:`, `baseURL:`, axios 객체 조합 → **high**
- `QUOTED_PATH_RE` (범용 경로 휴리스틱) → **low**
- import 패턴 → 정적 자산이므로 기존 동작 유지 (JS 추적용, 후보 생성 아님)

---

## 4. well-known 리소스 디스커버리

### 4.1 동작

각 대상 호스트(스캔 시작 시점의 target_url 기준)에 대해 `--scan-well-known` 활성 시:

1. **`/robots.txt` 조회** (`fetch_text`)
   - `Disallow:`, `Allow:` 경로 → **page / medium** 후보 (와일드카드 `*`, `$` 포함 항목은 제외)
   - `Sitemap:` URL → sitemap 큐에 추가
2. **`/sitemap.xml` 조회** (+ robots에서 발견된 Sitemap URL)
   - `<loc>` 항목 → **page / high** 후보
   - `<sitemapindex>`의 중첩 sitemap → 큐에 추가하여 따라감

### 4.2 안전 제한

| 제한 | 값 |
|-----|----|
| 최대 sitemap 조회 개수 (중첩 포함) | 10 |
| 최대 추출 URL 개수 (전체) | 500 |
| 응답 크기 제한 | 기존 `read_response_text` 재사용 (oversized 거부) |

- 모든 추출 URL은 `url_matches_scope`와 disallowed-host 검사를 통과해야 후보로 추가된다.
- 디텍터 이름: `robots_txt`, `sitemap_xml`
- 발견된 항목은 일반 후보와 동일하게 프로브된다 (`--skip-probe` 설정 따름).

### 4.3 통합 지점

`_discover_once`에서 정적/동적 분석 후, 후보 버킷 빌드 직전에 well-known 디스커버리를 호출하여 `page_bucket`에 병합한다.

---

## 5. 출력·GUI·설정 통합

### 5.1 출력

- **JSON**: `build_result_row` 반환 dict에 `confidence`, `detectors`(정렬된 리스트) 추가
- **XLSX**: `build_result_sheet_rows`의 페이지/API 시트에 `신뢰도` 컬럼 추가
- **HTML**: 페이지/API 테이블에 신뢰도 컬럼 추가

### 5.2 GUI (`route_api_discovery_ctk.py`)

- 통합 테이블의 api/page 행에 `confidence` 값 채우기 (`_build_rows`)
- 라벨 `col_confidence`("신뢰도"/"Confidence") 재사용
- confidence 컬럼 정렬·필터 지원 (기존 민감정보 탭의 confidence 필터 패턴 참고)

### 5.3 CLI / Config 플래그

| 플래그 | 기본값 | 설명 |
|-------|-------|------|
| `--min-confidence {low,medium,high}` | `low` | 지정 등급 미만 후보를 출력에서 제외 (low = 전체 표시) |
| `--scan-well-known` / `--no-scan-well-known` | **활성** | robots.txt/sitemap.xml 디스커버리 |

`Config`에 `scan_well_known: bool`, `min_confidence: str` 필드 추가. `min_confidence` 필터는 결과 행 빌드 후 적용한다.

---

## 6. 테스트 계획 (TDD)

신규/업데이트 테스트는 `tests/`에 추가한다.

### 6.1 신규 테스트

- **디텍터별 단위 테스트**: 각 신규 디텍터에 대해 입력 스니펫 → 기대 후보 URL + confidence + detector 이름
- **confidence 병합 테스트**: 같은 URL을 low/high 디텍터가 탐지 → 최종 high
- **well-known 파싱 테스트** (`fetch_text` 모킹):
  - robots.txt Disallow/Allow/Sitemap 파싱
  - sitemap.xml `<loc>` 추출
  - 중첩 sitemapindex 추적 (제한 개수 준수)
  - scope 밖 URL 제외
  - oversized 응답 거부
- **출력 형식 테스트**: JSON/XLSX/HTML에 confidence 포함 검증
- **min-confidence 필터 테스트**: medium 지정 시 low 후보 제외

### 6.2 기존 테스트 업데이트

- `Candidate` 구조 변경(신규 필드) 반영
- 결과 행 dict에 `confidence`/`detectors` 키 추가된 것 반영
- `collect_path_candidates` 동작 검증 테스트들 confidence 기대값 추가

### 6.3 회귀

- 전체 스위트 통과 확인: `python -m unittest discover -s tests -v`

---

## 7. 영향 범위 요약

| 파일 | 변경 |
|-----|------|
| `route_api_discovery.py` | Detector 데이터클래스, DETECTOR_REGISTRY, 신규 extractor 함수들, Candidate 확장, 병합 헬퍼, well-known 디스커버리, Config/CLI 플래그, 출력 빌더 |
| `route_api_discovery_ctk.py` | api/page 행 confidence 채우기, 컬럼 표시·정렬·필터 |
| `tests/` | 신규 디텍터·well-known·confidence·출력 테스트, 기존 테스트 업데이트 |

별도 모듈 분리 없이 기존 단일 모듈 패턴을 유지하되, 디텍터 정의는 파일 내 논리적 블록으로 묶어 배치한다.
