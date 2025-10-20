"""
Generate cURL commands for testing API endpoints.
모든 주요 API 엔드포인트에 대한 cURL 명령어를 생성합니다.
"""

import json

# API Base URL
BASE_URL = "http://localhost:5001"

# cURL 명령어 템플릿
CURL_COMMANDS = {
    "프로젝트 관리": {
        "프로젝트 목록 조회": f"""curl -X GET {BASE_URL}/api/projects""",
        
        "프로젝트 생성": f"""curl -X POST {BASE_URL}/api/projects \\
  -H "Content-Type: application/json" \\
  -d '{{
    "name": "테스트 프로젝트",
    "description": "cURL로 생성한 프로젝트"
  }}'""",
        
        "프로젝트 상세 조회": f"""curl -X GET {BASE_URL}/api/projects/{{project_id}}""",
        
        "프로젝트 수정": f"""curl -X PUT {BASE_URL}/api/projects/{{project_id}} \\
  -H "Content-Type: application/json" \\
  -d '{{
    "name": "수정된 프로젝트",
    "description": "업데이트된 설명"
  }}'""",
        
        "프로젝트 삭제": f"""curl -X DELETE {BASE_URL}/api/projects/{{project_id}}""",
    },
    
    "스캔 관리": {
        "스캔 시작 (전체)": f"""curl -X POST {BASE_URL}/api/scan \\
  -H "Content-Type: application/json" \\
  -d '{{
    "project_id": "{{project_id}}",
    "target_url": "http://localhost:5000",
    "analysis_type": "both",
    "ai_enabled": true,
    "bruteforce_enabled": true,
    "validate": true
  }}'""",
        
        "스캔 시작 (정적 분석만)": f"""curl -X POST {BASE_URL}/api/scan \\
  -H "Content-Type: application/json" \\
  -d '{{
    "project_id": "{{project_id}}",
    "target_url": "http://localhost:5000",
    "analysis_type": "static",
    "ai_enabled": false,
    "bruteforce_enabled": false,
    "validate": true
  }}'""",
        
        "스캔 상태 조회": f"""curl -X GET {BASE_URL}/api/status/{{scan_id}}""",
        
        "스캔 정지": f"""curl -X POST {BASE_URL}/api/scan/{{scan_id}}/stop""",
        
        "스캔 삭제": f"""curl -X DELETE {BASE_URL}/api/scan/{{scan_id}}""",
    },
    
    "스캔 결과": {
        "스캔 상세 조회": f"""curl -X GET {BASE_URL}/api/scan/{{scan_id}}""",
        
        "엔드포인트 목록": f"""curl -X GET {BASE_URL}/api/scan/{{scan_id}}/endpoints""",
        
        "취약점 목록": f"""curl -X GET {BASE_URL}/api/scan/{{scan_id}}/vulnerabilities""",
        
        "발견된 경로": f"""curl -X GET {BASE_URL}/api/scan/{{scan_id}}/discovered-paths""",
    },
    
    "AI 챗": {
        "AI 챗 (간단한 질문)": f"""curl -X POST {BASE_URL}/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{{
    "message": "스캔 결과를 요약해줘",
    "scan_context": {{
      "target_url": "http://localhost:5000",
      "total_endpoints": 50,
      "statistics": {{
        "count_2xx": 30,
        "count_4xx": 15,
        "count_5xx": 5
      }}
    }},
    "conversation_history": []
  }}'""",
        
        "AI 챗 (보안 분석)": f"""curl -X POST {BASE_URL}/api/chat \\
  -H "Content-Type: application/json" \\
  -d '{{
    "message": "보안 취약점이 있는지 분석해줘",
    "scan_context": {{
      "target_url": "http://localhost:5000",
      "total_endpoints": 50,
      "endpoint_samples": {{
        "by_status": {{
          "client_error_4xx": [
            {{"url": "/admin/dashboard", "method": "GET", "status_code": 401}},
            {{"url": "/api/secret", "method": "POST", "status_code": 403}}
          ]
        }},
        "sensitive_endpoints": [
          {{"url": "/admin/users", "method": "GET", "status_code": 401}}
        ]
      }}
    }},
    "conversation_history": []
  }}'""",
    },
    
    "통계": {
        "스캔 히스토리": f"""curl -X GET {BASE_URL}/api/history?limit=10""",
        
        "프로젝트 통계": f"""curl -X GET {BASE_URL}/api/projects/{{project_id}}/statistics""",
    }
}

def generate_curl_file():
    """Generate curl commands documentation."""
    output = []
    output.append("# Shadow API Scanner - cURL 명령어 모음")
    output.append("=" * 80)
    output.append("")
    output.append("## 📝 사용 방법")
    output.append("")
    output.append("1. API 서버 실행: `python api_server.py`")
    output.append("2. 아래 명령어를 복사하여 터미널에서 실행")
    output.append("3. `{project_id}`, `{scan_id}` 등은 실제 값으로 변경")
    output.append("")
    output.append("## 📌 주의사항")
    output.append("")
    output.append("- Windows PowerShell에서는 백슬래시(\\) 대신 백틱(`)을 사용")
    output.append("- JSON 데이터에서 중괄호({})가 있으면 이스케이프 필요")
    output.append("")
    output.append("=" * 80)
    output.append("")
    
    for category, commands in CURL_COMMANDS.items():
        output.append(f"\n## {category}")
        output.append("-" * 80)
        output.append("")
        
        for name, curl_cmd in commands.items():
            output.append(f"### {name}")
            output.append("")
            output.append("```bash")
            output.append(curl_cmd)
            output.append("```")
            output.append("")
    
    # PowerShell 버전
    output.append("\n" + "=" * 80)
    output.append("## PowerShell 버전")
    output.append("=" * 80)
    output.append("")
    output.append("PowerShell에서는 다음과 같이 사용:")
    output.append("")
    output.append("```powershell")
    output.append("# 프로젝트 생성 (PowerShell)")
    output.append(f"""Invoke-RestMethod -Uri "{BASE_URL}/api/projects" `
  -Method POST `
  -ContentType "application/json" `
  -Body (@{{
    name = "테스트 프로젝트"
    description = "PowerShell로 생성"
  }} | ConvertTo-Json)""")
    output.append("")
    output.append("# 스캔 시작 (PowerShell)")
    output.append(f"""$body = @{{
    project_id = "your-project-id"
    target_url = "http://localhost:5000"
    analysis_type = "both"
    ai_enabled = $true
    bruteforce_enabled = $true
    validate = $true
}} | ConvertTo-Json

Invoke-RestMethod -Uri "{BASE_URL}/api/scan" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body""")
    output.append("```")
    output.append("")
    
    return "\n".join(output)

def generate_postman_collection():
    """Generate Postman collection JSON."""
    collection = {
        "info": {
            "name": "Shadow API Scanner",
            "description": "API 스캐너 테스트용 Postman 컬렉션",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "variable": [
            {
                "key": "base_url",
                "value": "http://localhost:5001",
                "type": "string"
            },
            {
                "key": "project_id",
                "value": "",
                "type": "string"
            },
            {
                "key": "scan_id",
                "value": "",
                "type": "string"
            }
        ],
        "item": [
            {
                "name": "프로젝트 관리",
                "item": [
                    {
                        "name": "프로젝트 목록",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": "{{base_url}}/api/projects"
                        }
                    },
                    {
                        "name": "프로젝트 생성",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "테스트 프로젝트",
                                    "description": "Postman으로 생성"
                                }, indent=2)
                            },
                            "url": "{{base_url}}/api/projects"
                        }
                    }
                ]
            },
            {
                "name": "스캔",
                "item": [
                    {
                        "name": "스캔 시작",
                        "request": {
                            "method": "POST",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "project_id": "{{project_id}}",
                                    "target_url": "http://localhost:5000",
                                    "analysis_type": "both",
                                    "ai_enabled": True,
                                    "bruteforce_enabled": True,
                                    "validate": True
                                }, indent=2)
                            },
                            "url": "{{base_url}}/api/scan"
                        }
                    },
                    {
                        "name": "스캔 상태",
                        "request": {
                            "method": "GET",
                            "header": [],
                            "url": "{{base_url}}/api/status/{{scan_id}}"
                        }
                    }
                ]
            }
        ]
    }
    return json.dumps(collection, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    # Generate cURL commands
    print("📝 Generating cURL commands...")
    curl_doc = generate_curl_file()
    
    with open("CURL_COMMANDS.md", "w", encoding="utf-8") as f:
        f.write(curl_doc)
    print("✅ Generated: CURL_COMMANDS.md")
    
    # Generate Postman collection
    print("📝 Generating Postman collection...")
    postman_collection = generate_postman_collection()
    
    with open("API_Scanner.postman_collection.json", "w", encoding="utf-8") as f:
        f.write(postman_collection)
    print("✅ Generated: API_Scanner.postman_collection.json")
    
    print("\n🎉 Complete!")
    print("\n사용 방법:")
    print("  1. CURL_COMMANDS.md - cURL 명령어 참고")
    print("  2. API_Scanner.postman_collection.json - Postman에서 Import")
