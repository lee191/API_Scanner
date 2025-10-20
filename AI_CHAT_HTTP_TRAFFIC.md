# AI 챗 v4.0 - 실제 HTTP 트래픽 분석

## 🎯 개요

AI 챗이 이제 실제 HTTP 요청/응답 데이터를 분석할 수 있습니다!

### 이전 버전 (v3.0)
- ❌ URL, 메서드, 상태 코드만 분석
- ❌ 실제 페이로드 내용 분석 불가
- ❌ 헤더 정보 분석 불가
- ❌ 응답 시간 분석 불가

### 현재 버전 (v4.0)
- ✅ 실제 요청 헤더 분석
- ✅ 실제 요청 본문 분석
- ✅ 실제 응답 헤더 분석
- ✅ 실제 응답 본문 분석
- ✅ 응답 시간 분석 (성능 이슈)

## 📊 수집되는 데이터

### 요청 데이터
```json
{
  "request_headers": {
    "User-Agent": "Shadow-API-Scanner/1.0",
    "Content-Type": "application/json",
    "Authorization": "Bearer ..."
  },
  "request_body": "{\"username\": \"admin\", \"password\": \"test\"}",
  "response_time": 250  // milliseconds
}
```

### 응답 데이터
```json
{
  "response_headers": {
    "Content-Type": "application/json",
    "Set-Cookie": "session_id=...",
    "X-Frame-Options": "DENY"
  },
  "response_body": "{\"status\": \"success\", \"user_id\": 12345}",
  "status_code": 200
}
```

## 🧠 AI 분석 가능 항목

### 1. 보안 취약점 분석
- **요청 본문 민감 정보**: 평문 비밀번호, API 키 노출
- **응답 정보 유출**: 사용자 ID, 이메일, 내부 경로 노출
- **헤더 보안 설정**: CORS, CSP, X-Frame-Options 누락

### 2. 인증/인가 분석
- **토큰 방식**: Bearer, Cookie, Custom 헤더
- **토큰 만료**: 응답에서 토큰 갱신 메커니즘 확인
- **권한 체크**: 관리자 API의 인증 여부

### 3. 성능 분석
- **느린 엔드포인트**: response_time > 1000ms
- **타임아웃**: response_time 누락 (요청 실패)
- **최적화 권장**: 너무 큰 응답 본문 (>10KB)

### 4. API 설계 품질
- **응답 형식**: JSON, HTML, XML 일관성
- **에러 메시지**: 스택 트레이스 노출 여부
- **HTTP 메서드**: RESTful 원칙 준수

## 💬 AI 챗 사용 예시

### 질문 예시 1: 민감 정보 확인
```
Q: 요청이나 응답에 민감한 정보가 노출되어 있어?

A: 네, 다음 보안 문제를 발견했습니다:

1. POST /api/login
   - 요청 본문: {"password": "admin123"} (평문 비밀번호)
   - 권장: HTTPS 사용, 비밀번호 해싱

2. GET /api/user/profile
   - 응답 본문: {"email": "user@example.com", "ssn": "123-45-6789"}
   - 권장: PII 필드 마스킹, 최소 정보만 반환
```

### 질문 예시 2: 헤더 보안 점검
```
Q: HTTP 헤더 보안 설정이 적절해?

A: 다음 보안 헤더가 누락되었습니다:

1. X-Frame-Options: DENY/SAMEORIGIN
   → 클릭재킹 공격 방어

2. X-Content-Type-Options: nosniff
   → MIME 타입 스니핑 방지

3. Strict-Transport-Security
   → HTTPS 강제 사용

권장: 모든 응답에 보안 헤더 추가
```

### 질문 예시 3: 성능 이슈
```
Q: 느린 엔드포인트 알려줘

A: 응답 시간이 느린 엔드포인트:

1. GET /api/products?page=1 → 2350ms
   - 원인: 대량 데이터 쿼리
   - 권장: 페이지네이션 최적화, 캐싱

2. POST /api/search → 1850ms
   - 원인: 복잡한 검색 로직
   - 권장: ElasticSearch 도입
```

## 🚀 사용 방법

### 1. 데이터베이스 마이그레이션
```bash
python migrate_add_request_response_fields.py
```

### 2. API 서버 재시작
```bash
# 기존 서버 종료 (Ctrl+C)
python api_server.py
```

### 3. 새로운 스캔 실행
```bash
# 요청/응답 데이터가 자동으로 수집됨
python main.py --target https://example.com --validate
```

### 4. AI 챗 사용
1. 웹 UI에서 스캔 선택
2. "AI 챗" 탭 클릭
3. 질문 입력 또는 퀵 질문 버튼 클릭

## 📋 퀵 질문 버튼

### 1. 📊 전체 스캔 요약
- 발견된 엔드포인트 통계
- 주요 발견사항 요약
- 실제 HTTP 트래픽 통계

### 2. 🔒 보안 분석
- 요청 본문 민감 정보 확인
- 응답 데이터 정보 유출 점검
- 헤더 보안 설정 평가

### 3. ⚠️ 에러 분석
- 4xx/5xx 에러 원인 분석
- 에러 응답 메시지 검토
- 스택 트레이스 노출 확인

### 4. 🎯 민감 엔드포인트
- /admin, /api, /auth 경로 분석
- 인증 메커니즘 확인
- 권한 체크 누락 여부

### 5. 💡 개선 권장사항
- 성능 최적화 (느린 응답)
- 보안 강화 (헤더, 암호화)
- API 설계 개선 (RESTful)

## 🔧 기술 세부사항

### 데이터베이스 스키마 (Endpoint 모델)
```sql
ALTER TABLE endpoint ADD COLUMN request_headers JSON;
ALTER TABLE endpoint ADD COLUMN request_body TEXT;
ALTER TABLE endpoint ADD COLUMN response_headers JSON;
ALTER TABLE endpoint ADD COLUMN response_body TEXT;
ALTER TABLE endpoint ADD COLUMN response_time INTEGER;
```

### 데이터 크기 제한
- response_body: 최대 10KB (초과 시 truncate)
- request_body: 실제 전송 크기 그대로
- headers: JSON 형식으로 저장

### AI 컨텍스트 구조
```typescript
endpoint_samples: {
  by_status: {
    success_2xx: [{
      url, method, status_code,
      request_headers, request_body,
      response_headers, response_body,
      response_time
    }],
    client_error_4xx: [...],
    server_error_5xx: [...]
  },
  sensitive_endpoints: [...]
}
```

## ⚠️ 주의사항

### 1. 데이터 프라이버시
- 실제 요청/응답 데이터가 DB에 저장됨
- 민감 정보(비밀번호, 토큰)가 포함될 수 있음
- 테스트 환경에서만 사용 권장

### 2. 저장 공간
- 응답 본문이 큰 경우 DB 크기 증가
- 정기적으로 오래된 스캔 데이터 삭제 권장
- response_body는 10KB로 제한됨

### 3. 성능 영향
- 데이터 수집으로 스캔 시간 약간 증가
- AI 챗 응답 시 더 많은 컨텍스트 전송
- GPT-3.5-turbo로 최적화되어 있음

## 📈 이전 버전과 비교

| 기능 | v3.0 (이전) | v4.0 (현재) |
|------|-------------|-------------|
| URL 분석 | ✅ | ✅ |
| 메서드 분석 | ✅ | ✅ |
| 상태 코드 | ✅ | ✅ |
| 요청 헤더 | ❌ | ✅ |
| 요청 본문 | ❌ | ✅ |
| 응답 헤더 | ❌ | ✅ |
| 응답 본문 | ❌ | ✅ |
| 응답 시간 | ❌ | ✅ |
| 민감 정보 탐지 | 제한적 | 정확 |
| 보안 헤더 점검 | ❌ | ✅ |
| 성능 분석 | ❌ | ✅ |

## 🎓 학습 가이드

### AI에게 질문하는 법

#### ❌ 나쁜 질문
- "문제 있어?"
- "보안 체크해줘"
- "뭐가 이상해?"

#### ✅ 좋은 질문
- "POST 요청의 본문에 평문 비밀번호가 있어?"
- "응답 헤더에 X-Frame-Options가 설정되어 있어?"
- "1초 이상 걸리는 느린 엔드포인트 알려줘"
- "/admin 경로가 인증 없이 접근 가능해?"

### 효과적인 AI 활용

1. **구체적으로 질문**: "보안 문제" → "CORS 헤더 누락 확인"
2. **범위 지정**: "전체" → "POST 메서드만"
3. **우선순위**: "모든 문제" → "Critical/High만"
4. **실행 가능**: "분석해줘" → "수정 방법 알려줘"

## 🔄 업그레이드 가이드

### 기존 사용자
1. 마이그레이션 스크립트 실행
2. API 서버 재시작
3. 새로운 스캔 실행 (기존 스캔은 데이터 없음)
4. AI 챗에서 새로운 기능 체험

### 신규 사용자
1. 일반적인 설치 과정 진행
2. `--validate` 옵션으로 스캔 실행
3. AI 챗 탭에서 질문 시작

## 📞 문제 해결

### Q: 마이그레이션 실패
A: 기존 DB 백업 후 재시도
```bash
cp data/api_scanner.db data/api_scanner.db.backup
python migrate_add_request_response_fields.py
```

### Q: 응답 본문이 비어있음
A: `--validate` 옵션 확인
```bash
python main.py --target URL --validate
```

### Q: AI 챗이 상세 분석 안 함
A: 새로운 스캔 실행 (기존 스캔은 데이터 없음)

## 🎉 정리

AI 챗 v4.0은 실제 HTTP 트래픽을 분석하여:
- 🔍 더 정확한 보안 취약점 탐지
- 📊 구체적인 성능 이슈 파악
- 💡 실행 가능한 개선 권장사항 제공

이제 AI가 실제 데이터를 "보고" 분석할 수 있습니다! 🚀
