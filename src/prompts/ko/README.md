# 한국어 AI 프롬프트

이 디렉토리는 한국어 AI 분석 프롬프트를 포함합니다.

## 📁 파일 목록

- **endpoint_analysis.txt**: 엔드포인트 종합 보안 분석 프롬프트
- **classification.txt**: Shadow API vs Public API 분류 프롬프트
- **vulnerability_detection.txt**: 보안 취약점 탐지 프롬프트
- **payload_generation.txt**: 보안 테스트 페이로드 생성 프롬프트
- **url_validation.txt**: URL 보안 검증 프롬프트

## 🔧 사용 방법

### 1. 환경 변수 설정

`.env` 파일에서 언어 설정:

```bash
AI_PROMPT_LANGUAGE=ko
```

### 2. 코드에서 직접 지정

```python
from src.analyzer.ai_analyzer import AIAnalyzer

# 한국어 프롬프트 사용
analyzer = AIAnalyzer(language='ko')

# 영어 프롬프트 사용
analyzer = AIAnalyzer(language='en')
```

## 📝 프롬프트 수정

1. txt 파일을 직접 편집
2. 변수 형식 유지: `{method}`, `{url}`, `{status_code}`, `{response_sample}` 등
3. JSON 출력 형식 유지
4. 파일 저장 후 즉시 적용

## 🌐 언어 추가

새 언어를 추가하려면:

1. `src/prompts/{언어코드}/` 디렉토리 생성
2. 5개의 프롬프트 파일 번역
3. `.env`에서 `AI_PROMPT_LANGUAGE={언어코드}` 설정

예시:
```bash
mkdir src/prompts/ja  # 일본어
mkdir src/prompts/zh  # 중국어
mkdir src/prompts/es  # 스페인어
```

## ⚙️ 작동 방식

1. AIAnalyzer 초기화 시 언어 설정 확인
2. `src/prompts/{language}/` 디렉토리에서 프롬프트 로드
3. 언어별 디렉토리가 없으면 영어로 fallback
4. 영어도 없으면 기본 디렉토리 사용

## 🔄 Fallback 순서

```
한국어 (ko/)
  → 영어 (en/)
    → 기본 디렉토리 (src/prompts/)
      → 하드코딩된 fallback 프롬프트
```

## 📊 번역 품질

한국어 프롬프트는 다음을 고려하여 작성되었습니다:

- ✅ 보안 용어의 정확한 한국어 번역
- ✅ 명확한 지시사항
- ✅ 한국어 맥락에 맞는 표현
- ✅ 원본 영어 프롬프트와 동일한 구조

## 🧪 테스트

한국어 프롬프트 테스트:

```bash
# CLI에서 테스트
python main.py full-scan http://localhost:5000 --js-path test-app/static --ai

# 프롬프트 직접 확인
python -c "from src.analyzer.ai_analyzer import AIAnalyzer; a = AIAnalyzer(language='ko'); print(a.prompts['classification'])"
```

## 📈 개선 사항

프롬프트를 개선하려면:

1. 실제 스캔 결과 분석
2. False Positive/Negative 비율 확인
3. 프롬프트 수정 및 테스트
4. 버전 주석 추가

## 💡 팁

### 더 나은 한국어 프롬프트를 위한 팁:

1. **명확한 역할 정의**: "당신은 [역할]입니다"로 시작
2. **구체적인 지시**: 체크할 항목을 명확히 나열
3. **일관된 용어**: 보안 용어를 일관되게 사용
4. **JSON 형식 유지**: 영어 키 이름은 그대로 유지
5. **예시 제공**: 필요시 예시 추가 (선택사항)

### 피해야 할 것:

- ❌ 애매한 표현
- ❌ 너무 긴 프롬프트
- ❌ 일관성 없는 용어
- ❌ JSON 키 이름 번역 (키는 영어 유지!)
