# 에러 처리 개선 가이드

## 개요
page.tsx의 에러 처리를 개선하기 위한 가이드입니다. 기존 `alert()` 호출을 `toast` 알림으로 대체하고, 더 나은 에러 메시지를 제공합니다.

## 새로운 도구들

### 1. Toast 알림 시스템
`src/lib/toast.ts` - `alert()` 대신 사용할 수 있는 현대적인 알림 시스템

```typescript
import { toast } from '@/lib/toast';

// 사용 예시
toast.success('스캔이 완료되었습니다');
toast.error('스캔 시작 실패');
toast.warning('프로젝트를 선택해주세요');
toast.info('분석 중...');
```

### 2. 유틸리티 함수
`src/lib/utils.ts` - 에러 메시지 파싱 및 기타 헬퍼 함수

```typescript
import { parseErrorMessage } from '@/lib/utils';

// 사용 예시
try {
  // ... 코드
} catch (err) {
  const message = parseErrorMessage(err);
  toast.error(message);
}
```

## 개선 권장 사항

### ❌ 개선 전 (alert 사용)
```typescript
const createProject = async () => {
  if (!newProjectName.trim()) {
    alert('프로젝트 이름을 입력해주세요');
    return;
  }

  try {
    // ... API 호출
    alert('프로젝트가 생성되었습니다');
  } catch (err: any) {
    alert(`프로젝트 생성 실패: ${err.response?.data?.error || err.message}`);
  }
};
```

### ✅ 개선 후 (toast 사용)
```typescript
import { toast } from '@/lib/toast';
import { parseErrorMessage } from '@/lib/utils';

const createProject = async () => {
  if (!newProjectName.trim()) {
    toast.warning('프로젝트 이름을 입력해주세요');
    return;
  }

  try {
    // ... API 호출
    toast.success('프로젝트가 생성되었습니다');
  } catch (err) {
    const message = parseErrorMessage(err);
    toast.error(`프로젝트 생성 실패: ${message}`);
  }
};
```

## 교체해야 할 alert() 호출 목록

### page.tsx에서 발견된 alert() 호출:

1. **Line 198**: `alert('취약점 정보를 불러올 수 없습니다')`
   ```typescript
   // 개선
   toast.error('취약점 정보를 불러올 수 없습니다');
   ```

2. **Line 231**: `alert('스캔 기록이 삭제되었습니다')`
   ```typescript
   // 개선
   toast.success('스캔 기록이 삭제되었습니다');
   ```

3. **Line 240**: `alert(\`스캔 삭제 실패: ${...}\`)`
   ```typescript
   // 개선
   toast.error(`스캔 삭제 실패: ${parseErrorMessage(err)}`);
   ```

4. **Line 249**: `alert('프로젝트 이름을 입력해주세요')`
   ```typescript
   // 개선
   toast.warning('프로젝트 이름을 입력해주세요');
   ```

5. **Line 262**: `alert('프로젝트가 생성되었습니다')`
   ```typescript
   // 개선
   toast.success('프로젝트가 생성되었습니다');
   ```

6. **Line 266**: `alert(\`프로젝트 생성 실패: ${...}\`)`
   ```typescript
   // 개선
   toast.error(`프로젝트 생성 실패: ${parseErrorMessage(err)}`);
   ```

7. **Line 273**: `alert('프로젝트 이름을 입력해주세요')`
   ```typescript
   // 개선
   toast.warning('프로젝트 이름을 입력해주세요');
   ```

8. **Line 287**: `alert('프로젝트가 수정되었습니다')`
   ```typescript
   // 개선
   toast.success('프로젝트가 수정되었습니다');
   ```

9. **Line 289**: `alert(\`프로젝트 수정 실패: ${...}\`)`
   ```typescript
   // 개선
   toast.error(`프로젝트 수정 실패: ${parseErrorMessage(err)}`);
   ```

10. **Line 313**: `alert('프로젝트가 삭제되었습니다')`
    ```typescript
    // 개선
    toast.success('프로젝트가 삭제되었습니다');
    ```

11. **Line 315**: `alert(\`프로젝트 삭제 실패: ${...}\`)`
    ```typescript
    // 개선
    toast.error(`프로젝트 삭제 실패: ${parseErrorMessage(err)}`);
    ```

## console.error() 개선

console.error()는 개발 중에는 유용하지만, 프로덕션에서는 사용자에게 의미가 없습니다. 선택적으로 제거하거나 개발 환경에서만 실행되도록 할 수 있습니다.

### 개선 전
```typescript
try {
  // ... 코드
} catch (err) {
  console.error('Failed to load projects:', err);
}
```

### 개선 후
```typescript
try {
  // ... 코드
} catch (err) {
  if (process.env.NODE_ENV === 'development') {
    console.error('Failed to load projects:', err);
  }
  // 필요시 사용자에게도 알림
  toast.error('프로젝트 목록을 불러올 수 없습니다');
}
```

## 에러 상태 표시 개선

### 현재 에러 표시 (Line 1064-1072)
```typescript
{error && (
  <div className="bg-red-500/20 backdrop-blur-lg border border-red-500 rounded-xl p-6">
    <div className="flex items-start gap-3">
      <span className="text-2xl">⚠️</span>
      <div>
        <div className="text-red-300 font-semibold mb-1">오류 발생</div>
        <div className="text-red-200 text-sm">{error}</div>
      </div>
    </div>
  </div>
)}
```

이 부분은 이미 잘 구현되어 있으므로 유지하면 됩니다. toast는 일시적인 알림용이고, 이 에러 카드는 지속적인 에러 상태 표시용입니다.

## 로딩 상태 개선

### 개선 권장사항

1. **스켈레톤 로딩 사용**
   ```typescript
   {loading ? (
     <div className="skeleton h-32 w-full rounded-lg" />
   ) : (
     <div>{/* 실제 컨텐츠 */}</div>
   )}
   ```

2. **로딩 텍스트 개선**
   ```typescript
   import { getLoadingText } from '@/lib/utils';

   {loading && <p>{getLoadingText(progress)}</p>}
   ```

## 적용 방법

1. **page.tsx 파일 상단에 import 추가**
   ```typescript
   import { toast } from '@/lib/toast';
   import { parseErrorMessage, getLoadingText } from '@/lib/utils';
   ```

2. **alert() 호출을 toast로 하나씩 교체**
   - 성공 메시지: `toast.success()`
   - 에러 메시지: `toast.error()`
   - 경고 메시지: `toast.warning()`
   - 정보 메시지: `toast.info()`

3. **에러 메시지 파싱 추가**
   ```typescript
   catch (err) {
     const message = parseErrorMessage(err);
     toast.error(message);
   }
   ```

4. **개발 환경에서만 console 로그**
   ```typescript
   if (process.env.NODE_ENV === 'development') {
     console.error('...', err);
   }
   ```

## Toast 설정 옵션

### 지속 시간 조절
```typescript
toast.success('완료!', 5000); // 5초 동안 표시
toast.error('에러 발생', 0); // 수동으로 닫을 때까지 표시
```

### 여러 토스트 동시 표시
```typescript
toast.info('스캔 시작...');
// ... 몇 초 후
toast.success('스캔 완료!');
```

### 모든 토스트 닫기
```typescript
toast.clear();
```

## 테스트

Toast가 잘 작동하는지 테스트하려면 브라우저 콘솔에서:

```javascript
// 브라우저 콘솔에서 테스트
import('@/lib/toast').then(({ toast }) => {
  toast.success('테스트 성공 메시지');
  toast.error('테스트 에러 메시지');
  toast.warning('테스트 경고 메시지');
  toast.info('테스트 정보 메시지');
});
```

## 요약

- ✅ `alert()` → `toast` 알림으로 교체
- ✅ `parseErrorMessage()` 유틸리티 사용
- ✅ 개발 환경에서만 console.error() 실행
- ✅ 스켈레톤 로딩 UI 사용
- ✅ 일관된 에러 메시지 형식

이러한 개선을 통해 사용자 경험이 크게 향상됩니다.
