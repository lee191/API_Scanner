"""
취약한 테스트 웹 애플리케이션
Shadow API Scanner 테스트용 - 의도적으로 취약점이 포함되어 있음
경고: 절대 프로덕션 환경에서 사용하지 마세요!
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import json
import time

app = Flask(__name__)

# 취약점 1: CORS 설정 문제
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 인메모리 데이터베이스
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT,
            api_key TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY,
            name TEXT,
            price REAL,
            description TEXT
        )
    ''')

    # 샘플 데이터
    cursor.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin@test.com', 'sk_live_abc123xyz')")
    cursor.execute("INSERT INTO users VALUES (2, 'user', 'password', 'user@test.com', 'sk_test_def456')")
    cursor.execute("INSERT INTO products VALUES (1, 'Laptop', 999.99, 'High performance laptop')")
    cursor.execute("INSERT INTO products VALUES (2, 'Mouse', 29.99, 'Wireless mouse')")

    conn.commit()
    return conn

db_conn = init_db()


# 메인 페이지
@app.route('/')
def index():
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Vulnerable Test App</title>
    <script src="/static/app.js"></script>
</head>
<body>
    <h1>취약한 테스트 애플리케이션</h1>
    <p>Shadow API Scanner 테스트용</p>

    <div id="products"></div>
    <div id="user-info"></div>

    <script>
        // API 호출 예시
        fetch('/api/v1/products')
            .then(r => r.json())
            .then(data => {
                document.getElementById('products').innerHTML =
                    '<h2>Products:</h2>' + JSON.stringify(data);
            });
    </script>
</body>
</html>
    ''')


# 취약점 2: 인증 없는 API 엔드포인트
@app.route('/api/v1/users', methods=['GET'])
def get_users():
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, username, email FROM users")
    users = [{'id': row[0], 'username': row[1], 'email': row[2]} for row in cursor.fetchall()]
    return jsonify(users)


# 취약점 3: SQL Injection 취약점
@app.route('/api/v1/user/<user_id>', methods=['GET'])
def get_user(user_id):
    cursor = db_conn.cursor()
    # 의도적인 SQL Injection 취약점
    query = f"SELECT * FROM users WHERE id = {user_id}"
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            return jsonify({
                'id': row[0],
                'username': row[1],
                'password': row[2],  # 취약점: 비밀번호 노출
                'email': row[3],
                'api_key': row[4]    # 취약점: API 키 노출
            })
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        # 취약점: SQL 에러 메시지 노출
        return jsonify({'error': str(e)}), 500


# 취약점 4: XSS 취약점
@app.route('/api/v1/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    # 의도적인 XSS 취약점 - 입력 검증 없음
    return jsonify({
        'query': query,
        'results': f'<div>검색 결과: {query}</div>'
    })


# 취약점 5: Rate Limiting 없음
@app.route('/api/v1/products', methods=['GET'])
def get_products():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = [{'id': row[0], 'name': row[1], 'price': row[2], 'description': row[3]}
                for row in cursor.fetchall()]
    return jsonify(products)


# 취약점 6: 민감한 정보가 URL에 포함
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    username = request.args.get('username')  # 취약점: URL에 username
    password = request.args.get('password')  # 취약점: URL에 password

    cursor = db_conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")
    user = cursor.fetchone()

    if user:
        return jsonify({
            'success': True,
            'token': 'fake_jwt_token_12345',  # 취약점: 안전하지 않은 토큰
            'api_key': user[4]  # 취약점: API 키 노출
        })
    return jsonify({'success': False}), 401


# 취약점 7: HTTP를 통한 인증 (HTTPS 없음)
@app.route('/api/v1/secure/data', methods=['GET'])
def secure_data():
    auth_header = request.headers.get('Authorization')
    # 취약점: 약한 인증 체크
    if auth_header and 'Bearer' in auth_header:
        return jsonify({
            'secret': 'This is confidential data',
            'credit_card': '4532-1234-5678-9010',  # 취약점: 민감 데이터 노출
            'ssn': '123-45-6789'
        })
    return jsonify({'error': 'Unauthorized'}), 401


# 숨겨진 API 엔드포인트 (Shadow API)
@app.route('/api/internal/admin/users', methods=['GET'])
def admin_users():
    # 문서화되지 않은 내부 API
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = [{'id': row[0], 'username': row[1], 'password': row[2],
              'email': row[3], 'api_key': row[4]} for row in cursor.fetchall()]
    return jsonify(users)


@app.route('/api/internal/debug/config', methods=['GET'])
def debug_config():
    # 취약점: 디버그 정보 노출
    return jsonify({
        'database': 'sqlite:///production.db',
        'secret_key': 'super_secret_key_123',
        'api_keys': {
            'stripe': 'sk_live_abc123',
            'aws': 'AKIAIOSFODNN7EXAMPLE'
        },
        'debug': True
    })


# 브루트포싱 테스트용 숨겨진 페이지들
@app.route('/admin')
def admin_page():
    """브루트포싱으로 발견 가능한 관리자 페이지"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel</title>
    <script src="/static/admin.js"></script>
    <script src="/static/admin-dashboard.js"></script>
</head>
<body>
    <h1>🔐 Admin Panel</h1>
    <p>관리자 전용 페이지 - 브루트포싱으로 발견됨!</p>
    <div id="admin-content"></div>
    <script>
        // 관리자 API 호출
        fetch('/api/internal/admin/users')
            .then(r => r.json())
            .then(data => console.log('Admin users:', data));
    </script>
</body>
</html>
    ''')


@app.route('/internal')
def internal_page():
    """브루트포싱으로 발견 가능한 내부 페이지"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Internal Dashboard</title>
    <script src="/static/internal-api.js"></script>
    <script src="/static/internal-utils.js"></script>
</head>
<body>
    <h1>🏢 Internal Dashboard</h1>
    <p>내부 직원 전용 페이지</p>
    <div id="internal-stats"></div>
    <script>
        // 내부 API 호출
        fetch('/api/internal/stats')
            .then(r => r.json())
            .then(data => console.log('Internal stats:', data));
    </script>
</body>
</html>
    ''')


@app.route('/debug')
def debug_page():
    """브루트포싱으로 발견 가능한 디버그 페이지"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Debug Console</title>
    <script src="/static/debug-console.js"></script>
    <script src="/static/debug-logger.js"></script>
</head>
<body>
    <h1>🐛 Debug Console</h1>
    <p>개발자 디버그 콘솔</p>
    <div id="debug-output"></div>
    <script>
        // 디버그 API 호출
        fetch('/api/internal/debug/config')
            .then(r => r.json())
            .then(data => {
                console.log('Debug config:', data);
                document.getElementById('debug-output').innerHTML =
                    '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            });
    </script>
</body>
</html>
    ''')


@app.route('/backup')
def backup_page():
    """브루트포싱으로 발견 가능한 백업 페이지"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Backup Management</title>
    <script src="/static/backup-manager.js"></script>
</head>
<body>
    <h1>💾 Backup Management</h1>
    <p>데이터베이스 백업 관리</p>
    <div id="backup-list"></div>
</body>
</html>
    ''')


@app.route('/api')
def api_docs():
    """브루트포싱으로 발견 가능한 API 문서"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>API Documentation</title>
    <script src="/static/api-client.js"></script>
    <script src="/static/api-explorer.js"></script>
</head>
<body>
    <h1>📚 API Documentation</h1>
    <h2>Public APIs</h2>
    <ul>
        <li>GET /api/v1/products</li>
        <li>GET /api/v1/users</li>
    </ul>
    <h2>Internal APIs (Shadow APIs)</h2>
    <ul>
        <li>GET /api/internal/admin/users</li>
        <li>GET /api/internal/debug/config</li>
        <li>GET /api/internal/stats</li>
        <li>POST /api/internal/execute</li>
    </ul>
</body>
</html>
    ''')


# 추가 Shadow API 엔드포인트
@app.route('/api/internal/stats', methods=['GET'])
def internal_stats():
    """숨겨진 통계 API"""
    return jsonify({
        'total_users': 150,
        'active_sessions': 42,
        'server_load': 0.65,
        'database_size': '2.3GB',
        'last_backup': '2025-10-13 10:30:00'
    })


@app.route('/api/internal/execute', methods=['POST'])
def internal_execute():
    """위험한 내부 실행 API"""
    command = request.json.get('command', '')
    # 취약점: 명령어 실행 (실제로는 실행하지 않음)
    return jsonify({
        'status': 'executed',
        'command': command,
        'warning': 'This is a dangerous endpoint!'
    })


# 취약한 파일 업로드
@app.route('/api/v1/upload', methods=['POST'])
def upload_file():
    # 취약점: 파일 타입 검증 없음
    if 'file' in request.files:
        file = request.files['file']
        return jsonify({'message': 'File uploaded', 'filename': file.filename})
    return jsonify({'error': 'No file'}), 400


# CSRF 토큰 없는 중요 작업
@app.route('/api/v1/user/delete', methods=['POST'])
def delete_user():
    # 취약점: CSRF 보호 없음
    user_id = request.json.get('user_id')
    return jsonify({'message': f'User {user_id} deleted'})


if __name__ == '__main__':
    print("=" * 60)
    print("[WARNING] Vulnerable Test Application Starting")
    print("[WARNING] This app contains intentional vulnerabilities")
    print("[WARNING] Never use in production!")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
