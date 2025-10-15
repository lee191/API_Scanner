# AI 사용/미사용 스캔 정확도 비교 시스템

## 📋 개요

API Scanner의 AI 분석 기능의 효과를 정량적으로 측정하기 위한 비교 분석 시스템입니다.

## 🎯 목적

1. **AI 분석의 효과 측정**: AI를 사용했을 때와 사용하지 않았을 때의 정확도 차이 분석
2. **정량적 평가**: Precision, Recall, F1-Score 등의 메트릭으로 객관적 평가
3. **개선 영역 파악**: AI가 특히 효과적인 부분과 개선이 필요한 부분 식별

## 📁 파일 구성

### 1. 핵심 스크립트

#### `compare_ai_accuracy.py` (메인 스크립트)
- **기능**: AI 사용/미사용 스캔 자동 실행 및 비교
- **사용법**:
  ```bash
  # 자동 스캔 포함
  python compare_ai_accuracy.py
  
  # 기존 결과만 비교
  python compare_ai_accuracy.py --skip-scan
  ```

#### `quick_compare.py` (간단 비교)
- **기능**: 기존 스캔 결과를 빠르게 비교
- **사용법**:
  ```bash
  # 전체 비교 리포트
  python quick_compare.py
  
  # 메트릭만 출력
  python quick_compare.py --metrics-only
  ```

#### `measure_accuracy.py` (단일 스캔 평가)
- **기능**: 단일 스캔 결과의 정확도 측정
- **사용법**:
  ```bash
  python measure_accuracy.py
  ```

### 2. 문서

- `COMPARISON_GUIDE.md`: 상세 사용 가이드
- `COMPARISON_SUMMARY.md`: 이 문서 (요약)

### 3. 데이터

- `ground_truth.json`: 실제 API 엔드포인트 목록 (정답 데이터)
- `data/scanner_with_ai.db`: AI 사용 스캔 결과
- `data/scanner_without_ai.db`: AI 미사용 스캔 결과

## 🔬 분석 메트릭

### 기본 메트릭

1. **True Positives (TP)**: 정확히 탐지한 엔드포인트 수
2. **False Positives (FP)**: 오탐지 (실제로 없는데 탐지)
3. **False Negatives (FN)**: 미탐지 (실제로 있는데 못 찾음)

### 정확도 지표

1. **Precision (정밀도)**
   - 공식: `TP / (TP + FP)`
   - 의미: 탐지한 것 중 실제로 맞는 비율
   - 높을수록 오탐지가 적음

2. **Recall (재현율)**
   - 공식: `TP / (TP + FN)`
   - 의미: 실제 API 중 탐지한 비율
   - 높을수록 미탐지가 적음

3. **F1-Score**
   - 공식: `2 × (Precision × Recall) / (Precision + Recall)`
   - 의미: Precision과 Recall의 조화 평균
   - 종합 성능 지표

## 📊 출력 형식

### 요약 테이블

```
┌──────────────────────────────┬──────────────┬──────────────┬──────────────┐
│ 지표                         │ AI 미사용    │ AI 사용      │ 개선         │
├──────────────────────────────┼──────────────┼──────────────┼──────────────┤
│ 탐지된 총 엔드포인트         │ 18           │ 22           │ +4           │
│ 정확히 탐지 (TP)             │ 17           │ 21           │ +4           │
│ 오탐지 (FP)                  │ 1            │ 1            │ 0            │
│ 미탐지 (FN)                  │ 5            │ 1            │ +4           │
├──────────────────────────────┼──────────────┼──────────────┼──────────────┤
│ Precision (정밀도)           │ 94.44%       │ 95.45%       │ +1.01%p      │
│ Recall (재현율)              │ 77.27%       │ 95.45%       │ +18.18%p     │
│ F1-Score                     │ 85.00%       │ 95.45%       │ +10.45%p     │
└──────────────────────────────┴──────────────┴──────────────┴──────────────┘
```

### 상세 분석

- **AI만 탐지한 엔드포인트**: AI의 우수성을 보여주는 부분
- **기본 분석만으로 탐지**: AI 없이도 가능한 부분
- **고유 오탐지**: 각 방식의 약점

### 종합 평가

```
AI 미사용: B (Good) (F1-Score: 85.00%)
AI 사용:   A (Very Good) (F1-Score: 95.45%)

✓ AI 분석으로 10.45%p 개선
```

## 🚀 사용 워크플로우

### 1단계: 테스트 앱 실행

```bash
# Windows
start-test-app.bat

# Linux/Mac
./start-test-app.sh
```

### 2단계: 비교 스크립트 실행

#### 옵션 A: 자동 스캔 (권장)

```bash
python compare_ai_accuracy.py
```

이 방법은:
1. AI 미사용 스캔 자동 실행
2. AI 사용 스캔 자동 실행
3. 결과 비교 및 리포트 생성

#### 옵션 B: 기존 결과 사용

```bash
python compare_ai_accuracy.py --skip-scan
```

이미 스캔을 수행한 경우 재사용

#### 옵션 C: 빠른 비교

```bash
python quick_compare.py
```

기존 데이터베이스를 즉시 비교

### 3단계: 결과 확인

- **콘솔**: 상세한 비교 리포트
- **JSON 파일**: `output/accuracy_comparison/comparison_report_*.json`

## 💡 사용 예시

### 예시 1: 전체 분석

```bash
# 테스트 앱 시작
start-test-app.bat

# 전체 비교 (스캔 + 분석)
python compare_ai_accuracy.py

# 결과 확인
cat output/accuracy_comparison/comparison_report_*.json
```

### 예시 2: 메트릭만 확인

```bash
python quick_compare.py --metrics-only
```

출력:
```
AI 미사용:
  Precision: 94.44%
  Recall:    77.27%
  F1-Score:  85.00%

AI 사용:
  Precision: 95.45%
  Recall:    95.45%
  F1-Score:  95.45%

✓ AI 분석으로 10.45%p 개선
```

### 예시 3: Python API로 사용

```python
from compare_ai_accuracy import AccuracyComparator

# 초기화
comparator = AccuracyComparator("ground_truth.json")

# 비교 실행
comparison = comparator.compare_results()

# 특정 메트릭 추출
ai_f1 = comparison['with_ai']['f1_score']
no_ai_f1 = comparison['without_ai']['f1_score']
improvement = comparison['improvement']['f1_score']

print(f"F1-Score 개선: {improvement:.2%}p")
```

## 📈 결과 해석

### 좋은 결과

- **F1-Score ≥ 90%**: 매우 우수
- **Recall 개선 > 10%p**: AI가 숨겨진 API 탐지에 효과적
- **Precision 유지**: 오탐지를 증가시키지 않음

### 개선 필요

- **F1-Score < 80%**: 전반적 성능 개선 필요
- **높은 FP**: 오탐지 줄이기 (필터링 강화)
- **높은 FN**: 미탐지 줄이기 (탐지 기법 추가)

## 🔧 고급 설정

### 환경 변수 (.env)

```bash
# AI 분석 제어
AI_ANALYSIS_ENABLED=true

# OpenAI 설정
OPENAI_API_KEY=your-key
OPENAI_MODEL=gpt-4-turbo-preview
AI_MAX_TOKENS=8000

# 데이터베이스 경로 (선택사항)
SCANNER_DB_PATH=data/scanner.db
```

### 사용자 정의 데이터베이스

```python
from compare_ai_accuracy import AccuracyComparator

comparator = AccuracyComparator(
    ground_truth_path="ground_truth.json",
    db_with_ai="custom/scanner_ai.db",
    db_without_ai="custom/scanner_no_ai.db"
)
```

## 🐛 문제 해결

### 문제: 데이터베이스 없음

```bash
# 해결: 스캔 실행
python main.py full-scan http://localhost:5000 --js-path test-app/static
```

### 문제: Ground Truth 없음

```bash
# 해결: 복사
cp ground_truth_complete.json ground_truth.json
```

### 문제: 테스트 앱 미실행

```bash
# 해결: 앱 실행 확인
curl http://localhost:5000

# 재시작
stop-test-app.bat
start-test-app.bat
```

### 문제: AI 분석 실패

```bash
# .env 파일 확인
AI_ANALYSIS_ENABLED=true
OPENAI_API_KEY=sk-...

# 키 유효성 확인
python -c "from openai import OpenAI; OpenAI(api_key='your-key').models.list()"
```

## 📊 성능 등급

| F1-Score | 등급 | 설명 | 조치 |
|----------|------|------|------|
| ≥ 95% | S | 탁월 | 현재 상태 유지 |
| ≥ 90% | A | 매우 좋음 | 미세 조정 |
| ≥ 80% | B | 좋음 | 일부 개선 |
| ≥ 70% | C | 보통 | 개선 필요 |
| ≥ 60% | D | 미흡 | 대폭 개선 필요 |
| < 60% | F | 매우 미흡 | 전면 재검토 |

## 🎓 모범 사례

### 1. Ground Truth 관리
- 정기적 업데이트
- 실제 애플리케이션과 동기화
- 버전 관리 (Git)

### 2. 정기적 평가
- 새 기능 추가 시 평가
- AI 모델 변경 시 재평가
- 월별 벤치마크

### 3. 결과 문서화
- JSON 리포트 보관
- 추세 분석
- 개선 이력 추적

## 📚 참고 자료

- [COMPARISON_GUIDE.md](COMPARISON_GUIDE.md) - 상세 가이드
- [measure_accuracy.py](measure_accuracy.py) - 단일 스캔 평가
- [ACCURACY_ANALYSIS_v2.md](ACCURACY_ANALYSIS_v2.md) - 정확도 분석 문서

## 🤝 기여

개선 제안이나 버그 리포트는 이슈로 등록해주세요.

---

**작성일**: 2025-10-15  
**버전**: 1.0.0  
**작성자**: API Scanner Team
