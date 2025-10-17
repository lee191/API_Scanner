# AI Prompts for Shadow API Scanner

이 디렉토리는 AI 분석에 사용되는 프롬프트 템플릿을 관리합니다.

## 📁 프롬프트 파일 목록

### 1. `endpoint_analysis.txt`
**용도**: 엔드포인트 종합 보안 분석
**출력**: 위험도 점수, 분류, 취약점, 권장사항
**변수**: `{method}`, `{url}`, `{source}`, `{status_code}`, `{response_sample}`

### 2. `classification.txt`
**용도**: Shadow API vs Public API 분류
**출력**: 분류 결과, 신뢰도, 근거
**변수**: `{method}`, `{url}`, `{source}`, `{status_code}`, `{response_sample}`

### 3. `vulnerability_detection.txt`
**용도**: 보안 취약점 탐지
**출력**: 취약점 목록 (종류, 심각도, 설명, 증거, 수정 방법)
**변수**: `{method}`, `{url}`, `{status_code}`, `{response_sample}`

### 4. `payload_generation.txt`
**용도**: 보안 테스트 페이로드 생성
**출력**: 테스트 페이로드 목록
**변수**: `{method}`, `{url}`

### 5. `url_validation.txt`
**용도**: URL 보안 검증
**출력**: 유효성, 이유, 위험도
**변수**: `{url}`

## 🔧 프롬프트 수정 방법

1. **파일 직접 수정**: txt 파일을 열어서 프롬프트 내용 변경
2. **변수 유지**: `{변수명}` 형식의 변수는 반드시 유지
3. **JSON 형식 유지**: 요청하는 JSON 구조는 변경하지 않음
4. **재시작 불필요**: 파일 수정 후 즉시 적용됨

## 📝 프롬프트 작성 팁

### 좋은 프롬프트 특징:
- ✅ 명확한 역할 정의 ("You are a...")
- ✅ 구체적인 지시사항
- ✅ 체크할 항목 리스트
- ✅ 명확한 출력 형식 (JSON)
- ✅ 예시 포함 (선택사항)

### 피해야 할 것:
- ❌ 모호한 표현
- ❌ 너무 긴 프롬프트 (토큰 낭비)
- ❌ 불필요한 설명
- ❌ 변수명 변경

## 🌍 다국어 지원

프롬프트를 한국어로 번역하려면:

```
src/prompts/
  ko/
    endpoint_analysis.txt
    classification.txt
    ...
  en/
    endpoint_analysis.txt
    classification.txt
    ...
```

그리고 `ai_analyzer.py`에서 언어 설정 추가.

## 🔄 버전 관리

프롬프트 변경 시 주석으로 변경 이력 기록:

```
# Version 1.1 (2025-01-16): Added SSRF detection
# Version 1.0 (2025-01-15): Initial version

[프롬프트 내용]
```

## ⚠️ 주의사항

1. **JSON 형식 변경 시**: `ai_analyzer.py`의 파싱 로직도 함께 수정 필요
2. **변수 추가 시**: `ai_analyzer.py`의 `.format()` 호출도 업데이트 필요
3. **테스트**: 프롬프트 수정 후 반드시 실제 스캔으로 테스트

## 📊 프롬프트 성능 측정

프롬프트 효과를 측정하려면:
1. 테스트 엔드포인트 세트 준비
2. 프롬프트 버전별로 스캔 실행
3. False Positive/Negative 비율 비교
4. 검증 정확도 측정

## 🚀 최적화 팁

### 토큰 절약:
- 불필요한 설명 제거
- 간결한 표현 사용
- 예시는 필요한 경우에만

### 정확도 향상:
- 구체적인 체크리스트 제공
- 명확한 판단 기준 명시
- Few-shot learning 예시 추가 (선택)

### 속도 개선:
- 프롬프트 길이 최소화
- 불필요한 요청 항목 제거
- 배치 처리 활용
