"""
Generate .http/.req files for REST Client (VS Code/IntelliJ)
모든 주요 API 엔드포인트에 대한 HTTP 요청 파일을 생성합니다.
"""

# API Base URL
BASE_URL = "http://localhost:5001"

# HTTP Request 템플릿
HTTP_REQUESTS = """### Shadow API Scanner - HTTP Request File
### VS Code REST Client 또는 IntelliJ HTTP Client에서 사용 가능
### 사용 방법: 각 요청 앞의 "Send Request" 버튼 클릭 또는 Ctrl+Alt+R

### ============================================================
### 변수 설정
### ============================================================
@baseUrl = http://localhost:5001
@projectId = {{project_id}}
@scanId = {{scan_id}}

### ============================================================
### 프로젝트 관리
### ============================================================

### 프로젝트 목록 조회
GET {{baseUrl}}/api/projects

###

### 프로젝트 생성
POST {{baseUrl}}/api/projects
Content-Type: application/json

{
  "name": "테스트 프로젝트",
  "description": "HTTP Request로 생성한 프로젝트"
}

###

### 프로젝트 상세 조회
# @name getProject
GET {{baseUrl}}/api/projects/{{projectId}}

###

### 프로젝트 수정
PUT {{baseUrl}}/api/projects/{{projectId}}
Content-Type: application/json

{
  "name": "수정된 프로젝트",
  "description": "업데이트된 설명"
}

###

### 프로젝트 삭제
DELETE {{baseUrl}}/api/projects/{{projectId}}

###

### ============================================================
### 스캔 관리
### ============================================================

### 스캔 시작 (전체 분석)
# @name startScan
POST {{baseUrl}}/api/scan
Content-Type: application/json

{
  "project_id": "{{projectId}}",
  "target_url": "http://localhost:5000",
  "analysis_type": "both",
  "ai_enabled": true,
  "bruteforce_enabled": true,
  "validate": true
}

###

### 스캔 시작 (정적 분석만)
POST {{baseUrl}}/api/scan
Content-Type: application/json

{
  "project_id": "{{projectId}}",
  "target_url": "http://localhost:5000",
  "analysis_type": "static",
  "ai_enabled": false,
  "bruteforce_enabled": false,
  "validate": true
}

###

### 스캔 시작 (동적 분석만)
POST {{baseUrl}}/api/scan
Content-Type: application/json

{
  "project_id": "{{projectId}}",
  "target_url": "http://localhost:5000",
  "analysis_type": "dynamic",
  "ai_enabled": false,
  "bruteforce_enabled": false,
  "validate": true
}

###

### 스캔 상태 조회
# @name getScanStatus
GET {{baseUrl}}/api/status/{{scanId}}

###

### 스캔 정지
POST {{baseUrl}}/api/scan/{{scanId}}/stop

###

### 스캔 삭제
DELETE {{baseUrl}}/api/scan/{{scanId}}

###

### ============================================================
### 스캔 결과 조회
### ============================================================

### 스캔 상세 정보
GET {{baseUrl}}/api/scan/{{scanId}}

###

### 엔드포인트 목록
GET {{baseUrl}}/api/scan/{{scanId}}/endpoints

###

### 엔드포인트 목록 (필터링: GET 메서드만)
GET {{baseUrl}}/api/scan/{{scanId}}/endpoints?method=GET

###

### 엔드포인트 목록 (필터링: 200 응답만)
GET {{baseUrl}}/api/scan/{{scanId}}/endpoints?status_code=200

###

### 취약점 목록
GET {{baseUrl}}/api/scan/{{scanId}}/vulnerabilities

###

### 취약점 목록 (심각도별)
GET {{baseUrl}}/api/scan/{{scanId}}/vulnerabilities?severity=high

###

### 발견된 경로 목록
GET {{baseUrl}}/api/scan/{{scanId}}/discovered-paths

###

### ============================================================
### AI 챗 (v4.0 - HTTP 트래픽 분석)
### ============================================================

### AI 챗 - 간단한 질문
POST {{baseUrl}}/api/chat
Content-Type: application/json

{
  "message": "스캔 결과를 요약해줘",
  "scan_context": {
    "target_url": "http://localhost:5000",
    "total_endpoints": 50,
    "statistics": {
      "count_2xx": 30,
      "count_4xx": 15,
      "count_5xx": 5
    }
  },
  "conversation_history": []
}

###

### AI 챗 - 보안 취약점 분석
POST {{baseUrl}}/api/chat
Content-Type: application/json

{
  "message": "보안 취약점이 있는지 분석해줘",
  "scan_context": {
    "target_url": "http://localhost:5000",
    "total_endpoints": 50,
    "endpoint_samples": {
      "by_status": {
        "client_error_4xx": [
          {
            "url": "/admin/dashboard",
            "method": "GET",
            "status_code": 401
          },
          {
            "url": "/api/secret",
            "method": "POST",
            "status_code": 403
          }
        ]
      },
      "sensitive_endpoints": [
        {
          "url": "/admin/users",
          "method": "GET",
          "status_code": 401
        }
      ]
    }
  },
  "conversation_history": []
}

###

### AI 챗 - HTTP 트래픽 상세 분석 (v4.0)
POST {{baseUrl}}/api/chat
Content-Type: application/json

{
  "message": "이 엔드포인트의 HTTP 트래픽을 분석해줘",
  "scan_context": {
    "target_url": "http://localhost:5000",
    "endpoint_samples": {
      "http_traffic": [
        {
          "url": "/api/users",
          "method": "POST",
          "status_code": 201,
          "request_headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer token123"
          },
          "request_body": "{\"username\":\"test\",\"password\":\"pass123\"}",
          "response_headers": {
            "Content-Type": "application/json",
            "Set-Cookie": "session=abc123"
          },
          "response_body": "{\"id\":1,\"username\":\"test\",\"created\":true}",
          "response_time": 245
        }
      ]
    }
  },
  "conversation_history": []
}

###

### AI 챗 - 대화 이어가기
POST {{baseUrl}}/api/chat
Content-Type: application/json

{
  "message": "좀 더 자세히 설명해줘",
  "scan_context": {
    "target_url": "http://localhost:5000",
    "total_endpoints": 50
  },
  "conversation_history": [
    {
      "role": "user",
      "content": "스캔 결과를 요약해줘"
    },
    {
      "role": "assistant",
      "content": "스캔 결과 50개의 엔드포인트가 발견되었습니다..."
    }
  ]
}

###

### ============================================================
### 통계 및 히스토리
### ============================================================

### 스캔 히스토리 (최근 10개)
GET {{baseUrl}}/api/history?limit=10

###

### 스캔 히스토리 (최근 50개)
GET {{baseUrl}}/api/history?limit=50

###

### 프로젝트 통계
GET {{baseUrl}}/api/projects/{{projectId}}/statistics

###

### ============================================================
### 헬스체크
### ============================================================

### 서버 상태 확인
GET {{baseUrl}}/health

###

### API 버전 확인
GET {{baseUrl}}/api/version

###
"""

def generate_http_file():
    """Generate .http file for REST Client."""
    with open("api_requests.http", "w", encoding="utf-8") as f:
        f.write(HTTP_REQUESTS)
    print("✅ Generated: api_requests.http")
    
    # .req 파일도 동일하게 생성 (IntelliJ 호환)
    with open("api_requests.req", "w", encoding="utf-8") as f:
        f.write(HTTP_REQUESTS)
    print("✅ Generated: api_requests.req")

def generate_vscode_settings():
    """Generate VS Code REST Client settings."""
    settings = """{
  "rest-client.environmentVariables": {
    "$shared": {
      "baseUrl": "http://localhost:5001",
      "targetUrl": "http://localhost:5000"
    },
    "local": {
      "baseUrl": "http://localhost:5001",
      "projectId": "your-project-id-here",
      "scanId": "your-scan-id-here"
    },
    "production": {
      "baseUrl": "https://api.yourdomain.com",
      "projectId": "",
      "scanId": ""
    }
  }
}
"""
    with open("rest-client.settings.json", "w", encoding="utf-8") as f:
        f.write(settings)
    print("✅ Generated: rest-client.settings.json")

def generate_readme():
    """Generate README for HTTP requests."""
    readme = """# HTTP Request Files 사용 가이드

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
"""
    
    with open("HTTP_REQUESTS_README.md", "w", encoding="utf-8") as f:
        f.write(readme)
    print("✅ Generated: HTTP_REQUESTS_README.md")

if __name__ == "__main__":
    print("📝 Generating HTTP request files...")
    print()
    
    # Generate .http and .req files
    generate_http_file()
    
    # Generate VS Code settings
    generate_vscode_settings()
    
    # Generate README
    generate_readme()
    
    print()
    print("🎉 Complete!")
    print()
    print("사용 방법:")
    print("  1. VS Code: REST Client 확장 설치 → api_requests.http 열기")
    print("  2. IntelliJ: api_requests.req 열기")
    print("  3. rest-client.settings.json에서 projectId, scanId 설정")
    print("  4. HTTP_REQUESTS_README.md에서 자세한 가이드 확인")
