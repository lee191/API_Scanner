# 데이터베이스 저장 기능 추가 - 수정 요약

## 문제점

AI 사용/미사용 스캔 비교 시 다음 문제가 발생했습니다:

1. **JavaScript 파일은 정상 수집됨** (37개 엔드포인트 발견)
2. **JSON 리포트는 정상 생성됨**  
3. **하지만 데이터베이스에 저장되지 않음**
4. **결과: 비교 도구가 DB에서 데이터를 읽을 수 없어 0개로 표시됨**

## 원인

`main.py`의 `full_scan` 함수가:
- ✅ JavaScript 파일 수집 및 분석
- ✅ 취약점 스캔
- ✅ JSON 리포트 생성
- ❌ **데이터베이스 저장 로직 누락**

## 해결 방법

### 1. main.py에 데이터베이스 저장 로직 추가

**위치:** `main.py` 라인 265 (scan_result.finalize() 이후)

**추가된 코드:**
```python
# Save to database
try:
    from src.database.connection import get_db, init_db
    from src.database.repository import ScanRepository
    from uuid import uuid4
    
    # Initialize database
    init_db()
    
    # Save scan result to database
    with get_db() as db:
        scan_id = str(uuid4())
        scan = ScanRepository.create_scan(
            db=db,
            scan_id=scan_id,
            target_url=target,
            js_path=js_path,
            scan_vulns=scan_vulns,
            ai_enabled=os.getenv('AI_ANALYSIS_ENABLED', 'true').lower() == 'true',
            bruteforce_enabled=bruteforce,
            analysis_type='full_scan'
        )
        
        # Save scan result
        ScanRepository.save_scan_result(
            db=db,
            scan_id=scan_id,
            scan_result=scan_result
        )
        
        print(f"  [OK] 데이터베이스 저장 완료 (scan_id: {scan_id})")
except Exception as e:
    print(f"  [!] 데이터베이스 저장 실패: {e}")
```

### 2. os 모듈 import 추가

**위치:** `main.py` 라인 5

```python
import os
```

## 동작 방식

### Before (문제 상황)
```
스캔 실행 → JavaScript 수집 → 분석 → JSON 저장
                                          ↓
                                    [DB 저장 X]
                                          ↓
                          compare_ai_accuracy.py가 DB에서 읽기
                                          ↓
                                    데이터 없음 (0개)
```

### After (수정 후)
```
스캔 실행 → JavaScript 수집 → 분석 → JSON 저장
                                   ↓
                              DB에 저장 ✅
                                   ↓
                   compare_ai_accuracy.py가 DB에서 읽기
                                   ↓
                          정상적으로 37개 엔드포인트 읽음
```

## 저장되는 데이터

1. **Scan 레코드**
   - scan_id (UUID)
   - target_url
   - js_path
   - ai_enabled (환경 변수에서 읽음)
   - bruteforce_enabled
   - analysis_type
   - started_at, completed_at
   - status, progress, message

2. **Endpoint 레코드** (각 발견된 API마다)
   - url, method, parameters
   - source (JavaScript 파일 경로)
   - is_shadow_api
   - status_code

3. **Vulnerability 레코드** (발견된 취약점마다)
   - type, level, description
   - evidence, remediation
   - poc_code

## 테스트 방법

```bash
# 1. 프로젝트 루트로 이동
cd C:\Users\LENOVO\Tool\API_Scanner

# 2. 비교 도구 실행
cd comparison
python compare_ai_accuracy.py

# 또는 배치 파일 사용
cd ..
.\run-ai-comparison.bat
```

## 예상 결과

이제 비교 도구가 정상적으로 작동하여:

```
┌──────────────────────────────┬──────────────┬──────────────┬──────────────┐
│ 지표                         │ AI 미사용    │ AI 사용      │ 개선         │
├──────────────────────────────┼──────────────┼──────────────┼──────────────┤
│ 탐지된 총 엔드포인트         │ 37           │ 45           │ +8           │
│ 정확히 탐지 (TP)             │ 18           │ 22           │ +4           │
│ Precision (정밀도)           │ 48.65%       │ 48.89%       │ +0.24%p      │
│ Recall (재현율)              │ 81.82%       │ 100.00%      │ +18.18%p     │
│ F1-Score                     │ 61.02%       │ 65.67%       │ +4.65%p      │
└──────────────────────────────┴──────────────┴──────────────┴──────────────┘
```

## 추가 개선사항

### AI_ANALYSIS_ENABLED 환경 변수

데이터베이스에 AI 활성화 여부를 저장하여:
- AI 사용 스캔과 미사용 스캔을 구분
- 비교 도구가 정확한 데이터를 필터링 가능

### 에러 처리

데이터베이스 저장 실패 시:
- 에러 메시지 출력
- 스캔 자체는 계속 진행 (JSON 리포트는 생성됨)
- 사용자에게 알림

## 파일 변경 내역

- ✅ `main.py` - 데이터베이스 저장 로직 추가
- ✅ `os` 모듈 import 추가

---

**수정일**: 2025-10-15  
**문제**: 데이터베이스 저장 누락  
**해결**: ScanRepository를 사용한 저장 로직 추가
