# Web UI 문제 해결 가이드

## "Failed to check scan status" 오류

이 오류는 여러 원인으로 발생할 수 있습니다. 다음 단계를 따라 문제를 진단하세요.

### 1. 브라우저 개발자 도구 확인

1. 브라우저에서 F12 키를 눌러 개발자 도구를 엽니다
2. Console 탭을 확인합니다
3. 다음 로그를 찾아보세요:
   - `Starting scan with:` - 스캔 시작 파라미터
   - `Scan started:` - 스캔 ID 및 초기 상태
   - `Scan {id} status:` - 폴링 중 상태 업데이트
   - `Poll error:` - 폴링 오류 상세 정보

### 2. Python Scanner 확인

Web UI는 백그라운드에서 Python CLI를 실행합니다.

```bash
# Python 설치 확인
python --version

# 프로젝트 루트에서 수동 테스트
cd ..
python main.py full-scan http://localhost:5000 --js-path test-app/static --scan-vulns
```

### 3. 일반적인 문제 및 해결법

#### Python을 찾을 수 없음
**증상**: `'python' is not recognized as an internal or external command`

**해결법**:
```bash
# Python 경로 확인
where python

# PATH에 Python 추가하거나
# web-ui/src/app/api/scan/route.ts에서 python 대신 전체 경로 사용
# 예: C:\Python311\python.exe
```

#### 상대 경로 문제
**증상**: `No such file or directory: main.py`

**해결법**: web-ui가 Shadow API Scanner 프로젝트 내부에 있는지 확인
```
Shadow-API/
├── main.py          ← 여기
├── src/
└── web-ui/          ← 여기 내부
    └── src/
```

#### 포트 충돌
**증상**: `EADDRINUSE: address already in use :::3000`

**해결법**:
```bash
# 다른 포트 사용
PORT=3001 npm run dev

# 또는 실행 중인 프로세스 종료 (Windows)
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

#### 타임아웃
**증상**: "Scan timeout: 스캔이 너무 오래 걸립니다"

**원인**: 스캔이 5분 이상 걸림

**해결법**:
1. `web-ui/src/app/page.tsx`에서 `maxAttempts` 값 증가
2. `web-ui/src/app/api/scan/route.ts`에서 `timeout` 값 증가

```typescript
// page.tsx
const maxAttempts = 300; // 10분

// route.ts
timeout: 600000, // 10분
```

### 4. 서버 로그 확인

#### Next.js 개발 서버 로그
```bash
cd web-ui
npm run dev
# 콘솔 출력 확인
```

로그에서 다음을 찾아보세요:
- `Executing command:` - 실행된 Python 명령어
- `Command stdout:` - Python 스크립트 출력
- `Command stderr:` - Python 오류 메시지
- `Reading output directory:` - 리포트 파일 읽기
- `Scan result parsed successfully` - 결과 파싱 성공

#### Python Scanner 로그
Python 스캐너의 출력을 직접 확인:
```bash
cd ..
python main.py full-scan http://localhost:5000 \
  --js-path test-app/static \
  --scan-vulns \
  --output output/debug
```

### 5. 진단 체크리스트

- [ ] Python 3.8+ 설치 확인
- [ ] `pip install -r requirements.txt` 실행
- [ ] 테스트 앱 실행 중 (http://localhost:5000)
- [ ] web-ui가 프로젝트 내부에 위치
- [ ] Next.js 개발 서버 실행 중 (http://localhost:3000)
- [ ] 브라우저 콘솔에 에러 없음
- [ ] 서버 로그에 Python 실행 오류 없음

### 6. 수동 테스트 절차

완전한 수동 테스트:

```bash
# 1. 테스트 앱 시작
cd test-app
python app.py
# 또는 Docker
cd ..
./docker-run.sh  # Linux/Mac
docker-run.bat   # Windows

# 2. Python Scanner 테스트
python main.py full-scan http://localhost:5000 \
  --js-path test-app/static \
  --scan-vulns \
  --output output/test

# 3. 결과 확인
ls -la output/test/
cat output/test/*.json

# 4. Web UI 시작
cd web-ui
npm run dev

# 5. 브라우저에서 테스트
# http://localhost:3000
# Target URL: http://localhost:5000
# JS Path: (비워둠 또는 ../test-app/static)
# Full Scan 선택
# 스캔 시작 클릭
```

### 7. 고급 디버깅

#### API 라우트 직접 호출
```bash
# 스캔 시작
curl -X POST http://localhost:3000/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target_url": "http://localhost:5000",
    "js_path": "../test-app/static",
    "scan_vulns": true,
    "analysis_type": "full_scan"
  }'

# 응답에서 scan_id 확인
# 예: {"scan_id":"abc-123-def","status":"pending"}

# 상태 확인
curl http://localhost:3000/api/status/abc-123-def
```

#### scanStore 확인
`web-ui/src/lib/scanStore.ts` 파일이 존재하는지 확인:
```bash
ls -la web-ui/src/lib/scanStore.ts
```

없으면 생성:
```bash
mkdir -p web-ui/src/lib
# (scanStore.ts 파일 생성)
```

### 8. 도움 받기

위 단계로 해결되지 않으면:

1. **브라우저 콘솔 로그** 전체 복사
2. **서버 터미널 출력** 전체 복사
3. **사용한 입력값** (Target URL, JS Path 등)
4. **환경 정보**:
   ```bash
   python --version
   node --version
   npm --version
   ```

이 정보를 포함하여 이슈를 보고하세요.
