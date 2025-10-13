# Shadow API Scanner - Web UI

Next.js 기반 웹 인터페이스로 Shadow API Scanner를 사용할 수 있습니다.

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
cd web-ui
npm install
```

### 2. 개발 서버 실행

```bash
npm run dev
```

브라우저에서 http://localhost:3000 접속

### 3. 프로덕션 빌드

```bash
npm run build
npm start
```

## 📁 프로젝트 구조

```
web-ui/
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── scan/route.ts         # 스캔 시작 API
│   │   │   └── status/[scanId]/      # 스캔 상태 확인 API
│   │   ├── globals.css               # 전역 스타일
│   │   ├── layout.tsx                # 루트 레이아웃
│   │   └── page.tsx                  # 메인 페이지
│   └── types/
│       └── index.ts                  # TypeScript 타입 정의
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.mjs
```

## ✨ 주요 기능

### 1. 대화형 스캔 인터페이스
- 타겟 URL 입력
- JavaScript 경로 지정 (선택)
- 분석 타입 선택:
  - JS Analysis Only: JavaScript 파일만 분석
  - Full Scan: 전체 스캔 (JS + 취약점)

### 2. 실시간 스캔 진행 상태
- 스캔 진행률 표시
- 실시간 상태 업데이트

### 3. 시각화된 결과
- 📊 통계 대시보드
- 🌐 발견된 API 엔드포인트 목록
- 🛡️ 취약점 목록 (심각도별 색상 구분)
  - 🔴 Critical
  - 🟠 High
  - 🟡 Medium
  - 🔵 Low

## 🔧 API 엔드포인트

### POST /api/scan
스캔 시작

**Request:**
```json
{
  "target_url": "http://localhost:5000",
  "js_path": "path/to/js/files",
  "scan_vulns": true,
  "analysis_type": "full_scan"
}
```

**Response:**
```json
{
  "scan_id": "uuid",
  "status": "pending",
  "message": "Scan started successfully"
}
```

### GET /api/status/[scanId]
스캔 상태 확인

**Response:**
```json
{
  "scan_id": "uuid",
  "status": "completed",
  "progress": 100,
  "message": "Scan completed successfully",
  "result": {
    "target": "http://localhost:5000",
    "statistics": {
      "total_endpoints": 15,
      "total_vulnerabilities": 27,
      "critical": 2,
      "high": 6,
      "medium": 19
    },
    "endpoints": [...],
    "vulnerabilities": [...]
  }
}
```

## 🔌 Python Scanner와 통합

웹 UI는 백엔드에서 Python Scanner CLI를 실행합니다.

**요구사항:**
- Python 3.8+
- Shadow API Scanner CLI가 `../` (부모 디렉토리)에 설치되어 있어야 함

**자동 실행 명령어:**
```bash
# JS 분석만
python main.py analyze <js_path> --base-url <target_url>

# 전체 스캔
python main.py full-scan <target_url> --js-path <js_path> --scan-vulns --output <output_path>
```

## 🎨 스타일링

- **Tailwind CSS**: 유틸리티 기반 스타일링
- **Lucide React**: 아이콘
- **그라디언트 배경**: 현대적인 UI
- **반응형 디자인**: 모바일/데스크톱 지원

## 📝 환경 변수

`.env.local` 파일 생성 (선택사항):

```env
SCANNER_API_URL=http://localhost:8000
```

## 🐛 문제 해결

### Python 스크립트를 찾을 수 없음
```bash
# web-ui 디렉토리가 Shadow-API 프로젝트 내부에 있는지 확인
Shadow-API/
├── main.py
├── src/
├── web-ui/  <-- 여기
```

### 포트 충돌
```bash
# 다른 포트 사용
PORT=3001 npm run dev
```

### 스캔 타임아웃
`src/app/api/scan/route.ts`에서 타임아웃 조정:
```typescript
timeout: 300000 // 5분 -> 10분으로 변경
```

## 🚀 배포

### Vercel 배포
```bash
npm install -g vercel
vercel
```

### Docker 배포
```bash
docker build -t shadow-api-web .
docker run -p 3000:3000 shadow-api-web
```

## 📄 라이선스

교육 및 보안 연구 목적으로 제공됩니다.

---

**Shadow API Scanner Web UI** - 더 쉽고 직관적인 API 보안 스캔 🔍🛡️
