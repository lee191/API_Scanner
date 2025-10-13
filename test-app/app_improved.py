"""
개선된 취약한 테스트 애플리케이션
실제 시나리오를 반영한 더 많은 엔드포인트와 취약점 포함
"""

from flask import Flask, request, jsonify, render_template, render_template_string, session, redirect, url_for, make_response, flash
from flask_cors import CORS
import sqlite3
import hashlib
import jwt
import datetime
import os
import subprocess
import pickle
import base64

app = Flask(__name__)
app.secret_key = 'super-secret-key-12345'  # 취약점: 하드코딩된 비밀키
CORS(app)  # 취약점: 모든 origin 허용

JWT_SECRET = 'jwt-secret-key'  # 취약점: 약한 JWT 시크릿

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('test.db')
    c = conn.cursor()

    # 사용자 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT,
                  email TEXT, role TEXT, api_key TEXT)''')

    # 게시글 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY, title TEXT, content TEXT,
                  author_id INTEGER, created_at TIMESTAMP)''')

    # 댓글 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS comments
                 (id INTEGER PRIMARY KEY, post_id INTEGER, content TEXT,
                  author_id INTEGER, created_at TIMESTAMP)''')

    # 결제 정보 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS payments
                 (id INTEGER PRIMARY KEY, user_id INTEGER, card_number TEXT,
                  cvv TEXT, amount REAL, status TEXT)''')

    # 상품 테이블
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, description TEXT,
                  price REAL, category TEXT, stock INTEGER, image_url TEXT)''')

    # 초기 데이터
    try:
        c.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin@test.com', 'admin', 'ADMIN-KEY-12345')")
        c.execute("INSERT INTO users VALUES (2, 'user1', 'password', 'user1@test.com', 'user', 'USER-KEY-67890')")
        c.execute("INSERT INTO users VALUES (3, 'user2', 'qwerty', 'user2@test.com', 'user', 'USER-KEY-ABCDE')")

        c.execute("INSERT INTO posts VALUES (1, 'First Post', 'Hello World', 1, datetime('now'))")
        c.execute("INSERT INTO posts VALUES (2, 'Second Post', 'Test content', 2, datetime('now'))")

        c.execute("INSERT INTO comments VALUES (1, 1, 'Nice post!', 2, datetime('now'))")

        c.execute("INSERT INTO payments VALUES (1, 2, '4532-1234-5678-9010', '123', 99.99, 'completed')")

        # 상품 데이터
        products = [
            (1, '노트북', '고성능 게이밍 노트북', 1500000, 'electronics', 10, '💻'),
            (2, '무선 마우스', '인체공학적 무선 마우스', 35000, 'electronics', 50, '🖱️'),
            (3, '기계식 키보드', 'RGB 기계식 키보드', 120000, 'electronics', 30, '⌨️'),
            (4, '4K 모니터', '27인치 4K UHD 모니터', 450000, 'electronics', 15, '🖥️'),
            (5, '무선 헤드폰', '노이즈 캔슬링 헤드폰', 280000, 'electronics', 25, '🎧'),
            (6, '스마트폰', '최신 플래그십 스마트폰', 1200000, 'electronics', 20, '📱'),
            (7, '태블릿', '10.5인치 태블릿', 600000, 'electronics', 18, '📱'),
            (8, '스마트 워치', '건강 추적 스마트워치', 350000, 'electronics', 40, '⌚'),
        ]
        c.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?)", products)
    except:
        pass

    conn.commit()
    conn.close()

init_db()


# ==================== 웹 페이지 라우트 ====================

@app.route('/')
def index():
    """홈페이지"""
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products LIMIT 6")
    products = c.fetchall()
    conn.close()
    return render_template('index.html', products=products)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """로그인 페이지"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = sqlite3.connect('test.db')
        c = conn.cursor()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        try:
            c.execute(query)
            user = c.fetchone()
            conn.close()
            if user:
                session['user_id'] = user[0]
                session['username'] = user[1]
                session['role'] = user[4]
                flash('로그인 성공!', 'success')
                return redirect(url_for('index'))
            else:
                flash('잘못된 사용자명 또는 비밀번호입니다.', 'error')
        except Exception as e:
            flash(f'로그인 오류: {str(e)}', 'error')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        conn = sqlite3.connect('test.db')
        c = conn.cursor()
        try:
            api_key = hashlib.md5(username.encode()).hexdigest()
            c.execute("INSERT INTO users (username, password, email, role, api_key) VALUES (?, ?, ?, 'user', ?)",
                      (username, password, email, api_key))
            conn.commit()
            flash('회원가입 성공! 로그인해주세요.', 'success')
            return redirect(url_for('login_page'))
        except Exception as e:
            flash(f'회원가입 실패: {str(e)}', 'error')
        finally:
            conn.close()
    return render_template('register.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('index'))


@app.route('/products')
def products_page():
    category = request.args.get('category', 'all')
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    if category == 'all':
        c.execute("SELECT * FROM products")
    else:
        c.execute(f"SELECT * FROM products WHERE category = '{category}'")
    products = c.fetchall()
    conn.close()
    return render_template('products.html', products=products, category=category)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = c.fetchone()
    conn.close()
    if product:
        return render_template('product_detail.html', product=product)
    return "상품을 찾을 수 없습니다", 404


@app.route('/cart')
def cart_page():
    return render_template('cart.html')


@app.route('/profile')
def profile_page():
    if 'username' not in session:
        flash('로그인이 필요합니다.', 'warning')
        return redirect(url_for('login_page'))
    user_id = session.get('user_id')
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return render_template('profile.html', user=user)


@app.route('/admin')
def admin_page():
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template('admin.html', users=users, products=products)


@app.route('/search')
def search_page():
    query = request.args.get('q', '')
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    sql = f"SELECT * FROM products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%'"
    try:
        c.execute(sql)
        products = c.fetchall()
    except:
        products = []
    conn.close()
    return render_template('search.html', products=products, query=query)


# ==================== 인증 API ====================

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    """취약점: SQL Injection, 약한 비밀번호 해싱 없음"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # SQL Injection 취약점
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
    c.execute(query)
    user = c.fetchone()
    conn.close()

    if user:
        # 취약점: 약한 JWT
        token = jwt.encode({
            'user_id': user[0],
            'username': user[1],
            'role': user[4],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=30)
        }, JWT_SECRET, algorithm='HS256')

        session['user_id'] = user[0]
        session['username'] = user[1]

        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user[0],
                'username': user[1],
                'email': user[3],
                'role': user[4]
            }
        })

    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401


@app.route('/api/v1/auth/register', methods=['POST'])
def register():
    """취약점: 비밀번호 해싱 없음, 이메일 검증 없음"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')

    conn = sqlite3.connect('test.db')
    c = conn.cursor()

    try:
        api_key = hashlib.md5(username.encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, email, role, api_key) VALUES (?, ?, ?, 'user', ?)",
                  (username, password, email, api_key))
        conn.commit()
        user_id = c.lastrowid
        conn.close()

        return jsonify({'success': True, 'user_id': user_id, 'api_key': api_key})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@app.route('/api/v1/auth/reset-password', methods=['POST'])
def reset_password():
    """취약점: IDOR, 인증 없이 비밀번호 리셋"""
    data = request.get_json()
    user_id = data.get('user_id')
    new_password = data.get('new_password')

    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("UPDATE users SET password = ? WHERE id = ?", (new_password, user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# ==================== 사용자 API ====================

@app.route('/api/v1/users', methods=['GET'])
def get_users():
    """취약점: 인증 없음, 민감한 정보 노출"""
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("SELECT id, username, email, role, api_key FROM users")
    users = c.fetchall()
    conn.close()

    return jsonify([{
        'id': u[0],
        'username': u[1],
        'email': u[2],
        'role': u[3],
        'api_key': u[4]  # 취약점: API 키 노출
    } for u in users])


@app.route('/api/v1/users/<user_id>', methods=['GET'])
def get_user(user_id):
    """취약점: SQL Injection, IDOR"""
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    # SQL Injection
    query = f"SELECT * FROM users WHERE id = {user_id}"
    c.execute(query)
    user = c.fetchone()
    conn.close()

    if user:
        return jsonify({
            'id': user[0],
            'username': user[1],
            'password': user[2],  # 취약점: 비밀번호 노출
            'email': user[3],
            'role': user[4],
            'api_key': user[5]
        })

    return jsonify({'error': 'User not found'}), 404


@app.route('/api/v1/users/<user_id>', methods=['PUT'])
def update_user(user_id):
    """취약점: IDOR, Mass Assignment"""
    data = request.get_json()

    conn = sqlite3.connect('test.db')
    c = conn.cursor()

    # 취약점: 모든 필드 업데이트 가능 (role 포함)
    for key, value in data.items():
        c.execute(f"UPDATE users SET {key} = ? WHERE id = ?", (value, user_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True})


@app.route('/api/v1/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """취약점: 인증 없음, IDOR"""
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})


# ==================== 게시글 API ====================

@app.route('/api/v1/posts', methods=['GET'])
def get_posts():
    """취약점: NoSQL Injection (시뮬레이션), XSS"""
    search = request.args.get('search', '')

    conn = sqlite3.connect('test.db')
    c = conn.cursor()

    if search:
        # SQL Injection
        query = f"SELECT * FROM posts WHERE title LIKE '%{search}%' OR content LIKE '%{search}%'"
        c.execute(query)
    else:
        c.execute("SELECT * FROM posts")

    posts = c.fetchall()
    conn.close()

    return jsonify([{
        'id': p[0],
        'title': p[1],
        'content': p[2],  # XSS 취약점: 필터링 없음
        'author_id': p[3],
        'created_at': p[4]
    } for p in posts])


@app.route('/api/v1/posts/<post_id>', methods=['GET'])
def get_post(post_id):
    """취약점: SQL Injection"""
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    query = f"SELECT * FROM posts WHERE id = {post_id}"
    c.execute(query)
    post = c.fetchone()
    conn.close()

    if post:
        return jsonify({
            'id': post[0],
            'title': post[1],
            'content': post[2],
            'author_id': post[3],
            'created_at': post[4]
        })

    return jsonify({'error': 'Post not found'}), 404


@app.route('/api/v1/posts', methods=['POST'])
def create_post():
    """취약점: XSS, CSRF"""
    data = request.get_json()

    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("INSERT INTO posts (title, content, author_id, created_at) VALUES (?, ?, ?, datetime('now'))",
              (data.get('title'), data.get('content'), data.get('author_id', 1)))
    conn.commit()
    post_id = c.lastrowid
    conn.close()

    return jsonify({'success': True, 'post_id': post_id})


# ==================== 댓글 API ====================

@app.route('/api/v1/posts/<post_id>/comments', methods=['GET'])
def get_comments(post_id):
    """댓글 조회"""
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    query = f"SELECT * FROM comments WHERE post_id = {post_id}"
    c.execute(query)
    comments = c.fetchall()
    conn.close()

    return jsonify([{
        'id': c[0],
        'post_id': c[1],
        'content': c[2],
        'author_id': c[3],
        'created_at': c[4]
    } for c in comments])


@app.route('/api/v1/comments', methods=['POST'])
def create_comment():
    """취약점: XSS, CSRF"""
    data = request.get_json()

    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("INSERT INTO comments (post_id, content, author_id, created_at) VALUES (?, ?, ?, datetime('now'))",
              (data.get('post_id'), data.get('content'), data.get('author_id', 1)))
    conn.commit()
    comment_id = c.lastrowid
    conn.close()

    return jsonify({'success': True, 'comment_id': comment_id})


# ==================== 결제 API ====================

@app.route('/api/v1/payments', methods=['GET'])
def get_payments():
    """취약점: 인증 없음, 민감한 정보 노출"""
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("SELECT * FROM payments")
    payments = c.fetchall()
    conn.close()

    return jsonify([{
        'id': p[0],
        'user_id': p[1],
        'card_number': p[2],  # 취약점: 카드번호 노출
        'cvv': p[3],  # 취약점: CVV 노출
        'amount': p[4],
        'status': p[5]
    } for p in payments])


@app.route('/api/v1/payments', methods=['POST'])
def create_payment():
    """취약점: 민감한 정보 로깅, 암호화 없음"""
    data = request.get_json()

    print(f"[LOG] Payment: {data}")  # 취약점: 카드 정보 로깅

    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("INSERT INTO payments (user_id, card_number, cvv, amount, status) VALUES (?, ?, ?, ?, 'pending')",
              (data.get('user_id'), data.get('card_number'), data.get('cvv'), data.get('amount')))
    conn.commit()
    payment_id = c.lastrowid
    conn.close()

    return jsonify({'success': True, 'payment_id': payment_id})


# ==================== Shadow APIs (숨겨진 엔드포인트) ====================

@app.route('/api/internal/admin/users', methods=['GET'])
def internal_admin_users():
    """Shadow API: 관리자 전용 (인증 없음)"""
    conn = sqlite3.connect('test.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users")
    users = c.fetchall()
    conn.close()

    return jsonify([{
        'id': u[0],
        'username': u[1],
        'password': u[2],
        'email': u[3],
        'role': u[4],
        'api_key': u[5]
    } for u in users])


@app.route('/api/internal/debug/config', methods=['GET'])
def internal_debug_config():
    """Shadow API: 디버그 설정 노출"""
    return jsonify({
        'database': 'test.db',
        'jwt_secret': JWT_SECRET,
        'app_secret': app.secret_key,
        'debug_mode': True,
        'admin_password': 'admin123',
        'database_connection': 'sqlite:///test.db'
    })


@app.route('/api/internal/backup/database', methods=['GET'])
def internal_backup():
    """Shadow API: 데이터베이스 백업 다운로드"""
    import os
    if os.path.exists('test.db'):
        with open('test.db', 'rb') as f:
            return f.read(), 200, {'Content-Type': 'application/octet-stream'}
    return jsonify({'error': 'Database not found'}), 404


@app.route('/api/internal/exec', methods=['POST'])
def internal_exec():
    """Shadow API: 명령어 실행 (RCE)"""
    data = request.get_json()
    cmd = data.get('command')

    try:
        result = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT)
        return jsonify({'output': result.decode()})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/internal/deserialize', methods=['POST'])
def internal_deserialize():
    """Shadow API: Insecure Deserialization"""
    data = request.get_json()
    serialized = data.get('data')

    try:
        obj = pickle.loads(base64.b64decode(serialized))
        return jsonify({'result': str(obj)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 검색 API ====================

@app.route('/api/v1/search', methods=['GET'])
def search():
    """취약점: SQL Injection, XSS"""
    query = request.args.get('q', '')
    table = request.args.get('table', 'posts')  # 취약점: 테이블 이름 직접 지정

    conn = sqlite3.connect('test.db')
    c = conn.cursor()

    # SQL Injection
    sql = f"SELECT * FROM {table} WHERE title LIKE '%{query}%' OR content LIKE '%{query}%'"

    try:
        c.execute(sql)
        results = c.fetchall()
        conn.close()
        return jsonify({'results': results})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== 파일 업로드 ====================

@app.route('/api/v1/upload', methods=['POST'])
def upload_file():
    """취약점: 파일 업로드 검증 없음"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['file']
    filename = file.filename  # 취약점: 파일명 검증 없음

    # 취약점: 경로 탐색 가능
    file.save(f'uploads/{filename}')

    return jsonify({'success': True, 'filename': filename})


# ==================== Rate Limiting 없는 API ====================

@app.route('/api/v1/newsletter/subscribe', methods=['POST'])
def subscribe_newsletter():
    """취약점: Rate Limiting 없음"""
    data = request.get_json()
    email = data.get('email')

    # Rate limiting 없이 무한 요청 가능
    return jsonify({'success': True, 'message': f'Subscribed: {email}'})


# ==================== JSP 파일 서빙 ====================

@app.route('/static/<path:filename>')
def serve_static(filename):
    """정적 파일 및 JSP 파일 서빙"""
    from flask import send_from_directory
    return send_from_directory('static', filename)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
