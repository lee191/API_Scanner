# Shadow API Scanner - cURL 명령어 모음
================================================================================

## 📝 사용 방법

1. API 서버 실행: `python api_server.py`
2. 아래 명령어를 복사하여 터미널에서 실행
3. `{project_id}`, `{scan_id}` 등은 실제 값으로 변경

## 📌 주의사항

- Windows PowerShell에서는 백슬래시(\) 대신 백틱(`)을 사용
- JSON 데이터에서 중괄호({})가 있으면 이스케이프 필요

================================================================================


## 프로젝트 관리
--------------------------------------------------------------------------------

### 프로젝트 목록 조회

```bash
curl -X GET http://localhost:5001/api/projects
```

### 프로젝트 생성

```bash
curl -X POST http://localhost:5001/api/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "테스트 프로젝트",
    "description": "cURL로 생성한 프로젝트"
  }'
```

### 프로젝트 상세 조회

```bash
curl -X GET http://localhost:5001/api/projects/{project_id}
```

### 프로젝트 수정

```bash
curl -X PUT http://localhost:5001/api/projects/{project_id} \
  -H "Content-Type: application/json" \
  -d '{
    "name": "수정된 프로젝트",
    "description": "업데이트된 설명"
  }'
```

### 프로젝트 삭제

```bash
curl -X DELETE http://localhost:5001/api/projects/{project_id}
```


## 스캔 관리
--------------------------------------------------------------------------------

### 스캔 시작 (전체)

```bash
curl -X POST http://localhost:5001/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "{project_id}",
    "target_url": "http://localhost:5000",
    "analysis_type": "both",
    "ai_enabled": true,
    "bruteforce_enabled": true,
    "validate": true
  }'
```

### 스캔 시작 (정적 분석만)

```bash
curl -X POST http://localhost:5001/api/scan \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "{project_id}",
    "target_url": "http://localhost:5000",
    "analysis_type": "static",
    "ai_enabled": false,
    "bruteforce_enabled": false,
    "validate": true
  }'
```

### 스캔 상태 조회

```bash
curl -X GET http://localhost:5001/api/status/{scan_id}
```

### 스캔 정지

```bash
curl -X POST http://localhost:5001/api/scan/{scan_id}/stop
```

### 스캔 삭제

```bash
curl -X DELETE http://localhost:5001/api/scan/{scan_id}
```


## 스캔 결과
--------------------------------------------------------------------------------

### 스캔 상세 조회

```bash
curl -X GET http://localhost:5001/api/scan/{scan_id}
```

### 엔드포인트 목록

```bash
curl -X GET http://localhost:5001/api/scan/{scan_id}/endpoints
```

### 취약점 목록

```bash
curl -X GET http://localhost:5001/api/scan/{scan_id}/vulnerabilities
```

### 발견된 경로

```bash
curl -X GET http://localhost:5001/api/scan/{scan_id}/discovered-paths
```


## AI 챗
--------------------------------------------------------------------------------

### AI 챗 (간단한 질문)

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

### AI 챗 (보안 분석)

```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "보안 취약점이 있는지 분석해줘",
    "scan_context": {
      "target_url": "http://localhost:5000",
      "total_endpoints": 50,
      "endpoint_samples": {
        "by_status": {
          "client_error_4xx": [
            {"url": "/admin/dashboard", "method": "GET", "status_code": 401},
            {"url": "/api/secret", "method": "POST", "status_code": 403}
          ]
        },
        "sensitive_endpoints": [
          {"url": "/admin/users", "method": "GET", "status_code": 401}
        ]
      }
    },
    "conversation_history": []
  }'
```


## 통계
--------------------------------------------------------------------------------

### 스캔 히스토리

```bash
curl -X GET http://localhost:5001/api/history?limit=10
```

### 프로젝트 통계

```bash
curl -X GET http://localhost:5001/api/projects/{project_id}/statistics
```


================================================================================
## PowerShell 버전
================================================================================

PowerShell에서는 다음과 같이 사용:

```powershell
# 프로젝트 생성 (PowerShell)
Invoke-RestMethod -Uri "http://localhost:5001/api/projects" `
  -Method POST `
  -ContentType "application/json" `
  -Body (@{
    name = "테스트 프로젝트"
    description = "PowerShell로 생성"
  } | ConvertTo-Json)

# 스캔 시작 (PowerShell)
$body = @{
    project_id = "your-project-id"
    target_url = "http://localhost:5000"
    analysis_type = "both"
    ai_enabled = $true
    bruteforce_enabled = $true
    validate = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5001/api/scan" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```
