# Test-App2: E-Commerce 취약한 테스트 애플리케이션

Shadow API Scanner 테스트용 E-Commerce 애플리케이션입니다.

## ⚠️ 경고
이 애플리케이션은 의도적으로 보안 취약점을 포함하고 있습니다.
**절대 프로덕션 환경에서 사용하지 마세요!**

## 특징

### 도메인: E-Commerce (주문, 결제, 리뷰, 쿠폰 시스템)

**Public APIs (7개)**
- `GET /api/v2/orders` - 주문 목록 조회
- `GET /api/v2/orders/<order_id>` - 주문 상세 조회
- `POST /api/v2/orders` - 주문 생성
- `GET /api/v2/reviews` - 리뷰 목록 조회
- `POST /api/v2/reviews` - 리뷰 작성
- `POST /api/v2/coupons/validate` - 쿠폰 검증
- `GET /` - 메인 페이지

**Shadow APIs (8개)**
- `GET /api/internal/payments/all` - 모든 결제 정보 (카드번호, CVV 포함) ⚠️ Critical
- `GET /api/internal/admin/orders` - 관리자용 주문 관리 ⚠️ High
- `GET /api/internal/coupons/all` - 모든 쿠폰 조회 (비활성 포함)
- `POST /api/internal/admin/coupons` - 쿠폰 생성 ⚠️ High
- `GET /api/internal/shipping/config` - 배송 API 키 노출 ⚠️ Critical
- `GET /api/internal/payment/gateway` - 결제 게이트웨이 설정 (Stripe, PayPal 키) ⚠️ Critical
- `GET /api/internal/users/<user_id>/payment-history` - 사용자 결제 히스토리 (CVV 포함) ⚠️ Critical
- `GET /api/internal/reports/sales` - 내부 통계 및 리포트

### 취약점
- SQL Injection
- 민감한 정보 노출 (카드번호, CVV, API 키)
- 인증/권한 없는 관리자 API 접근
- XSS 취약점
- 에러 메시지를 통한 정보 노출

## 실행 방법

### Docker Compose로 실행
```bash
cd test-app2
docker-compose up --build
```

### Docker 직접 실행
```bash
cd test-app2
docker build -t test-app2 .
docker run -p 5002:5002 test-app2
```

### Python으로 직접 실행
```bash
cd test-app2
pip install -r requirements.txt
python app.py
```

## 접속
- URL: http://localhost:5002
- Port: 5002 (test-app의 5000, test-app의 5001과 구분)

## Shadow API Scanner로 테스트

### CLI로 스캔
```bash
# 정적 분석만
python main.py full-scan http://localhost:5001 --js-path test-app2/static --static-only

# AI 분석만
python main.py full-scan http://localhost:5001 --js-path test-app2/static --ai-only

# 정적 + AI 분석
python main.py full-scan http://localhost:5001 --js-path test-app2/static --ai
```

### 웹 UI로 스캔
1. API 서버 및 웹 UI 실행
2. http://localhost:3000 접속
3. Target URL: http://localhost:5001
4. JS Path: test-app2/static
5. 분석 모드 선택 (정적/AI/정적+AI)
6. 스캔 시작

## Ground Truth 비교
```bash
python scripts/compare_ai_accuracy.py \
  --target http://localhost:5001 \
  --ground-truth test-app2/ground_truth.json \
  --js-path test-app2/static
```

## 파일 구조
```
test-app2/
├── app.py                 # Flask 애플리케이션
├── requirements.txt       # Python 의존성
├── Dockerfile            # Docker 설정
├── docker-compose.yml    # Docker Compose 설정
├── ground_truth.json     # 정답 엔드포인트 목록
├── static/               # JavaScript 파일
│   ├── checkout.js       # 주문 관련 API 호출
│   ├── payment.js        # 결제 관련 API 호출
│   └── shop.js           # 리뷰, 쿠폰 관련 API 호출
└── templates/            # HTML 템플릿 (없음, render_template_string 사용)
```

## test-app과의 차이점

| 항목 | test-app | test-app2 |
|------|----------|-----------|
| 도메인 | 일반 제품/사용자 관리 | E-Commerce (주문/결제) |
| 포트 | 5000 | 5001 |
| API 버전 | /api/v1/* | /api/v2/* |
| 엔드포인트 수 | 12개 | 15개 |
| 데이터베이스 | users, products | orders, payments, reviews, coupons |
| JavaScript 파일 | main.js, auth.js, app.js | checkout.js, payment.js, shop.js |
| 주요 Shadow API | admin/users, debug/config | payments/all, payment/gateway |
