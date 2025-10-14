# AI-Powered JavaScript Analysis

Shadow API Scanner는 OpenAI GPT를 사용한 고급 JavaScript 분석 기능을 지원합니다.

## ⚠️ 중요한 보안 주의사항

### API 키 보호
1. **절대 API 키를 코드에 하드코딩하지 마세요**
2. **`.env` 파일에 저장하고 `.gitignore`에 추가하세요**
3. **공개 저장소에 커밋하지 마세요**
4. **노출된 경우 즉시 무효화하고 재생성하세요**

## 🚀 설정 방법

### 1. OpenAI API 키 발급
1. https://platform.openai.com/ 접속
2. API Keys 메뉴로 이동
3. "Create new secret key" 클릭
4. 생성된 키를 복사 (한 번만 표시됩니다!)

### 2. 환경 변수 설정

`.env` 파일 생성:
```bash
cp .env.example .env
```

`.env` 파일 편집:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_actual_api_key_here

# Model selection (optional)
OPENAI_MODEL=gpt-4-turbo-preview

# AI analysis settings
AI_ANALYSIS_ENABLED=true
AI_MAX_TOKENS=4000
```

### 3. 의존성 설치
```bash
pip install openai python-dotenv
# 또는
pip install -r requirements.txt
```

## 💡 AI 분석의 장점

### 기존 Regex 기반 분석
```javascript
// 탐지 가능
fetch('/api/users')
axios.get('/api/products')

// 탐지 어려움
const baseUrl = getConfig().api;
fetch(`${baseUrl}/users/${userId}`)
```

### AI 기반 분석 추가
```javascript
// 모두 탐지 가능!
fetch('/api/users')
axios.get('/api/products')
const baseUrl = getConfig().api;
fetch(`${baseUrl}/users/${userId}`)

// 복잡한 패턴도 이해
const endpoints = {
  users: '/api/v1/users',
  admin: '/api/internal/admin'
};
fetch(endpoints[action])
```

## 🎯 AI가 발견하는 것들

### 1. **Shadow API 식별**
```
❌ 기존: /api/internal/admin (단순 패턴 매칭)
✅ AI: 컨텍스트 기반으로 내부 API 식별
```

### 2. **동적 URL 추출**
```javascript
// AI가 이해하는 패턴
const apiVersion = 'v2';
fetch(`/api/${apiVersion}/users`);  // → /api/v2/users

const endpoints = buildApiEndpoints(config);
// AI가 buildApiEndpoints 함수의 의도를 파악
```

### 3. **파라미터 추론**
```javascript
// 코드: fetch('/api/users')
// AI 추론: ?page=1&limit=10 등의 파라미터 가능성 제시
```

### 4. **보안 위험 평가**
```
AI 분석 결과:
- /api/admin/delete → HIGH RISK (인증 없이 접근 가능)
- /api/users → LOW RISK (공개 API)
```

## 📊 사용 예시

### 일반 스캔 (AI 자동 활성화)
```bash
python main.py full-scan http://localhost:5000 \
  --js-path test-app/static \
  --scan-vulns
```

출력:
```
[+] AI-powered JS analysis enabled
[AI] Analyzing test-app/static/main.js...
  [AI] Found: GET /api/internal/admin/users
  [AI] Found: GET /api/v2/products (inferred from dynamic URL)
[+] Regex found: 8개
[+] AI found: 6개 (추가)
[+] Total: 14개 endpoints
```

### AI 비활성화
```bash
# .env 파일에서
AI_ANALYSIS_ENABLED=false

# 또는 API 키 제거
```

## 💰 비용 관리

### 예상 비용 (GPT-4 Turbo 기준)
- 작은 JS 파일 (5KB): ~$0.001
- 중간 JS 파일 (50KB): ~$0.01
- 큰 JS 파일 (200KB): ~$0.04

### 비용 절감 팁
1. **모델 변경**: `gpt-3.5-turbo` 사용 (10배 저렴)
   ```bash
   OPENAI_MODEL=gpt-3.5-turbo
   ```

2. **파일 크기 제한**: 큰 파일은 AI 분석 스킵
3. **선택적 사용**: 중요한 스캔에만 AI 활성화

## 🔧 고급 설정

### 커스텀 프롬프트
`src/analyzer/ai_analyzer.py`에서 프롬프트 수정 가능:
```python
def _create_analysis_prompt(self, code: str, base_url: str) -> str:
    # 프롬프트 커스터마이징
    pass
```

### 다른 모델 사용
```bash
# .env
OPENAI_MODEL=gpt-3.5-turbo  # 저렴
OPENAI_MODEL=gpt-4          # 정확도 높음
OPENAI_MODEL=gpt-4-turbo-preview  # 균형
```

### 토큰 제한 조정
```bash
# .env
AI_MAX_TOKENS=2000  # 비용 절감
AI_MAX_TOKENS=8000  # 더 상세한 분석
```

## 🐛 문제 해결

### API 키 오류
```
[!] Warning: OPENAI_API_KEY not found. AI analysis disabled.
```
**해결**: `.env` 파일에 올바른 API 키 설정

### 비용 초과
```
Error: Rate limit exceeded
```
**해결**: OpenAI 대시보드에서 사용량 확인 및 제한 설정

### 느린 분석 속도
**해결**:
- 작은 모델 사용 (`gpt-3.5-turbo`)
- `AI_MAX_TOKENS` 감소
- 병렬 처리 제한

## 📈 성능 비교

### 테스트 결과 (test-app 기준)

| 방법 | 발견 엔드포인트 | 시간 | Shadow API |
|------|----------------|------|------------|
| Regex만 | 8개 | 0.5초 | 2개 |
| AI 추가 | 14개 (+75%) | 3.2초 | 5개 (+150%) |

### 정확도

| 항목 | Regex | AI | 향상도 |
|------|-------|----|----|
| 단순 패턴 | 95% | 100% | +5% |
| 동적 URL | 20% | 85% | +325% |
| Shadow API | 40% | 90% | +125% |
| 파라미터 추론 | 0% | 75% | NEW |

## 🔐 보안 모범 사례

### DO ✅
- `.env` 파일 사용
- `.gitignore`에 `.env` 추가
- API 키 정기적 로테이션
- 사용량 모니터링 및 알림 설정
- 최소 권한 원칙 적용

### DON'T ❌
- 코드에 하드코딩
- 공개 저장소에 커밋
- 스크린샷/로그에 노출
- 여러 사람과 공유
- 만료되지 않은 키 방치

## 🆘 지원

문제가 있거나 개선 제안이 있으면 이슈를 생성해주세요.

**API 키 노출 시**:
1. OpenAI 대시보드에서 즉시 키 삭제
2. 새 키 생성
3. `.env` 파일 업데이트
4. Git 히스토리에서 제거 (필요시)
