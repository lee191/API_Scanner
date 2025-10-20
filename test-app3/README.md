# Test Application 3 - Web Crawling Depth Test

## 📋 개요
API Scanner의 **웹 페이지 크롤링 깊이**를 테스트하기 위한 애플리케이션입니다.
3단계 깊이의 HTML 페이지 구조로, 각 페이지마다 고유한 JavaScript 파일이 로드되며, 각 JS 파일은 서로 다른 API 엔드포인트를 호출합니다.

## 🌳 웹 페이지 구조 (3단계 깊이)

```
Level 0 (시작점)
└─ / (index.html)
   └─ main.js → /api/health, /api/info
   ├─ 링크: /products, /users
   │
   Level 1
   ├─ /products (products.html)
   │  └─ products.js → /api/products, /api/products/{id}, /api/products/search
   │  └─ 링크: /admin, /reports
   │
   └─ /users (users.html)
      └─ users.js → /api/users, /api/users/{id}, /api/users/{id}/profile
      └─ 링크: /admin, /reports
      │
      Level 2
      ├─ /admin (admin.html)
      │  └─ admin.js → /api/admin/stats, /api/admin/users, /api/admin/config, /api/admin/logs
      │  └─ 링크: /dashboard, /analytics, /settings
      │
      └─ /reports (reports.html)
         └─ reports.js → /api/reports/sales, /api/reports/monthly, /api/reports/export
         └─ 링크: /dashboard, /analytics
         │
         Level 3 (최종 깊이)
         ├─ /dashboard (dashboard.html)
         │  └─ dashboard.js → /api/dashboard/widgets, /api/dashboard/summary, /api/dashboard/realtime
         │
         ├─ /analytics (analytics.html)
         │  └─ analytics.js → /api/analytics/events, /api/analytics/metrics, /api/analytics/funnel
         │
         └─ /settings (settings.html)
            └─ settings.js → /api/settings/general, /api/settings/security, /api/settings/notifications
                          → /api/internal/debug (HIDDEN)
```

## 📊 통계

### 페이지 및 JS 파일
| Level | 페이지 수 | JS 파일 | 엔드포인트 수 |
|-------|----------|---------|-------------|
| 0 | 1 | main.js | 2 |
| 1 | 2 | products.js, users.js | 6 (3+3) |
| 2 | 2 | admin.js, reports.js | 7 (4+3) |
| 3 | 3 | dashboard.js, analytics.js, settings.js | 12 (3+3+3+1 hidden) |
| **총계** | **8** | **8** | **27** |

### API 엔드포인트 목록

**Level 0 (main.js):**
- GET /api/health
- GET /api/info

**Level 1 (products.js):**
- GET /api/products
- GET /api/products/{id}
- GET /api/products/search

**Level 1 (users.js):**
- GET /api/users
- GET /api/users/{id}
- GET /api/users/{id}/profile

**Level 2 (admin.js):**
- GET /api/admin/stats
- GET /api/admin/users
- GET /api/admin/config
- GET /api/admin/logs

**Level 2 (reports.js):**
- GET /api/reports/sales
- GET /api/reports/monthly
- GET /api/reports/export

**Level 3 (dashboard.js):**
- GET /api/dashboard/widgets
- GET /api/dashboard/summary
- GET /api/dashboard/realtime

**Level 3 (analytics.js):**
- GET /api/analytics/events
- GET /api/analytics/metrics
- GET /api/analytics/funnel

**Level 3 (settings.js):**
- GET /api/settings/general
- GET /api/settings/security
- GET /api/settings/notifications
- GET /api/internal/debug **(HIDDEN - JavaScript only)**

**Hidden:**
- GET /api/v2/products/advanced **(문서화 안 됨)**

## 🚀 실행 방법

### Windows
```bash
start.bat
```

### Linux/Mac
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## 📡 접속
- **URL**: http://localhost:5003
- **포트**: 5003

## 🧪 API Scanner 테스트

### 크롤링 설정
```
Target URL: http://localhost:5003
Max Depth: 3
Scan JavaScript: ✅ 활성화
```

### 예상 결과
```
총 발견된 페이지: 8개
├─ Level 0: 1개 (/)
├─ Level 1: 2개 (/products, /users)
├─ Level 2: 2개 (/admin, /reports)
└─ Level 3: 3개 (/dashboard, /analytics, /settings)

총 발견된 JS 파일: 8개
├─ main.js
├─ products.js, users.js
├─ admin.js, reports.js
└─ dashboard.js, analytics.js, settings.js

총 발견된 API 엔드포인트: ~27개
├─ Level 0: 2개
├─ Level 1: 6개
├─ Level 2: 7개
├─ Level 3: 12개
└─ Hidden: 2개
```

## 🎯 테스트 시나리오

### 시나리오 1: 깊이 1 크롤링
- 설정: Max Depth = 1
- 예상: / (Level 0)만 크롤링
- JS 파일: main.js
- API 발견: 2개

### 시나리오 2: 깊이 2 크롤링
- 설정: Max Depth = 2
- 예상: /, /products, /users (Level 0-1)
- JS 파일: main.js, products.js, users.js
- API 발견: 8개

### 시나리오 3: 깊이 3 크롤링 (전체)
- 설정: Max Depth = 3
- 예상: Level 0-2 전체 (8개 페이지 중 5개)
- JS 파일: 5개
- API 발견: ~15개

### 시나리오 4: 깊이 4 크롤링 (최대)
- 설정: Max Depth = 4 (또는 제한 없음)
- 예상: 전체 8개 페이지
- JS 파일: 전체 8개
- API 발견: 27개 (숨겨진 것 포함)

## 🔍 검증 포인트

1. ✅ **깊이별 페이지 발견**
   - Depth 1: 1개 페이지
   - Depth 2: 3개 페이지 (누적)
   - Depth 3: 5개 페이지 (누적)
   - Depth 4: 8개 페이지 (전체)

2. ✅ **JavaScript 파일 수집**
   - 각 페이지의 `<script>` 태그에서 JS 파일 URL 추출
   - 각 레벨별로 서로 다른 JS 파일

3. ✅ **JS 파일에서 API 추출**
   - fetch() 호출 분석
   - URL 패턴 추출
   - 레벨별로 고유한 API 엔드포인트

4. ✅ **숨겨진 엔드포인트 발견**
   - /api/internal/debug (settings.js에서만 호출)
   - /api/v2/products/advanced (호출 안 됨 - 스캐너가 발견하지 못할 것)

## 📝 참고사항
- 각 페이지는 다음 레벨로 가는 링크를 포함
- 각 JS 파일은 자동으로 해당 레벨의 API를 호출
- 브라우저 콘솔에서 API 호출 로그 확인 가능
- Level 3이 최종 깊이 (더 이상 새 페이지 링크 없음)
