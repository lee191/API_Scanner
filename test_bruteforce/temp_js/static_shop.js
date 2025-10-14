/**
 * 쇼핑 관련 JavaScript
 */

const SHOP_API = 'http://localhost:5000/api/v1';

// 게시글 관련
const posts = {
    // 모든 게시글 가져오기
    getAll: async () => {
        const response = await fetch(`${SHOP_API}/posts`);
        return response.json();
    },

    // 게시글 상세 조회
    get: async (postId) => {
        const response = await fetch(`${SHOP_API}/posts/${postId}`);
        return response.json();
    },

    // 게시글 작성
    create: async (title, content, authorId) => {
        const response = await fetch(`${SHOP_API}/posts`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ title, content, author_id: authorId })
        });
        return response.json();
    },

    // 게시글 검색
    search: async (query) => {
        const response = await fetch(`${SHOP_API}/posts?search=${encodeURIComponent(query)}`);
        return response.json();
    }
};

// 댓글 관련
const comments = {
    // 게시글의 댓글 가져오기
    getByPost: async (postId) => {
        const response = await fetch(`${SHOP_API}/posts/${postId}/comments`);
        return response.json();
    },

    // 댓글 작성
    create: async (postId, content, authorId) => {
        const response = await fetch(`${SHOP_API}/comments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                post_id: postId,
                content: content,
                author_id: authorId
            })
        });
        return response.json();
    }
};

// 사용자 관련
const users = {
    // 모든 사용자 조회
    getAll: async () => {
        const response = await fetch(`${SHOP_API}/users`);
        return response.json();
    },

    // 사용자 상세 조회
    get: async (userId) => {
        const response = await fetch(`${SHOP_API}/users/${userId}`);
        return response.json();
    },

    // 사용자 정보 업데이트
    update: async (userId, data) => {
        const response = await fetch(`${SHOP_API}/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    // 사용자 삭제
    delete: async (userId) => {
        const response = await fetch(`${SHOP_API}/users/${userId}`, {
            method: 'DELETE'
        });
        return response.json();
    }
};

// 결제 관련
const payments = {
    // 모든 결제 내역 조회
    getAll: async () => {
        const response = await fetch(`${SHOP_API}/payments`);
        return response.json();
    },

    // 결제 생성
    create: async (userId, cardNumber, cvv, amount) => {
        const response = await fetch(`${SHOP_API}/payments`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: userId,
                card_number: cardNumber,
                cvv: cvv,
                amount: amount
            })
        });
        return response.json();
    }
};

// 장바구니 (로컬 스토리지 사용)
const cart = {
    items: [],

    init: function() {
        const saved = localStorage.getItem('cart');
        if (saved) {
            this.items = JSON.parse(saved);
        }
    },

    add: function(item) {
        this.items.push(item);
        this.save();
    },

    remove: function(index) {
        this.items.splice(index, 1);
        this.save();
    },

    clear: function() {
        this.items = [];
        this.save();
    },

    save: function() {
        localStorage.setItem('cart', JSON.stringify(this.items));
    },

    getTotal: function() {
        return this.items.reduce((sum, item) => sum + item.price, 0);
    }
};

// 상품 데이터 (하드코딩)
const products = [
    { id: 1, name: '노트북', price: 1500000, category: 'electronics' },
    { id: 2, name: '마우스', price: 30000, category: 'electronics' },
    { id: 3, name: '키보드', price: 80000, category: 'electronics' },
    { id: 4, name: '모니터', price: 400000, category: 'electronics' },
    { id: 5, name: '헤드폰', price: 150000, category: 'electronics' }
];

// 상품 로드 함수
function loadProducts() {
    const container = document.getElementById('products');
    if (!container) return;

    products.forEach(product => {
        const div = document.createElement('div');
        div.className = 'product';
        div.innerHTML = `
            <h3>${product.name}</h3>
            <p>가격: ${product.price.toLocaleString()}원</p>
            <button onclick="cart.add(${JSON.stringify(product).replace(/"/g, '&quot;')})">
                장바구니 담기
            </button>
        `;
        container.appendChild(div);
    });
}

// 프로필 업데이트 (IDOR 취약점 활용)
async function updateProfile(userId, newData) {
    // 취약점: 다른 사용자의 정보도 수정 가능
    return users.update(userId, newData);
}

// 관리자 권한 상승 시도
async function escalateToAdmin(userId) {
    // 취약점: Mass Assignment를 통한 권한 상승
    return users.update(userId, { role: 'admin' });
}

// 초기화
cart.init();

// 페이지 로드 시 상품 로드
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadProducts);
} else {
    loadProducts();
}

// 내보내기
window.posts = posts;
window.comments = comments;
window.users = users;
window.payments = payments;
window.cart = cart;
window.products = products;
window.updateProfile = updateProfile;
window.escalateToAdmin = escalateToAdmin;
