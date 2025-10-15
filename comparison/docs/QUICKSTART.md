# 🎯 AI 정확도 비교 시스템 - 빠른 시작

## 무엇을 하나요?

AI를 사용한 스캔과 사용하지 않은 스캔의 정확도를 비교하여 AI의 효과를 정량적으로 측정합니다.

## 🚀 빠른 시작 (3단계)

### 1️⃣ 테스트 앱 실행

```bash
start-test-app.bat
```

### 2️⃣ 비교 실행

```bash
run-comparison.bat
```

또는 직접:

```bash
# 자동 스캔 + 비교
python compare_ai_accuracy.py

# 기존 결과만 비교
python compare_ai_accuracy.py --skip-scan

# 메트릭만 빠르게 확인
python quick_compare.py --metrics-only
```

### 3️⃣ 결과 확인

콘솔에 출력된 비교 리포트를 확인하거나, JSON 파일을 열어보세요:

```
output/accuracy_comparison/comparison_report_YYYYMMDD_HHMMSS.json
```

## 📊 출력 예시

```
┌──────────────────────────────┬──────────────┬──────────────┬──────────────┐
│ 지표                         │ AI 미사용    │ AI 사용      │ 개선         │
├──────────────────────────────┼──────────────┼──────────────┼──────────────┤
│ 탐지된 총 엔드포인트         │ 18           │ 22           │ +4           │
│ 정확히 탐지 (TP)             │ 17           │ 21           │ +4           │
│ Precision (정밀도)           │ 94.44%       │ 95.45%       │ +1.01%p      │
│ Recall (재현율)              │ 77.27%       │ 95.45%       │ +18.18%p     │
│ F1-Score                     │ 85.00%       │ 95.45%       │ +10.45%p     │
└──────────────────────────────┴──────────────┴──────────────┴──────────────┘

종합 평가:
AI 미사용: B (Good)
AI 사용:   A (Very Good)
✓ AI 분석으로 10.45%p 개선
```

## 📁 주요 파일

| 파일 | 설명 | 용도 |
|------|------|------|
| `compare_ai_accuracy.py` | 메인 비교 스크립트 | 자동 스캔 + 비교 |
| `quick_compare.py` | 빠른 비교 | 기존 결과만 비교 |
| `run-comparison.bat` | Windows 배치 파일 | 사용자 친화적 실행 |
| `COMPARISON_GUIDE.md` | 상세 가이드 | 심화 사용법 |
| `COMPARISON_SUMMARY.md` | 요약 문서 | 전체 개요 |

## 🔬 측정 메트릭

- **Precision**: 탐지한 것 중 실제로 맞는 비율 (정밀도)
- **Recall**: 실제 API 중 탐지한 비율 (재현율)
- **F1-Score**: Precision과 Recall의 조화 평균 (종합 점수)

## 💡 사용 시나리오

### 시나리오 1: AI 효과 검증

```bash
# 전체 비교 실행
python compare_ai_accuracy.py
```

**결과**: AI가 몇 개의 숨겨진 API를 더 찾았는지 확인

### 시나리오 2: 빠른 메트릭 확인

```bash
# 메트릭만 출력
python quick_compare.py --metrics-only
```

**결과**: 5초 만에 주요 지표 확인

### 시나리오 3: 정기 평가

```bash
# 매주 또는 매월 실행하여 추세 파악
python compare_ai_accuracy.py
```

**결과**: 시간에 따른 성능 변화 추적

## 🎯 목표 성능

| 등급 | F1-Score | 평가 |
|------|----------|------|
| S | ≥ 95% | 탁월 |
| A | ≥ 90% | 매우 좋음 |
| B | ≥ 80% | 좋음 |
| C | ≥ 70% | 보통 |
| D | ≥ 60% | 미흡 |
| F | < 60% | 매우 미흡 |

## 🔧 필수 요구사항

1. **테스트 앱 실행**: `start-test-app.bat`
2. **Ground Truth**: `ground_truth.json` (자동으로 복사됨)
3. **Python 패키지**: `requirements.txt` 설치 필요

## ❓ FAQ

**Q: 스캔이 너무 오래 걸려요**
A: `--skip-scan` 옵션으로 기존 결과만 비교하세요.

**Q: AI 분석이 비활성화되어 있어요**
A: `.env` 파일에서 `AI_ANALYSIS_ENABLED=true` 확인

**Q: Ground Truth는 어디서 나오나요?**
A: `ground_truth.json`은 실제 API 목록입니다. `test-app/app_improved.py`에서 자동 생성됩니다.

## 📚 더 알아보기

- [COMPARISON_GUIDE.md](COMPARISON_GUIDE.md) - 상세 사용 가이드
- [COMPARISON_SUMMARY.md](COMPARISON_SUMMARY.md) - 전체 시스템 개요
- [measure_accuracy.py](measure_accuracy.py) - 단일 스캔 평가

## 🎉 완료!

이제 AI 분석의 효과를 정량적으로 측정할 수 있습니다!
