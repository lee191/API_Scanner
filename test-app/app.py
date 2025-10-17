"""
취약한 테스트 웹 애플리케이션
Shadow API Scanner 테스트용 - 의도적으로 취약점이 포함되어 있음
경고: 절대 프로덕션 환경에서 사용하지 마세요!
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import json

app = Flask(__name__)

# CORS 설정
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
    cursor.execute("INSERT INTO products VALUES (3, 'Keyboard', 79.99, 'Mechanical keyboard')")
    cursor.execute("INSERT INTO products VALUES (4, 'Monitor', 299.99, '27-inch 4K monitor')")

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
    <!-- 모든 JavaScript 파일 로드 -->
    <script src="/static/main.js"></script>
    <script src="/static/auth.js"></script>
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


# Public API: 제품 목록
@app.route('/api/v1/products', methods=['GET'])
def get_products():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM products")
    products = [{'id': row[0], 'name': row[1], 'price': row[2], 'description': row[3]}
                for row in cursor.fetchall()]
    return jsonify(products)


# Public API: 사용자 목록 (인증 없음)
@app.route('/api/v1/users', methods=['GET'])
def get_users():
    cursor = db_conn.cursor()
    cursor.execute("SELECT id, username, email FROM users")
    users = [{'id': row[0], 'username': row[1], 'email': row[2]} for row in cursor.fetchall()]
    return jsonify(users)


# Public API: 사용자 상세 (SQL Injection 취약점)
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


# Public API: 로그인
@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')

    cursor = db_conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")
    user = cursor.fetchone()

    if user:
        return jsonify({
            'success': True,
            'token': 'fake_jwt_token_12345',
            'api_key': user[4]
        })
    return jsonify({'success': False}), 401


# Shadow API: 관리자용 사용자 목록 (비밀번호 포함)
@app.route('/api/internal/admin/users', methods=['GET'])
def admin_users():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = [{'id': row[0], 'username': row[1], 'password': row[2],
              'email': row[3], 'api_key': row[4]} for row in cursor.fetchall()]
    return jsonify(users)


# Shadow API: 디버그 설정 정보
@app.route('/api/internal/debug/config', methods=['GET'])
def debug_config():
    return jsonify({
        'database': 'sqlite:///production.db',
        'secret_key': 'super_secret_key_123',
        'api_keys': {
            'stripe': 'sk_live_abc123',
            'aws': 'AKIAIOSFODNN7EXAMPLE'
        },
        'debug': True
    })


# ========== 새로 추가된 엔드포인트 (5개) ==========

# Public API: 제품 상세 조회
@app.route('/api/v1/products/<product_id>', methods=['GET'])
def get_product_detail(product_id):
    cursor = db_conn.cursor()
    # 의도적인 SQL Injection 취약점
    query = f"SELECT * FROM products WHERE id = {product_id}"
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            return jsonify({
                'id': row[0],
                'name': row[1],
                'price': row[2],
                'description': row[3],
                'stock': 100  # 고정값
            })
        return jsonify({'error': 'Product not found'}), 404
    except Exception as e:
        # 취약점: SQL 에러 메시지 노출
        return jsonify({'error': str(e)}), 500


# Public API: 제품 생성
@app.route('/api/v1/products', methods=['POST'])
def create_product():
    data = request.get_json() or {}
    name = data.get('name', '')
    price = data.get('price', 0)
    description = data.get('description', '')

    # 입력 검증 없음 (취약점)
    cursor = db_conn.cursor()

    try:
        # 의도적인 SQL Injection 취약점
        query = f"INSERT INTO products (name, price, description) VALUES ('{name}', {price}, '{description}')"
        cursor.execute(query)
        db_conn.commit()

        return jsonify({
            'success': True,
            'message': 'Product created',
            'product': {'name': name, 'price': price, 'description': description}
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Public API: 사용자 프로필 조회
@app.route('/api/v1/user/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
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
                'email': row[3],
                'bio': 'User biography here',
                'created_at': '2025-01-01',
                'last_login': '2025-01-15'
            })
        return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        # 취약점: SQL 에러 메시지 노출
        return jsonify({'error': str(e)}), 500


# Shadow API: 시스템 메트릭 (민감한 시스템 정보 노출)
@app.route('/api/internal/metrics', methods=['GET'])
def get_metrics():
    return jsonify({
        'system': {
            'hostname': 'prod-server-01',
            'os': 'Ubuntu 20.04',
            'python_version': '3.9.7',
            'uptime': '45 days',
            'memory_usage': '78%',
            'cpu_usage': '34%'
        },
        'database': {
            'host': '10.0.1.50',
            'port': 5432,
            'database': 'production_db',
            'username': 'db_admin',
            'connections': 45,
            'max_connections': 100
        },
        'api': {
            'requests_per_minute': 1240,
            'error_rate': '0.5%',
            'avg_response_time': '120ms'
        },
        'sensitive_paths': [
            '/var/www/app/config.py',
            '/etc/nginx/nginx.conf',
            '/home/admin/.ssh/id_rsa'
        ]
    })


# Shadow API: 로그 조회 (민감한 로그 정보 노출)
@app.route('/api/internal/logs', methods=['GET'])
def get_logs():
    # 쿼리 파라미터로 로그 타입 받기
    log_type = request.args.get('type', 'all')
    limit = request.args.get('limit', '50')

    # 의도적인 취약점: 입력 검증 없음
    logs = [
        {
            'timestamp': '2025-01-15 10:30:15',
            'level': 'INFO',
            'message': 'User admin logged in from 192.168.1.100',
            'session_id': 'sess_abc123'
        },
        {
            'timestamp': '2025-01-15 10:31:22',
            'level': 'WARNING',
            'message': 'Failed login attempt for user: admin, password: admin123',
            'ip': '192.168.1.200'
        },
        {
            'timestamp': '2025-01-15 10:32:45',
            'level': 'ERROR',
            'message': 'Database connection failed: password=db_password123 host=10.0.1.50',
            'stack_trace': '/var/www/app/database.py line 45'
        },
        {
            'timestamp': '2025-01-15 10:33:10',
            'level': 'DEBUG',
            'message': 'API Key used: sk_live_abc123xyz',
            'endpoint': '/api/v1/users'
        },
        {
            'timestamp': '2025-01-15 10:34:00',
            'level': 'INFO',
            'message': f'Fetching logs with type={log_type}, limit={limit}',
            'user': 'admin'
        }
    ]

    return jsonify({
        'total': len(logs),
        'logs': logs,
        'query': {
            'type': log_type,
            'limit': limit
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("[WARNING] Vulnerable Test Application Starting")
    print("[WARNING] This app contains intentional vulnerabilities")
    print("[WARNING] Never use in production!")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
