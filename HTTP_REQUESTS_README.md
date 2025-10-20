# HTTP Request Files 사용 가이드

## 📌 개요
이 폴더에는 Shadow API Scanner의 모든 API 엔드포인트를 테스트할 수 있는 HTTP 요청 파일이 포함되어 있습니다.

## 📁 파일 설명

- **api_requests.http** - VS Code REST Client용
- **api_requests.req** - IntelliJ HTTP Client용  
- **rest-client.settings.json** - VS Code 환경 변수 설정

## 🚀 사용 방법

### VS Code에서 사용

1. **REST Client 확장 설치**
   - Extension ID: `humao.rest-client`
   - 또는 Extensions에서 "REST Client" 검색

2. **api_requests.http 파일 열기**

3. **요청 실행**
   - 요청 위에 나타나는 "Send Request" 클릭
   - 또는 `Ctrl+Alt+R` (Windows/Linux) / `Cmd+Alt+R` (Mac)

4. **변수 설정**
   - `rest-client.settings.json`에서 `projectId`, `scanId` 값 수정
   - 또는 요청 파일 상단의 `@projectId`, `@scanId` 직접 수정

### IntelliJ IDEA / WebStorm에서 사용

1. **api_requests.req 파일 열기**

2. **요청 실행**
   - 요청 옆 실행 버튼(▶️) 클릭
   - 또는 `Ctrl+Enter`

3. **변수 설정**
   - 파일 상단의 변수 값 직접 수정

## 📝 주요 API 카테고리

### 1. 프로젝트 관리
- ✅ 프로젝트 생성/조회/수정/삭제
- ✅ 프로젝트 목록

### 2. 스캔 관리
- ✅ 스캔 시작 (정적/동적/통합)
- ✅ 스캔 상태 조회
- ✅ 스캔 정지/삭제

### 3. 스캔 결과
- ✅ 엔드포인트 목록
- ✅ 취약점 목록
- ✅ 발견된 경로

### 4. AI 챗 (v4.0)
- ✅ 스캔 결과 요약
- ✅ 보안 취약점 분석
- ✅ **HTTP 트래픽 상세 분석 (NEW!)**
  - Request/Response Headers
  - Request/Response Body
  - Response Time

### 5. 통계
- ✅ 스캔 히스토리
- ✅ 프로젝트 통계

## 🔧 환경 변수 설정

`rest-client.settings.json` 파일에서 환경별로 설정 가능:

```json
{
  "local": {
    "baseUrl": "http://localhost:5001",
    "projectId": "abc-123",
    "scanId": "xyz-789"
  },
  "production": {
    "baseUrl": "https://api.yourdomain.com",
    "projectId": "",
    "scanId": ""
  }
}
```

## 💡 팁

### 변수 사용하기
```http
@projectId = your-project-id-here

### 프로젝트 조회
GET {{baseUrl}}/api/projects/{{projectId}}
```

### 응답 저장하기 (VS Code)
```http
# @name createProject
POST {{baseUrl}}/api/projects
Content-Type: application/json

{
  "name": "New Project"
}

### 생성한 프로젝트 조회
@newProjectId = {{createProject.response.body.id}}
GET {{baseUrl}}/api/projects/{{newProjectId}}
```

### 인증 헤더 추가
```http
POST {{baseUrl}}/api/scan
Authorization: Bearer {{token}}
Content-Type: application/json

{
  "target_url": "http://localhost:5000"
}
```

## 📚 추가 리소스

- [VS Code REST Client 문서](https://marketplace.visualstudio.com/items?itemName=humao.rest-client)
- [IntelliJ HTTP Client 문서](https://www.jetbrains.com/help/idea/http-client-in-product-code-editor.html)
- [API Scanner 문서](./DOCUMENTATION.md)

## 🐛 트러블슈팅

### "Connection refused" 에러
→ API 서버가 실행 중인지 확인: `python api_server.py`

### "404 Not Found" 에러
→ 엔드포인트 URL 확인 (baseUrl이 올바른지 체크)

### "500 Internal Server Error"
→ API 서버 로그 확인 및 DB 상태 점검

### 변수가 적용되지 않음
→ `rest-client.settings.json` 파일 위치 확인 (프로젝트 루트)
