// 취약한 JavaScript 코드 - Shadow API Scanner 테스트용

// API 베이스 URL
const API_BASE = 'http://localhost:5000';

// 다양한 API 호출 패턴들 (Scanner가 탐지해야 함)

// 1. fetch API - 제품 목록
async function loadProducts() {
    const response = await fetch(`${API_BASE}/api/v1/products`);
    const data = await response.json();
    console.log('Products:', data);
    return data;
}

// 2. 사용자 목록 조회
function getAllUsers() {
    return fetch(`${API_BASE}/api/v1/users`)
        .then(response => response.json());
}

// 3. XMLHttpRequest - 사용자 상세 조회 (SQL Injection 취약점)
function getUserData(userId) {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', `/api/v1/user/${userId}`, true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            console.log('User:', JSON.parse(xhr.responseText));
        }
    };
    xhr.send();
}

// 4. 템플릿 리터럴로 된 동적 URL
const userId = 123;
fetch(`${API_BASE}/api/v1/user/${userId}`)
    .then(response => response.json())
    .then(user => console.log('User detail:', user));

// 5. 로그인 API
async function login(username, password) {
    const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (data.success) {
        console.log('Login successful:', data);
        localStorage.setItem('auth_token', data.token);
        return data;
    }

    return null;
}

// 6. Shadow API - 관리자용 사용자 목록 (숨겨진 엔드포인트)
function getAdminUsers() {
    // 문서화되지 않은 내부 API
    return fetch('/api/internal/admin/users')
        .then(r => r.json())
        .then(users => {
            console.log('Admin users with passwords:', users);
            return users;
        });
}

// 7. Shadow API - 디버그 설정 (숨겨진 엔드포인트)
function getDebugConfig() {
    // 문서화되지 않은 디버그 엔드포인트
    return fetch('/api/internal/debug/config')
        .then(r => r.json())
        .then(config => {
            console.log('Debug config with secrets:', config);
            return config;
        });
}

// 8. 변수로 구성된 동적 URL
function getResource(resourceType, resourceId) {
    const endpoint = `/api/v1/${resourceType}/${resourceId}`;
    return fetch(endpoint).then(r => r.json());
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    console.log('App loaded');

    // 제품 목록 로드
    loadProducts().then(products => {
        const productsDiv = document.getElementById('products');
        if (productsDiv && products) {
            productsDiv.innerHTML = '<h2>Products:</h2>' +
                JSON.stringify(products, null, 2);
        }
    });

    // 사용자 목록 로드
    getAllUsers().then(users => {
        console.log('All users:', users);
    });
});

// ========== 새로 추가된 함수들 (5개 엔드포인트용) ==========

// 9. 제품 상세 조회
function getProductDetail(productId) {
    return fetch(`${API_BASE}/api/v1/products/${productId}`)
        .then(r => r.json())
        .then(product => {
            console.log('Product detail:', product);
            return product;
        });
}

// 10. 제품 생성
async function createProduct(name, price, description) {
    const response = await fetch(`${API_BASE}/api/v1/products`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, price, description })
    });

    const data = await response.json();
    console.log('Product created:', data);
    return data;
}

// 11. 사용자 프로필 조회
function getUserProfile(userId) {
    return fetch(`${API_BASE}/api/v1/user/${userId}/profile`)
        .then(r => r.json())
        .then(profile => {
            console.log('User profile:', profile);
            return profile;
        });
}

// 전역으로 내보내기
window.app = {
    loadProducts,
    getAllUsers,
    getUserData,
    login,
    getAdminUsers,
    getDebugConfig,
    getResource,
    // 새로 추가된 함수들
    getProductDetail,
    createProduct,
    getUserProfile
};
