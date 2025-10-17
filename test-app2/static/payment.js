// Payment Processing System
// 결제 관련 API 호출 및 처리

const PAYMENT_API = 'http://localhost:5002';

class PaymentProcessor {
    constructor() {
        this.paymentMethods = ['credit_card', 'paypal', 'bank_transfer'];
        this.gatewayConfig = null;
    }

    // 결제 게이트웨이 설정 로드 (Shadow API)
    async loadGatewayConfig() {
        const configUrl = `${PAYMENT_API}/api/internal/payment/gateway`;
        try {
            const response = await fetch(configUrl);
            this.gatewayConfig = await response.json();
            console.log('Gateway config loaded:', this.gatewayConfig);
            return this.gatewayConfig;
        } catch (error) {
            console.error('Failed to load gateway config:', error);
        }
    }

    // 모든 결제 정보 조회 (Shadow API - 카드 정보 포함)
    async getAllPayments() {
        const url = `${PAYMENT_API}/api/internal/payments/all`;
        try {
            const response = await fetch(url);
            const payments = await response.json();
            console.log('All payments (with sensitive data):', payments);
            return payments;
        } catch (error) {
            console.error('Failed to fetch payments:', error);
        }
    }

    // 사용자 결제 히스토리 조회 (Shadow API)
    async getUserPaymentHistory(userId) {
        const historyUrl = `/api/internal/users/${userId}/payment-history`;
        try {
            const response = await fetch(PAYMENT_API + historyUrl);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch payment history:', error);
        }
    }

    // 결제 처리 (실제로는 구현되지 않음)
    async processPayment(orderId, cardInfo) {
        console.log('Processing payment for order:', orderId);
        console.log('Card info:', cardInfo);

        // 실제 결제 처리는 백엔드에서 수행
        // 여기서는 API 호출만 시뮬레이션
        return {
            success: true,
            transaction_id: 'TXN_' + Date.now()
        };
    }

    // Stripe 연동 초기화 (Shadow API 정보 사용)
    async initializeStripe() {
        if (!this.gatewayConfig) {
            await this.loadGatewayConfig();
        }

        if (this.gatewayConfig && this.gatewayConfig.stripe) {
            const stripeKey = this.gatewayConfig.stripe.public_key;
            console.log('Initializing Stripe with key:', stripeKey);
            // 실제 Stripe 초기화 코드는 생략
        }
    }
}

// 전역 인스턴스
const paymentProcessor = new PaymentProcessor();

// 페이지 로드 시 게이트웨이 설정 로드
window.addEventListener('load', () => {
    paymentProcessor.loadGatewayConfig();
});
