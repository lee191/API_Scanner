# 🎯 AI 정확도 비교 시스템

API Scanner의 AI 분석 기능 효과를 정량적으로 측정하는 비교 분석 시스템입니다.

## 📁 디렉토리 구조

```
comparison/
├── README.md                      # 이 파일
├── compare_ai_accuracy.py         # 메인 비교 스크립트
├── quick_compare.py               # 빠른 비교 스크립트
├── test_comparison_system.py      # 시스템 테스트 스크립트
├── run-comparison.bat             # Windows 실행 배치 파일
└── docs/                          # 문서
    ├── QUICKSTART.md              # 빠른 시작 가이드
    ├── GUIDE.md                   # 상세 사용 가이드
    ├── SUMMARY.md                 # 시스템 개요
    └── COMPLETE.md                # 완전한 문서
```

## 🚀 빠른 시작

### 1️⃣ 테스트 앱 실행

```bash
# 프로젝트 루트에서
cd ..
start-test-app.bat
```

### 2️⃣ 비교 실행

```bash
# comparison 디렉토리에서
run-comparison.bat
```

또는 Python으로 직접:

```bash
# 자동 스캔 + 비교 (5-10분)
python compare_ai_accuracy.py

# 기존 결과만 비교 (10초)
python compare_ai_accuracy.py --skip-scan

# 메트릭만 확인 (5초)
python quick_compare.py --metrics-only
```

### 3️⃣ 시스템 테스트

```bash
python test_comparison_system.py
```

## 📊 주요 기능

### 1. 자동 스캔 및 비교
- ✅ AI 사용 스캔 자동 실행
- ✅ AI 미사용 스캔 자동 실행
- ✅ Ground Truth와 비교하여 정확도 계산
- ✅ 상세한 비교 리포트 생성

### 2. 정확도 메트릭
- **Precision (정밀도)**: 탐지한 것 중 실제로 맞는 비율
- **Recall (재현율)**: 실제 API 중 탐지한 비율
- **F1-Score**: Precision과 Recall의 조화 평균
- **개선도 분석**: AI 사용 전후 비교

### 3. 상세 분석
- True Positives (정확 탐지)
- False Positives (오탐지)
- False Negatives (미탐지)
- AI 고유 탐지 목록
- 성능 등급 평가

## 📈 출력 예시

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

## 📚 문서

| 문서 | 내용 | 용도 |
|------|------|------|
| [QUICKSTART.md](docs/QUICKSTART.md) | 빠른 시작 | 3분 안에 시작 |
| [GUIDE.md](docs/GUIDE.md) | 상세 가이드 | 심화 사용법 |
| [SUMMARY.md](docs/SUMMARY.md) | 시스템 개요 | 전체 이해 |
| [COMPLETE.md](docs/COMPLETE.md) | 완전한 문서 | 모든 정보 |

## 🔧 필수 요구사항

1. **Ground Truth 파일**: `../ground_truth.json`
2. **테스트 앱 실행**: `http://localhost:5000`
3. **Python 패키지**: `../requirements.txt`
4. **OpenAI API 키** (AI 사용 시): `../.env`

## 🎓 사용 예시

### 예시 1: 전체 비교

```bash
# 프로젝트 루트로 이동
cd ..

# 테스트 앱 시작
start-test-app.bat

# comparison 디렉토리로 이동
cd comparison

# 전체 비교 실행
python compare_ai_accuracy.py
```

### 예시 2: Python API 사용

```python
import sys
sys.path.insert(0, '..')  # 프로젝트 루트를 경로에 추가

from comparison.compare_ai_accuracy import AccuracyComparator

# 초기화
comparator = AccuracyComparator("../ground_truth.json")

# 비교 실행
comparison = comparator.compare_results()

# 리포트 출력
comparator.print_comparison_report(comparison)

# 결과 저장
comparator.export_comparison(comparison)
```

### 예시 3: 메트릭만 확인

```bash
python quick_compare.py --metrics-only
```

## 📊 출력 파일

모든 출력은 프로젝트 루트의 `output/accuracy_comparison/` 디렉토리에 저장됩니다:

- **비교 리포트**: `comparison_report_YYYYMMDD_HHMMSS.json`
- **데이터베이스**: `../data/scanner_with_ai.db`, `../data/scanner_without_ai.db`
- **백업 파일**: `*.backup_YYYYMMDD_HHMMSS`

## 🐛 문제 해결

### 문제: ModuleNotFoundError

```bash
# 프로젝트 루트에서 실행하거나
cd ..
python comparison/compare_ai_accuracy.py

# 또는 PYTHONPATH 설정
set PYTHONPATH=%CD%
cd comparison
python compare_ai_accuracy.py
```

### 문제: Ground Truth 파일 없음

```bash
# 프로젝트 루트로 이동
cd ..

# ground_truth.json 복사
copy ground_truth_complete.json ground_truth.json

# comparison으로 돌아가기
cd comparison
```

### 문제: 테스트 앱 미실행

```bash
# 프로젝트 루트에서
cd ..
start-test-app.bat

# 확인
curl http://localhost:5000
```

## 🎯 성능 등급

| F1-Score | 등급 | 평가 |
|----------|------|------|
| ≥ 95% | S | Excellent |
| ≥ 90% | A | Very Good |
| ≥ 80% | B | Good |
| ≥ 70% | C | Fair |
| ≥ 60% | D | Poor |
| < 60% | F | Very Poor |

## 💡 팁

1. **첫 실행**: `test_comparison_system.py`로 시스템 테스트 먼저 실행
2. **빠른 확인**: `quick_compare.py --metrics-only` 사용
3. **정기 평가**: 매주 실행하여 추세 파악
4. **결과 보관**: JSON 파일을 Git으로 버전 관리

## 🤝 기여

개선 제안이나 버그 리포트는 이슈로 등록해주세요.

---

**버전**: 1.0.0  
**최종 업데이트**: 2025-10-15  
**위치**: `comparison/`
