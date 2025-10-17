// E-Commerce Checkout System
// 주문 및 체크아웃 관련 API 호출

const API_BASE = 'http://localhost:5002';

class CheckoutManager {
    constructor() {
        this.cart = [];
        this.currentOrder = null;
    }

    // 주문 생성
    async createOrder(userId, totalAmount, shippingAddress) {
        const orderData = {
            user_id: userId,
            total_amount: totalAmount,
            shipping_address: shippingAddress
        };

        try {
            const response = await fetch(`${API_BASE}/api/v2/orders`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(orderData)
            });
            const data = await response.json();
            this.currentOrder = data;
            return data;
        } catch (error) {
            console.error('Order creation failed:', error);
        }
    }

    // 주문 목록 조회
    async getOrders(userId) {
        try {
            const response = await fetch(`${API_BASE}/api/v2/orders?user_id=${userId}`);
            const orders = await response.json();
            return orders;
        } catch (error) {
            console.error('Failed to fetch orders:', error);
        }
    }

    // 주문 상세 조회
    async getOrderDetail(orderId) {
        try {
            const response = await fetch(`${API_BASE}/api/v2/orders/${orderId}`);
            const order = await response.json();
            return order;
        } catch (error) {
            console.error('Failed to fetch order details:', error);
        }
    }

    // 숨겨진 관리자 API 호출 (Shadow API)
    async fetchAdminOrders() {
        // 이 엔드포인트는 문서화되지 않았지만 JS에 하드코딩되어 있음
        const url = `${API_BASE}/api/internal/admin/orders`;
        try {
            const response = await fetch(url);
            return await response.json();
        } catch (error) {
            console.error('Admin API failed:', error);
        }
    }

    // 배송 추적 (Shadow API - 하드코딩된 내부 엔드포인트)
    async getShippingConfig() {
        const endpoint = '/api/internal/shipping/config';
        try {
            const response = await fetch(API_BASE + endpoint);
            return await response.json();
        } catch (error) {
            console.error('Shipping config fetch failed:', error);
        }
    }
}

// 전역 인스턴스
const checkoutManager = new CheckoutManager();

// 전역 함수들 (index.html에서 호출)
async function loadOrders() {
    const orders = await checkoutManager.getOrders(1);
    const container = document.getElementById('orders-container');

    if (!orders || orders.length === 0) {
        container.innerHTML = '<p>No orders found.</p>';
        return;
    }

    container.innerHTML = orders.map(order => `
        <div class="order-item">
            <strong>Order #${order.id}</strong>
            <span class="status ${order.status}">${order.status}</span>
            <p>Amount: $${order.total_amount}</p>
            <p>Address: ${order.shipping_address}</p>
            <p>Date: ${order.created_at}</p>
            <button class="btn" onclick="viewOrderDetail(${order.id})">View Details</button>
        </div>
    `).join('');
}

async function viewOrderDetail(orderId) {
    const order = await checkoutManager.getOrderDetail(orderId);
    if (order) {
        alert(`Order Details:\n\nOrder ID: ${order.id}\nAmount: $${order.total_amount}\nStatus: ${order.status}\nAddress: ${order.shipping_address}\nTracking: ${order.tracking_number}\nDate: ${order.created_at}`);
    }
}

async function createOrder() {
    const amount = document.getElementById('order-amount').value;
    const address = document.getElementById('order-address').value;
    const messageDiv = document.getElementById('order-message');

    if (!amount || !address) {
        messageDiv.innerHTML = '<div class="error">Please fill all fields</div>';
        return;
    }

    const result = await checkoutManager.createOrder(1, parseFloat(amount), address);

    if (result && result.success) {
        messageDiv.innerHTML = `<div class="success">Order created! Order ID: ${result.order_id}</div>`;
        document.getElementById('order-amount').value = '';
        document.getElementById('order-address').value = '';
        setTimeout(loadOrders, 1000);
    } else {
        messageDiv.innerHTML = `<div class="error">${result?.error || 'Failed to create order'}</div>`;
    }
}

// DOM이 로드되면 주문 목록 가져오기
document.addEventListener('DOMContentLoaded', () => {
    console.log('Checkout.js loaded');
});
