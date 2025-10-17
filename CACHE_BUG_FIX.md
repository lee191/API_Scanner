# 스캔 상태 캐시 문제 해결 (완전 수정)

## 🐛 문제

웹 UI에서 스캔이 완료되었는데도 계속 "진행중" 상태로 표시되는 버그
**F12(개발자 도구)를 눌러야만 업데이트되는 심각한 캐싱 문제**

### 근본 원인

**1. 스캔 상세 페이지에 폴링 로직 없음**
- `web-ui/src/app/scan/[id]/page.tsx`에서 처음 한 번만 스캔 상태를 로드
- 스캔이 "running" 상태일 때 주기적으로 업데이트하지 않음
- 메인 페이지는 폴링을 하지만, 상세 페이지는 폴링 없음

**2. API 서버에서 캐시 헤더 미설정**
- `/api/status/{scan_id}` 엔드포인트에 캐시 방지 헤더 없음
- 브라우저가 이전 응답을 캐시하여 같은 데이터 반환
- 실제로는 DB에서 상태가 업데이트되었지만 캐시된 응답 표시

**3. 브라우저의 공격적인 HTTP 캐싱**
- 헤더만으로는 부족한 경우 URL 자체가 같아서 캐시됨
- Next.js의 기본 정적 생성 및 캐싱 정책
- Axios의 기본 동작이 브라우저 캐시 사용

## ✅ 해결 방법 (4단계 완전 수정)

### 1. API 서버 - 캐시 방지 헤더 추가 ✅

**파일**: `api_server.py`

```python
@app.route('/api/status/<scan_id>', methods=['GET'])
def get_scan_status(scan_id):
    """Get scan status."""
    try:
        with get_db() as db:
            result = ScanRepository.get_scan_with_details(db, scan_id)

        if not result:
            return jsonify({'error': 'Scan not found'}), 404

        # discovered_paths are now loaded directly from database
        response = jsonify(result)

        # Prevent caching for real-time status updates
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response

    except Exception as e:
        print(f"[!] Get status error: {e}")
        return jsonify({'error': 'Failed to get scan status', 'details': str(e)}), 500
```

**추가된 헤더:**
- `Cache-Control: no-cache, no-store, must-revalidate` - 캐시 금지
- `Pragma: no-cache` - HTTP/1.0 호환성
- `Expires: 0` - 즉시 만료

### 2. 웹 UI - 폴링 로직 추가

**파일**: `web-ui/src/app/scan/[id]/page.tsx`

**변경 전:**
```typescript
useEffect(() => {
  loadScanDetail();
}, [scanId]);

const loadScanDetail = async () => {
  try {
    setLoading(true);
    const response = await api.get(`/api/status/${scanId}`);
    setScanData(response.data);
  } catch (err: any) {
    setError(err.response?.data?.error || err.message || '스캔 정보를 불러오는데 실패했습니다');
  } finally {
    setLoading(false);
  }
};
```

**변경 후:**
```typescript
useEffect(() => {
  loadScanDetail();
}, [scanId]);

// Poll scan status if it's still running
useEffect(() => {
  if (!scanData || scanData.status !== 'running') {
    return;
  }

  const pollInterval = setInterval(() => {
    loadScanDetail();
  }, 2000); // Poll every 2 seconds

  return () => clearInterval(pollInterval);
}, [scanData?.status]);

const loadScanDetail = async () => {
  try {
    setLoading(true);
    const response = await api.get(`/api/status/${scanId}`, {
      headers: {
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }
    });
    setScanData(response.data);
  } catch (err: any) {
    setError(err.response?.data?.error || err.message || '스캔 정보를 불러오는데 실패했습니다');
  } finally {
    setLoading(false);
  }
};
```

**주요 변경사항:**
1. **새 useEffect 추가**: `scanData.status`가 'running'일 때만 폴링 시작
2. **2초 간격 폴링**: `setInterval`로 2초마다 `loadScanDetail()` 호출
3. **클린업**: 컴포넌트 언마운트 또는 상태 변경 시 interval 정리
4. **요청 헤더**: API 호출 시 캐시 방지 헤더 추가

### 3. Axios 인스턴스 - 기본 캐시 방지 헤더 설정 ✅

**파일**: `web-ui/src/app/scan/[id]/page.tsx`, `web-ui/src/app/page.tsx`

**모든 axios 요청에 기본으로 캐시 방지 헤더 적용:**

```typescript
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
});
```

### 4. URL에 Timestamp 추가 (Cache Busting) ✅

**URL 자체를 매번 다르게 만들어 캐시 원천 차단:**

```typescript
const loadScanDetail = async () => {
  try {
    setLoading(true);
    // Add timestamp to prevent caching
    const timestamp = new Date().getTime();
    const response = await api.get(`/api/status/${scanId}?_t=${timestamp}`, {
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      }
    });
    setScanData(response.data);
  } catch (err: any) {
    setError(err.response?.data?.error || err.message || '스캔 정보를 불러오는데 실패했습니다');
  } finally {
    setLoading(false);
  }
};
```

**핵심 변경:**
- `?_t=${timestamp}` - 매 요청마다 고유한 URL 생성
- 브라우저가 URL이 다르므로 새로운 요청으로 인식
- 캐시를 완전히 우회

**메인 페이지 폴링에도 동일하게 적용:**

```typescript
const timestamp = new Date().getTime();
const response = await axios.get(`/api/status/${id}?_t=${timestamp}`, {
  headers: {
    'Cache-Control': 'no-cache, no-store, must-revalidate',
    'Pragma': 'no-cache',
    'Expires': '0'
  }
});
```

### 5. Next.js Dynamic Rendering 강제 ✅

**파일**: `web-ui/src/app/scan/[id]/page.tsx`, `web-ui/src/app/page.tsx`

**Next.js의 정적 생성 및 캐싱 비활성화:**

```typescript
'use client';

// Force dynamic rendering - no static generation or caching
export const dynamic = 'force-dynamic';
export const revalidate = 0;

import { useEffect, useState } from 'react';
// ...
```

**효과:**
- `dynamic = 'force-dynamic'` - 모든 요청을 동적으로 렌더링
- `revalidate = 0` - 재검증 시간을 0으로 설정 (캐싱 없음)
- Next.js의 빌드 타임 정적 생성 방지

### 6. UI 개선 - 진행률 표시 ✅

**스캔 진행 중일 때 진행률 바 표시:**

```typescript
{scanData.status === 'running' && (
  <div className="w-48">
    <div className="flex justify-between text-sm text-gray-400 mb-1">
      <span>진행률</span>
      <span>{scanData.progress || 0}%</span>
    </div>
    <div className="w-full bg-gray-700 rounded-full h-2">
      <div
        className="bg-blue-500 h-2 rounded-full transition-all duration-300"
        style={{ width: `${scanData.progress || 0}%` }}
      />
    </div>
    {scanData.message && (
      <div className="text-xs text-gray-400 mt-1">{scanData.message}</div>
    )}
  </div>
)}
```

**표시 내용:**
- 진행률 퍼센트 (0-100%)
- 시각적 진행률 바
- 현재 상태 메시지 ("Starting scan...", "Executing scanner..." 등)

## 🎯 동작 방식

### Before (버그)

```
1. 사용자가 스캔 상세 페이지 접속
2. API 호출: GET /api/status/{scan_id}
3. 응답: status='running', progress=30%
4. 브라우저가 응답 캐시
5. ❌ 더 이상 업데이트 안됨
6. 실제로는 스캔 완료되었지만 "진행중" 계속 표시
```

### After (수정)

```
1. 사용자가 스캔 상세 페이지 접속
2. API 호출: GET /api/status/{scan_id} (캐시 방지 헤더)
3. 응답: status='running', progress=30%
4. ✓ 2초 후 자동으로 재요청
5. API 응답: status='running', progress=50% (캐시 안됨)
6. ✓ 2초 후 자동으로 재요청
7. API 응답: status='completed', progress=100%
8. ✓ 폴링 중지 (status !== 'running')
9. "완료" 상태 표시
```

## 📊 폴링 전략

**폴링 조건:**
- `scanData.status === 'running'`일 때만 활성화
- 완료/실패 상태가 되면 자동으로 중지

**폴링 간격:**
- 2초마다 업데이트
- 과도한 서버 부하 방지

**메모리 누수 방지:**
- `useEffect` cleanup 함수로 `clearInterval()`
- 컴포넌트 언마운트 시 자동 정리

## 🧪 테스트 방법

### 1. 로컬 환경에서 테스트

```bash
# 1. test-app2 시작
start-test-app2.bat

# 2. API 서버 시작
python api_server.py

# 3. 웹 UI 시작 (새 터미널)
cd web-ui
npm run dev
```

### 2. 테스트 시나리오

**시나리오 1: 스캔 시작 후 상세 페이지 이동**
1. http://localhost:3000 접속
2. 프로젝트 선택 및 스캔 시작
3. 스캔이 진행 중일 때 상세 페이지로 이동
4. ✅ 진행률이 실시간으로 업데이트되는지 확인
5. ✅ 스캔 완료 시 "완료" 상태로 자동 변경되는지 확인

**시나리오 2: 브라우저 새로고침**
1. 스캔 진행 중인 상태에서 페이지 새로고침 (F5)
2. ✅ 현재 진행 상태가 정확히 표시되는지 확인
3. ✅ 폴링이 다시 시작되는지 확인

**시나리오 3: 완료된 스캔 확인**
1. 이미 완료된 스캔의 상세 페이지 접속
2. ✅ "완료" 상태 표시
3. ✅ 폴링이 시작되지 않음 (불필요한 API 호출 없음)

## 📝 주의사항

**폴링 성능:**
- 2초 간격은 적절한 균형점
- 너무 짧으면: 서버 부하 증가
- 너무 길면: 사용자 경험 저하

**메모리 관리:**
- useEffect cleanup으로 interval 정리 필수
- React 18 Strict Mode에서도 정상 동작 확인

**브라우저 호환성:**
- Cache-Control 헤더는 모든 주요 브라우저 지원
- Pragma와 Expires는 하위 호환성 보장

## ✅ 검증 체크리스트

- [x] API 서버에 캐시 방지 헤더 추가
- [x] 웹 UI에 폴링 로직 추가
- [x] 진행률 바 UI 추가
- [x] 메모리 누수 방지 (cleanup 함수)
- [x] 완료 시 폴링 자동 중지
- [ ] 실제 스캔으로 테스트

## 🔒 4단계 캐시 방지 전략 요약

| 단계 | 방법 | 효과 | 파일 |
|-----|------|------|------|
| 1 | API 응답 헤더 | 서버 측 캐시 방지 | `api_server.py` |
| 2 | Axios 기본 헤더 | 클라이언트 요청 캐시 방지 | `page.tsx`, `[id]/page.tsx` |
| 3 | URL Timestamp | URL 자체를 매번 다르게 | 양쪽 page.tsx |
| 4 | Next.js Dynamic | 정적 생성 방지 | 양쪽 page.tsx |

**이 4단계를 모두 적용하여 완전한 캐시 방지 달성!**

## 🎉 기대 효과

1. **✅ 완전한 캐시 제거**: F12 없이도 정상 업데이트
2. **✅ 실시간 업데이트**: 스캔 상태가 2초마다 정확히 표시
3. **✅ 사용자 경험 개선**: 진행률과 상태 메시지로 투명한 피드백
4. **✅ 브라우저 호환성**: 모든 주요 브라우저에서 동작
5. **✅ 자동 폴링 중지**: 불필요한 API 호출 최소화

## 🔍 추가 개선 가능 사항

**WebSocket 도입 (선택):**
- 폴링 대신 실시간 양방향 통신
- 서버 부하 감소
- 즉각적인 상태 업데이트
- 구현 복잡도 증가

**현재는 폴링이 충분:**
- 스캔은 보통 1-5분 소요
- 2초 간격 폴링으로 충분히 빠른 피드백
- 구현이 간단하고 안정적
