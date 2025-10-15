# AI 사용/미사용 스캔 비교 가이드

## 개요

`compare_ai_accuracy.py` 스크립트는 AI 분석을 사용한 스캔과 사용하지 않은 스캔의 결과를 비교하여 정확도를 분석합니다.

## 주요 기능

### 1. 자동 스캔 및 비교
- AI 사용 스캔 자동 실행
- AI 미사용 스캔 자동 실행  
- Ground Truth와 비교하여 정확도 계산
- 상세한 비교 리포트 생성

### 2. 정확도 메트릭
- **Precision (정밀도)**: 탐지한 것 중 실제로 맞는 비율
- **Recall (재현율)**: 실제 API 중 탐지한 비율
- **F1-Score**: Precision과 Recall의 조화 평균
- **True Positives (TP)**: 정확히 탐지한 엔드포인트
- **False Positives (FP)**: 오탐지 (실제로는 없는데 탐지)
- **False Negatives (FN)**: 미탐지 (실제로는 있는데 못 찾음)

### 3. 비교 분석
- AI만 탐지한 엔드포인트 (AI의 우수성)
- 기본 분석만으로 탐지한 엔드포인트
- AI 분석의 고유 오탐지
- 기본 분석의 고유 오탐지
- 성능 개선/하락 분석

## 사용 방법

### 기본 사용 (자동 스캔 포함)

```bash
# 테스트 앱 실행
start-test-app.bat

# 비교 스크립트 실행 (자동으로 두 번 스캔)
python compare_ai_accuracy.py
```

### 기존 스캔 결과 사용

이미 스캔을 수행한 경우, 기존 데이터베이스를 재사용할 수 있습니다:

```bash
python compare_ai_accuracy.py --skip-scan
```

### 사용자 정의 데이터베이스 경로

```python
from compare_ai_accuracy import AccuracyComparator

comparator = AccuracyComparator(
    ground_truth_path="ground_truth.json",
    db_with_ai="custom/path/scanner_ai.db",
    db_without_ai="custom/path/scanner_no_ai.db"
)

comparison = comparator.compare_results()
comparator.print_comparison_report(comparison)
comparator.export_comparison(comparison)
```

## 출력 예시

### 요약 테이블

```
┌──────────────────────────────────┬──────────────────────┬──────────────────────┬──────────────────────┐
│ 지표                             │ AI 미사용            │ AI 사용              │ 개선                 │
├──────────────────────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ 탐지된 총 엔드포인트             │ 18                   │ 22                   │ +4                   │
│ 정확히 탐지 (TP)                 │ 17                   │ 21                   │ +4                   │
│ 오탐지 (FP)                      │ 1                    │ 1                    │ 0                    │
│ 미탐지 (FN)                      │ 5                    │ 1                    │ +4                   │
├──────────────────────────────────┼──────────────────────┼──────────────────────┼──────────────────────┤
│ Precision (정밀도)               │ 94.44%               │ 95.45%               │ +1.01%p              │
│ Recall (재현율)                  │ 77.27%               │ 95.45%               │ +18.18%p             │
│ F1-Score                         │ 85.00%               │ 95.45%               │ +10.45%p             │
└──────────────────────────────────┴──────────────────────┴──────────────────────┴──────────────────────┘
```

### 상세 분석

```
[+] AI만 탐지한 엔드포인트 (실제 존재) - 4개:
    POST   /api/internal/admin
    GET    /api/internal/debug/config
    POST   /api/internal/deserialize
    POST   /api/internal/exec

[*] 기본 분석만으로 탐지한 엔드포인트 (실제 존재) - 0개:

[!] AI 분석의 고유 오탐지 - 1개:
    GET    /api/v1/nonexistent

[!] 기본 분석의 고유 오탐지 - 1개:
    POST   /api/fake/endpoint
```

### 종합 평가

```
AI 미사용: B (Good) (F1-Score: 85.00%)
AI 사용:   A (Very Good) (F1-Score: 95.45%)

✓ AI 분석으로 10.45%p 개선
```

## 등급 체계

| F1-Score | 등급 | 평가 |
|----------|------|------|
| ≥ 95% | S | Excellent |
| ≥ 90% | A | Very Good |
| ≥ 80% | B | Good |
| ≥ 70% | C | Fair |
| ≥ 60% | D | Poor |
| < 60% | F | Very Poor |

## 출력 파일

스크립트는 다음 파일들을 생성합니다:

1. **비교 리포트 JSON**: `output/accuracy_comparison/comparison_report_YYYYMMDD_HHMMSS.json`
   - 전체 비교 결과를 JSON 형식으로 저장
   - 프로그래밍 방식으로 분석 가능

2. **데이터베이스 백업**: 
   - `data/scanner_with_ai.db.backup_YYYYMMDD_HHMMSS`
   - `data/scanner_without_ai.db.backup_YYYYMMDD_HHMMSS`

## 고급 사용

### Python API로 사용

```python
from compare_ai_accuracy import AccuracyComparator

# 초기화
comparator = AccuracyComparator("ground_truth.json")

# 개별 스캔 실행
comparator.run_scan(
    target="http://localhost:5000",
    js_path="test-app/static",
    use_ai=True
)

# 결과 비교
comparison = comparator.compare_results()

# 메트릭만 확인
metrics_with_ai = comparison['with_ai']
print(f"AI F1-Score: {metrics_with_ai['f1_score']:.2%}")

# 개선도 확인
improvement = comparison['improvement']
print(f"Recall 개선: {improvement['recall']:.2%}p")
```

### 특정 메트릭만 계산

```python
from compare_ai_accuracy import AccuracyComparator

comparator = AccuracyComparator("ground_truth.json")

# AI 사용 결과만 분석
endpoints_with_ai = comparator._load_scan_results("data/scanner_with_ai.db")
metrics = comparator.calculate_metrics(endpoints_with_ai)

print(f"Precision: {metrics['precision']:.2%}")
print(f"Recall: {metrics['recall']:.2%}")
print(f"F1-Score: {metrics['f1_score']:.2%}")
```

## 문제 해결

### 스캔이 실행되지 않음

1. 테스트 앱이 실행 중인지 확인:
   ```bash
   curl http://localhost:5000
   ```

2. 필요한 디렉토리가 있는지 확인:
   ```bash
   mkdir -p data output
   ```

### Ground Truth 파일이 없음

`ground_truth.json` 파일을 먼저 생성해야 합니다:
```bash
# 실제 API 엔드포인트를 정의한 JSON 파일
cp ground_truth_complete.json ground_truth.json
```

### 데이터베이스 오류

기존 데이터베이스를 삭제하고 다시 스캔:
```bash
rm data/scanner_with_ai.db data/scanner_without_ai.db
python compare_ai_accuracy.py
```

## 환경 변수 설정

AI 분석을 제어하려면 `.env` 파일에서 설정:

```bash
# AI 분석 활성화/비활성화
AI_ANALYSIS_ENABLED=true

# OpenAI API 키
OPENAI_API_KEY=your-api-key-here

# 사용할 모델
OPENAI_MODEL=gpt-4-turbo-preview

# 최대 토큰
AI_MAX_TOKENS=8000
```

## 성능 팁

1. **스캔 시간 단축**: 취약점 스캔을 건너뛰려면 `--no-scan-vulns` 사용
2. **비용 절감**: AI 분석은 OpenAI API 비용이 발생하므로 필요시에만 사용
3. **정확도 향상**: Ground Truth를 정확하게 유지보수

## 참고 자료

- [measure_accuracy.py](measure_accuracy.py) - 단일 스캔 정확도 측정
- [ACCURACY_ANALYSIS_v2.md](ACCURACY_ANALYSIS_v2.md) - 정확도 분석 문서
- [ground_truth.json](ground_truth.json) - Ground Truth 데이터
