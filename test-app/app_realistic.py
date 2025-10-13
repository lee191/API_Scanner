"""
실제 웹 환경처럼 개선된 취약한 전자상거래 애플리케이션
"""

from flask import Flask, request, jsonify, render_template, session, redirect, url_for, make_response, flash
from flask_cors import CORS
import sqlite3
import hashlib
import jwt
import datetime
import os
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super-secret-key-12345'
CORS(app)

JWT_SECRET = 'jwt-secret-key'

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect('test.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT,
                  email TEXT, role TEXT, api_key TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, description TEXT,
                  price REAL, category TEXT, stock INTEGER, image_url TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS posts
                 (id INTEGER PRIMARY KEY, title TEXT, content TEXT,
                  author_id INTEGER, created_at TIMESTAMP)''')

    try:
        # 사용자
        c.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin@vulnshop.com', 'admin', 'ADMIN-KEY-12345')")
        c.execute("INSERT INTO users VALUES (2, 'user1', 'password', 'user1@test.com', 'user', 'USER-KEY-67890')")

        # 상품
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

        # SQL Injection 취약점
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
    """회원가입 페이지"""
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
    """로그아웃"""
    session.clear()
    flash('로그아웃되었습니다.', 'info')
    return redirect(url_for('index'))


@app.route('/products')
def products_page():
    """상품 목록 페이지"""
    category = request.args.get('category', 'all')

    conn = sqlite3.connect('test.db')
    c = conn.cursor()

    if category == 'all':
        c.execute("SELECT * FROM products")
    else:
        c.execute(f"SELECT * FROM products WHERE category = '{category}'")  # SQL Injection

    products = c.fetchall()
    conn.close()

    return render_template('products.html', products=products, category=category)


@app.route('/product/<int:product_id>')
def product_detail(product_id):
    """상품 상세 페이지"""
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
    """장바구니 페이지"""
    return render_template('cart.html')


@app.route('/profile')
def profile_page():
    """프로필 페이지"""
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
    """관리자 페이지 (권한 체크 없음 - 취약점)"""
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
    """검색 페이지"""
    query = request.args.get('q', '')

    conn = sqlite3.connect('test.db')
    c = conn.cursor()

    # SQL Injection 취약점
    sql = f"SELECT * FROM products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%'"

    try:
        c.execute(sql)
        products = c.fetchall()
    except:
        products = []

    conn.close()

    return render_template('search.html', products=products, query=query)


# API 라우트들은 기존 app_improved.py의 API 라우트를 그대로 사용
# (여기서는 웹 페이지 라우트만 추가)

from app_improved import *  # 기존 API 라우트 import


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
