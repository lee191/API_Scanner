"""
E-Commerce 취약한 테스트 웹 애플리케이션
Shadow API Scanner 테스트용 - 의도적으로 취약점이 포함되어 있음
경고: 절대 프로덕션 환경에서 사용하지 마세요!
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime

app = Flask(__name__)

# CORS 설정
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# 인메모리 데이터베이스
def init_db():
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()

    # 주문 테이블
    cursor.execute('''
        CREATE TABLE orders (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            total_amount REAL,
            status TEXT,
            created_at TEXT,
            shipping_address TEXT
        )
    ''')

    # 결제 테이블
    cursor.execute('''
        CREATE TABLE payments (
            id INTEGER PRIMARY KEY,
            order_id INTEGER,
            card_number TEXT,
            cvv TEXT,
            amount REAL,
            status TEXT
        )
    ''')

    # 리뷰 테이블
    cursor.execute('''
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY,
            product_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT,
            created_at TEXT
        )
    ''')

    # 쿠폰 테이블
    cursor.execute('''
        CREATE TABLE coupons (
            id INTEGER PRIMARY KEY,
            code TEXT,
            discount_percent INTEGER,
            is_active BOOLEAN,
            max_uses INTEGER
        )
    ''')

    # 샘플 데이터
    cursor.execute("INSERT INTO orders VALUES (1, 1, 1299.98, 'delivered', '2025-01-10 10:30:00', '123 Main St, Seoul')")
    cursor.execute("INSERT INTO orders VALUES (2, 2, 399.99, 'processing', '2025-01-15 14:20:00', '456 Oak Ave, Busan')")
    cursor.execute("INSERT INTO orders VALUES (3, 1, 89.97, 'shipped', '2025-01-14 09:15:00', '789 Pine Rd, Incheon')")

    cursor.execute("INSERT INTO payments VALUES (1, 1, '4532-1234-5678-9012', '123', 1299.98, 'completed')")
    cursor.execute("INSERT INTO payments VALUES (2, 2, '5412-3456-7890-1234', '456', 399.99, 'pending')")

    cursor.execute("INSERT INTO reviews VALUES (1, 1, 1, 5, 'Excellent product!', '2025-01-11 10:30:00')")
    cursor.execute("INSERT INTO reviews VALUES (2, 1, 2, 4, 'Good quality', '2025-01-12 15:45:00')")
    cursor.execute("INSERT INTO reviews VALUES (3, 2, 1, 3, 'Average performance', '2025-01-13 11:20:00')")

    cursor.execute("INSERT INTO coupons VALUES (1, 'SAVE20', 20, 1, 100)")
    cursor.execute("INSERT INTO coupons VALUES (2, 'WELCOME10', 10, 1, 500)")
    cursor.execute("INSERT INTO coupons VALUES (3, 'SECRET50', 50, 1, 10)")

    conn.commit()
    return conn

db_conn = init_db()


# 메인 페이지
@app.route('/')
def index():
    return render_template('index.html')


# ========== Public API ==========

# Public API: 주문 목록 조회
@app.route('/api/v2/orders', methods=['GET'])
def get_orders():
    user_id = request.args.get('user_id', '1')
    cursor = db_conn.cursor()
    # 의도적인 SQL Injection 취약점
    query = f"SELECT * FROM orders WHERE user_id = {user_id}"
    try:
        cursor.execute(query)
        orders = [{'id': row[0], 'user_id': row[1], 'total_amount': row[2],
                   'status': row[3], 'created_at': row[4], 'shipping_address': row[5]}
                  for row in cursor.fetchall()]
        return jsonify(orders)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Public API: 주문 상세 조회
@app.route('/api/v2/orders/<order_id>', methods=['GET'])
def get_order_detail(order_id):
    cursor = db_conn.cursor()
    query = f"SELECT * FROM orders WHERE id = {order_id}"
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            return jsonify({
                'id': row[0],
                'user_id': row[1],
                'total_amount': row[2],
                'status': row[3],
                'created_at': row[4],
                'shipping_address': row[5],
                'tracking_number': 'TR' + str(row[0]).zfill(10)
            })
        return jsonify({'error': 'Order not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Public API: 주문 생성
@app.route('/api/v2/orders', methods=['POST'])
def create_order():
    data = request.get_json() or {}
    user_id = data.get('user_id', 1)
    total_amount = data.get('total_amount', 0)
    shipping_address = data.get('shipping_address', '')

    cursor = db_conn.cursor()
    try:
        # 입력 검증 없음 (취약점)
        query = f"INSERT INTO orders (user_id, total_amount, status, created_at, shipping_address) VALUES ({user_id}, {total_amount}, 'pending', datetime('now'), '{shipping_address}')"
        cursor.execute(query)
        db_conn.commit()

        return jsonify({
            'success': True,
            'order_id': cursor.lastrowid,
            'message': 'Order created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Public API: 리뷰 목록 조회
@app.route('/api/v2/reviews', methods=['GET'])
def get_reviews():
    product_id = request.args.get('product_id')
    cursor = db_conn.cursor()

    if product_id:
        query = f"SELECT * FROM reviews WHERE product_id = {product_id}"
    else:
        query = "SELECT * FROM reviews"

    try:
        cursor.execute(query)
        reviews = [{'id': row[0], 'product_id': row[1], 'user_id': row[2],
                   'rating': row[3], 'comment': row[4], 'created_at': row[5]}
                  for row in cursor.fetchall()]
        return jsonify(reviews)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Public API: 리뷰 작성
@app.route('/api/v2/reviews', methods=['POST'])
def create_review():
    data = request.get_json() or {}
    product_id = data.get('product_id', 1)
    user_id = data.get('user_id', 1)
    rating = data.get('rating', 5)
    comment = data.get('comment', '')

    cursor = db_conn.cursor()
    try:
        # XSS 취약점: comment 입력 검증 없음
        query = f"INSERT INTO reviews (product_id, user_id, rating, comment, created_at) VALUES ({product_id}, {user_id}, {rating}, '{comment}', datetime('now'))"
        cursor.execute(query)
        db_conn.commit()

        return jsonify({
            'success': True,
            'review_id': cursor.lastrowid,
            'message': 'Review posted successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Public API: 쿠폰 검증
@app.route('/api/v2/coupons/validate', methods=['POST'])
def validate_coupon():
    data = request.get_json() or {}
    code = data.get('code', '')

    cursor = db_conn.cursor()
    query = f"SELECT * FROM coupons WHERE code = '{code}' AND is_active = 1"

    try:
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            return jsonify({
                'valid': True,
                'code': row[1],
                'discount_percent': row[2],
                'max_uses': row[4]
            })
        return jsonify({'valid': False, 'message': 'Invalid coupon code'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========== Shadow API ==========

# Shadow API: 모든 결제 정보 조회 (카드 정보 포함)
@app.route('/api/internal/payments/all', methods=['GET'])
def get_all_payments():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM payments")
    payments = [{'id': row[0], 'order_id': row[1], 'card_number': row[2],
                'cvv': row[3], 'amount': row[4], 'status': row[5]}
               for row in cursor.fetchall()]
    return jsonify(payments)


# Shadow API: 관리자용 주문 관리
@app.route('/api/internal/admin/orders', methods=['GET'])
def admin_get_orders():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM orders")
    orders = [{'id': row[0], 'user_id': row[1], 'total_amount': row[2],
              'status': row[3], 'created_at': row[4], 'shipping_address': row[5]}
             for row in cursor.fetchall()]
    return jsonify(orders)


# Shadow API: 모든 쿠폰 조회 (비활성 쿠폰 포함)
@app.route('/api/internal/coupons/all', methods=['GET'])
def get_all_coupons():
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM coupons")
    coupons = [{'id': row[0], 'code': row[1], 'discount_percent': row[2],
               'is_active': bool(row[3]), 'max_uses': row[4]}
              for row in cursor.fetchall()]
    return jsonify(coupons)


# Shadow API: 쿠폰 생성 (관리자 전용)
@app.route('/api/internal/admin/coupons', methods=['POST'])
def admin_create_coupon():
    data = request.get_json() or {}
    code = data.get('code', '')
    discount = data.get('discount_percent', 0)
    max_uses = data.get('max_uses', 100)

    cursor = db_conn.cursor()
    try:
        query = f"INSERT INTO coupons (code, discount_percent, is_active, max_uses) VALUES ('{code}', {discount}, 1, {max_uses})"
        cursor.execute(query)
        db_conn.commit()

        return jsonify({
            'success': True,
            'coupon_id': cursor.lastrowid,
            'message': 'Coupon created successfully'
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Shadow API: 배송 추적 시스템 정보
@app.route('/api/internal/shipping/config', methods=['GET'])
def shipping_config():
    return jsonify({
        'carriers': {
            'dhl': {
                'api_key': 'DHL_API_KEY_123456789',
                'api_endpoint': 'https://api.dhl.com/tracking',
                'username': 'dhl_admin',
                'password': 'dhl_pass_2025'
            },
            'fedex': {
                'api_key': 'FEDEX_KEY_ABCDEF123',
                'api_endpoint': 'https://api.fedex.com/track',
                'account_number': '123456789'
            },
            'ups': {
                'api_key': 'UPS_API_987654321',
                'api_endpoint': 'https://onlinetools.ups.com/track',
                'license_number': 'UPS_LICENSE_XYZ'
            }
        },
        'warehouse_locations': [
            {'id': 1, 'address': '100 Warehouse Blvd, Seoul', 'coordinates': '37.5665,126.9780'},
            {'id': 2, 'address': '200 Storage Ave, Busan', 'coordinates': '35.1796,129.0756'}
        ],
        'internal_notes': 'Do not expose carrier API keys to public'
    })


# Shadow API: 결제 게이트웨이 설정
@app.route('/api/internal/payment/gateway', methods=['GET'])
def payment_gateway():
    return jsonify({
        'stripe': {
            'public_key': 'pk_live_51234567890abcdef',
            'secret_key': 'sk_live_9876543210zyxwvu',
            'webhook_secret': 'whsec_abc123def456',
            'api_version': '2023-10-16'
        },
        'paypal': {
            'client_id': 'AaBbCcDdEeFfGgHhIiJjKkLlMm',
            'client_secret': 'paypal_secret_NnOoPpQqRrSsTt',
            'webhook_id': 'WH-1A2B3C4D5E6F7G8H',
            'environment': 'production'
        },
        'fraud_detection': {
            'enabled': True,
            'max_daily_amount': 10000,
            'blocked_countries': ['XX', 'YY'],
            'risk_score_threshold': 75
        },
        'database_connection': 'postgresql://payment_user:pay_db_pass@10.0.2.100:5432/payments_db'
    })


# Shadow API: 사용자 결제 히스토리 (민감 정보 포함)
@app.route('/api/internal/users/<user_id>/payment-history', methods=['GET'])
def user_payment_history(user_id):
    cursor = db_conn.cursor()

    # 주문과 결제 정보를 조인
    query = f"""
        SELECT o.id, o.total_amount, o.created_at, p.card_number, p.cvv, p.status
        FROM orders o
        LEFT JOIN payments p ON o.id = p.order_id
        WHERE o.user_id = {user_id}
    """

    try:
        cursor.execute(query)
        history = []
        for row in cursor.fetchall():
            history.append({
                'order_id': row[0],
                'amount': row[1],
                'date': row[2],
                'card_number': row[3],
                'cvv': row[4],  # 취약점: CVV 노출
                'status': row[5]
            })

        return jsonify({
            'user_id': user_id,
            'total_orders': len(history),
            'payment_history': history
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Shadow API: 내부 통계 및 리포트
@app.route('/api/internal/reports/sales', methods=['GET'])
def sales_report():
    cursor = db_conn.cursor()

    cursor.execute("SELECT SUM(total_amount) FROM orders")
    total_revenue = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(total_amount) FROM orders")
    avg_order_value = cursor.fetchone()[0] or 0

    return jsonify({
        'period': '2025-01-01 to 2025-01-31',
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'average_order_value': avg_order_value,
        'top_customers': [
            {'user_id': 1, 'total_spent': 1389.95, 'email': 'customer1@email.com'},
            {'user_id': 2, 'total_spent': 399.99, 'email': 'customer2@email.com'}
        ],
        'payment_methods': {
            'credit_card': 85,
            'paypal': 12,
            'bank_transfer': 3
        },
        'database_query_stats': {
            'slowest_queries': [
                {'query': 'SELECT * FROM orders WHERE status = "processing"', 'time_ms': 234},
                {'query': 'SELECT * FROM payments', 'time_ms': 189}
            ]
        }
    })


if __name__ == '__main__':
    print("=" * 60)
    print("[WARNING] E-Commerce Vulnerable Test Application Starting")
    print("[WARNING] This app contains intentional vulnerabilities")
    print("[WARNING] Never use in production!")
    print("[WARNING] Running on port 5002")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5002, debug=True)
