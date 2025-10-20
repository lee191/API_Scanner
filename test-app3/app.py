"""
Test Application 3 for API Scanner - Web Crawling Depth Test
이 앱은 웹 페이지 크롤링 깊이를 테스트하기 위해 설계되었습니다:
- 3단계 깊이의 HTML 페이지 구조
- 각 페이지마다 고유한 JavaScript 파일
- 각 JS 파일에 서로 다른 API 엔드포인트 포함
- 페이지 간 링크로 연결
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Mock 데이터
PRODUCTS = [
    {"id": 1, "name": "Laptop", "price": 1200},
    {"id": 2, "name": "Mouse", "price": 25},
    {"id": 3, "name": "Keyboard", "price": 75},
]

USERS = [
    {"id": 1, "username": "admin", "role": "admin"},
    {"id": 2, "username": "user1", "role": "user"},
]

ORDERS = [
    {"id": 1, "user_id": 1, "total": 1200},
    {"id": 2, "user_id": 2, "total": 100},
]

# ===========================
# HTML Pages (3 Levels Deep)
# ===========================

@app.route('/')
def home():
    """Level 0: 메인 페이지 - main.js 로드"""
    return render_template('index.html')

@app.route('/products')
def products_page():
    """Level 1: 제품 페이지 - products.js 로드"""
    return render_template('products.html')

@app.route('/users')
def users_page():
    """Level 1: 사용자 페이지 - users.js 로드"""
    return render_template('users.html')

@app.route('/admin')
def admin_page():
    """Level 2: 관리자 페이지 - admin.js 로드"""
    return render_template('admin.html')

@app.route('/reports')
def reports_page():
    """Level 2: 리포트 페이지 - reports.js 로드"""
    return render_template('reports.html')

@app.route('/dashboard')
def dashboard_page():
    """Level 3: 대시보드 페이지 - dashboard.js 로드"""
    return render_template('dashboard.html')

@app.route('/analytics')
def analytics_page():
    """Level 3: 분석 페이지 - analytics.js 로드"""
    return render_template('analytics.html')

@app.route('/settings')
def settings_page():
    """Level 3: 설정 페이지 - settings.js 로드"""
    return render_template('settings.html')

# ===========================
# API Endpoints (Level 0 - main.js)
# ===========================

@app.route('/api/health')
def health():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/api/info')
def info():
    """서버 정보"""
    return jsonify({
        "server": "Test App 3",
        "purpose": "Web Crawling Depth Test"
    }), 200

# ===========================
# API Endpoints (Level 1 - products.js)
# ===========================

@app.route('/api/products')
def get_products():
    """제품 목록"""
    return jsonify({"products": PRODUCTS}), 200

@app.route('/api/products/<int:product_id>')
def get_product(product_id):
    """특정 제품"""
    product = next((p for p in PRODUCTS if p['id'] == product_id), None)
    if product:
        return jsonify(product), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/api/products/search')
def search_products():
    """제품 검색"""
    query = request.args.get('q', '')
    results = [p for p in PRODUCTS if query.lower() in p['name'].lower()]
    return jsonify({"results": results}), 200

# ===========================
# API Endpoints (Level 1 - users.js)
# ===========================

@app.route('/api/users')
def get_users():
    """사용자 목록"""
    return jsonify({"users": USERS}), 200

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    """특정 사용자"""
    user = next((u for u in USERS if u['id'] == user_id), None)
    if user:
        return jsonify(user), 200
    return jsonify({"error": "Not found"}), 404

@app.route('/api/users/<int:user_id>/profile')
def get_user_profile(user_id):
    """사용자 프로필"""
    return jsonify({
        "user_id": user_id,
        "name": f"User {user_id}",
        "email": f"user{user_id}@test.com"
    }), 200

# ===========================
# API Endpoints (Level 2 - admin.js)
# ===========================

@app.route('/api/admin/stats')
def admin_stats():
    """관리자 통계"""
    return jsonify({
        "total_users": len(USERS),
        "total_products": len(PRODUCTS),
        "total_orders": len(ORDERS)
    }), 200

@app.route('/api/admin/users')
def admin_users():
    """관리자 - 전체 사용자"""
    return jsonify({"users": USERS, "admin": True}), 200

@app.route('/api/admin/config')
def admin_config():
    """관리자 설정"""
    return jsonify({
        "debug_mode": True,
        "maintenance": False
    }), 200

@app.route('/api/admin/logs')
def admin_logs():
    """관리자 로그"""
    return jsonify({
        "logs": [
            {"level": "info", "message": "Server started"},
            {"level": "warning", "message": "High memory usage"}
        ]
    }), 200

# ===========================
# API Endpoints (Level 2 - reports.js)
# ===========================

@app.route('/api/reports/sales')
def reports_sales():
    """판매 리포트"""
    return jsonify({
        "total_sales": 5000,
        "total_orders": len(ORDERS)
    }), 200

@app.route('/api/reports/monthly')
def reports_monthly():
    """월별 리포트"""
    return jsonify({
        "month": "October",
        "revenue": 15000,
        "orders": 50
    }), 200

@app.route('/api/reports/export')
def reports_export():
    """리포트 내보내기"""
    return jsonify({
        "format": "pdf",
        "size": "2.5MB",
        "url": "/downloads/report.pdf"
    }), 200

# ===========================
# API Endpoints (Level 3 - dashboard.js)
# ===========================

@app.route('/api/dashboard/widgets')
def dashboard_widgets():
    """대시보드 위젯"""
    return jsonify({
        "widgets": [
            {"type": "chart", "title": "Sales"},
            {"type": "table", "title": "Recent Orders"}
        ]
    }), 200

@app.route('/api/dashboard/summary')
def dashboard_summary():
    """대시보드 요약"""
    return jsonify({
        "active_users": 45,
        "total_revenue": 25000,
        "pending_orders": 5
    }), 200

@app.route('/api/dashboard/realtime')
def dashboard_realtime():
    """실시간 데이터"""
    return jsonify({
        "current_users": 12,
        "server_load": 35
    }), 200

# ===========================
# API Endpoints (Level 3 - analytics.js)
# ===========================

@app.route('/api/analytics/events')
def analytics_events():
    """분석 이벤트"""
    return jsonify({
        "events": [
            {"event": "page_view", "count": 1500},
            {"event": "click", "count": 850}
        ]
    }), 200

@app.route('/api/analytics/metrics')
def analytics_metrics():
    """분석 메트릭"""
    return jsonify({
        "bounce_rate": 45.5,
        "avg_session": "5:30",
        "conversion_rate": 3.2
    }), 200

@app.route('/api/analytics/funnel')
def analytics_funnel():
    """전환 퍼널"""
    return jsonify({
        "steps": [
            {"name": "Visit", "users": 1000},
            {"name": "Signup", "users": 500},
            {"name": "Purchase", "users": 100}
        ]
    }), 200

# ===========================
# API Endpoints (Level 3 - settings.js)
# ===========================

@app.route('/api/settings/general')
def settings_general():
    """일반 설정"""
    return jsonify({
        "site_name": "Test App 3",
        "language": "ko",
        "timezone": "Asia/Seoul"
    }), 200

@app.route('/api/settings/security')
def settings_security():
    """보안 설정"""
    return jsonify({
        "two_factor": True,
        "session_timeout": 3600,
        "password_policy": "strong"
    }), 200

@app.route('/api/settings/notifications')
def settings_notifications():
    """알림 설정"""
    return jsonify({
        "email_notifications": True,
        "push_notifications": False,
        "frequency": "daily"
    }), 200

# ===========================
# Hidden/Deep Endpoints
# ===========================

@app.route('/api/internal/debug')
def internal_debug():
    """내부 디버그 (숨겨진 엔드포인트)"""
    return jsonify({
        "debug": True,
        "memory": "512MB",
        "cpu": "45%"
    }), 200

@app.route('/api/v2/products/advanced')
def v2_products_advanced():
    """V2 고급 제품 API"""
    return jsonify({
        "version": "v2",
        "products": PRODUCTS,
        "features": ["filter", "sort", "pagination"]
    }), 200

if __name__ == '__main__':
    print("=" * 60)
    print("Test Application 3 - Web Crawling Depth Test")
    print("=" * 60)
    print("\n🌐 Page Structure (3 Levels Deep):")
    print("  Level 0: / (index.html + main.js)")
    print("  Level 1: /products, /users (+ JS files)")
    print("  Level 2: /admin, /reports (+ JS files)")
    print("  Level 3: /dashboard, /analytics, /settings (+ JS files)")
    print("\n📄 Total Pages: 8")
    print("📦 Total JS Files: 8")
    print("🔗 Total API Endpoints: ~30+")
    print("\n📊 APIs by Page:")
    print("  main.js (Level 0): 2 endpoints")
    print("  products.js (Level 1): 3 endpoints")
    print("  users.js (Level 1): 3 endpoints")
    print("  admin.js (Level 2): 4 endpoints")
    print("  reports.js (Level 2): 3 endpoints")
    print("  dashboard.js (Level 3): 3 endpoints")
    print("  analytics.js (Level 3): 3 endpoints")
    print("  settings.js (Level 3): 3 endpoints")
    print("  + Hidden: 2 endpoints")
    print("\n🎯 Crawling Test:")
    print("  Start at: http://localhost:5003/")
    print("  Crawl depth: 3 levels")
    print("  Expected JS files found: 8")
    print("  Expected API endpoints: 30+")
    print("\n🚀 Starting server on http://localhost:5003")
    print("=" * 60)
    
    app.run(debug=True, port=5003, host='0.0.0.0')
