// E-Commerce Shop Features
// 리뷰, 쿠폰, 판매 리포트 관련 기능

const SHOP_API = 'http://localhost:5002';

class ShopManager {
    constructor() {
        this.reviews = [];
        this.coupons = [];
    }

    // 리뷰 목록 조회
    async getReviews(productId = null) {
        let url = `${SHOP_API}/api/v2/reviews`;
        if (productId) {
            url += `?product_id=${productId}`;
        }

        try {
            const response = await fetch(url);
            this.reviews = await response.json();
            return this.reviews;
        } catch (error) {
            console.error('Failed to fetch reviews:', error);
        }
    }

    // 리뷰 작성
    async postReview(productId, userId, rating, comment) {
        const reviewData = {
            product_id: productId,
            user_id: userId,
            rating: rating,
            comment: comment
        };

        try {
            const response = await fetch(`${SHOP_API}/api/v2/reviews`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(reviewData)
            });
            return await response.json();
        } catch (error) {
            console.error('Failed to post review:', error);
        }
    }

    // 쿠폰 검증
    async validateCoupon(couponCode) {
        try {
            const response = await fetch(`${SHOP_API}/api/v2/coupons/validate`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ code: couponCode })
            });
            return await response.json();
        } catch (error) {
            console.error('Coupon validation failed:', error);
        }
    }

    // 모든 쿠폰 조회 (Shadow API - 비활성 쿠폰 포함)
    async getAllCoupons() {
        const url = `${SHOP_API}/api/internal/coupons/all`;
        try {
            const response = await fetch(url);
            this.coupons = await response.json();
            console.log('All coupons (including inactive):', this.coupons);
            return this.coupons;
        } catch (error) {
            console.error('Failed to fetch all coupons:', error);
        }
    }

    // 관리자 쿠폰 생성 (Shadow API)
    async createAdminCoupon(code, discountPercent, maxUses) {
        const couponData = {
            code: code,
            discount_percent: discountPercent,
            max_uses: maxUses
        };

        const adminUrl = `${SHOP_API}/api/internal/admin/coupons`;
        try {
            const response = await fetch(adminUrl, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(couponData)
            });
            return await response.json();
        } catch (error) {
            console.error('Admin coupon creation failed:', error);
        }
    }

    // 판매 리포트 조회 (Shadow API)
    async getSalesReport() {
        const reportUrl = `${SHOP_API}/api/internal/reports/sales`;
        try {
            const response = await fetch(reportUrl);
            const report = await response.json();
            console.log('Sales report:', report);
            return report;
        } catch (error) {
            console.error('Failed to fetch sales report:', error);
        }
    }

    // 특별 할인 쿠폰 자동 적용 (하드코딩된 시크릿 쿠폰)
    async applySecretCoupon() {
        // 코드에 하드코딩된 시크릿 쿠폰
        const secretCoupons = ['SECRET50', 'HIDDEN30', 'ADMIN100'];

        for (const code of secretCoupons) {
            const result = await this.validateCoupon(code);
            if (result.valid) {
                console.log('Secret coupon applied:', code);
                return result;
            }
        }
        return null;
    }
}

// 전역 인스턴스
const shopManager = new ShopManager();

// 전역 함수들 (index.html에서 호출)
async function loadReviews(productId = null) {
    const reviews = await shopManager.getReviews(productId);
    const container = document.getElementById('reviews-container');

    if (!reviews || reviews.length === 0) {
        container.innerHTML = '<p>No reviews yet.</p>';
        return;
    }

    container.innerHTML = reviews.map(review => `
        <div class="review-item">
            <div>
                <strong>Product #${review.product_id}</strong>
                <span class="rating">${'★'.repeat(review.rating)}${'☆'.repeat(5 - review.rating)}</span>
            </div>
            <p>${review.comment}</p>
            <small>By User #${review.user_id} on ${review.created_at}</small>
        </div>
    `).join('');
}

async function submitReview() {
    const productId = document.getElementById('review-product-id').value;
    const rating = document.getElementById('review-rating').value;
    const comment = document.getElementById('review-comment').value;
    const messageDiv = document.getElementById('review-message');

    if (!productId || !rating || !comment) {
        messageDiv.innerHTML = '<div class="error">Please fill all fields</div>';
        return;
    }

    const result = await shopManager.postReview(
        parseInt(productId),
        1,
        parseInt(rating),
        comment
    );

    if (result && result.success) {
        messageDiv.innerHTML = '<div class="success">Review submitted successfully!</div>';
        document.getElementById('review-product-id').value = '';
        document.getElementById('review-rating').value = '';
        document.getElementById('review-comment').value = '';
        setTimeout(loadReviews, 1000);
    } else {
        messageDiv.innerHTML = `<div class="error">${result?.error || 'Failed to submit review'}</div>`;
    }
}

async function validateCoupon() {
    const code = document.getElementById('coupon-code').value;
    const resultDiv = document.getElementById('coupon-result');

    if (!code) {
        resultDiv.innerHTML = '<div class="error">Please enter a coupon code</div>';
        return;
    }

    const result = await shopManager.validateCoupon(code);

    if (result && result.valid) {
        resultDiv.innerHTML = `
            <div class="success">
                ✅ Valid Coupon!<br>
                Code: ${result.code}<br>
                Discount: ${result.discount_percent}%<br>
                Max Uses: ${result.max_uses}
            </div>
        `;
    } else {
        resultDiv.innerHTML = `<div class="error">❌ ${result?.message || 'Invalid coupon code'}</div>`;
    }
}

// 페이지 로드 시 데이터 가져오기
document.addEventListener('DOMContentLoaded', async () => {
    console.log('Shop.js loaded');

    // 숨겨진 쿠폰 정보 가져오기 (Shadow API)
    await shopManager.getAllCoupons();

    // 판매 리포트 가져오기 (Shadow API)
    await shopManager.getSalesReport();
});

// 제품 페이지에서 자동으로 시크릿 쿠폰 확인
if (window.location.pathname.includes('/product')) {
    shopManager.applySecretCoupon();
}
