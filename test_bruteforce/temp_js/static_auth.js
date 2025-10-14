/**
 * 인증 관련 JavaScript
 */

const AUTH_API = 'http://localhost:5000/api/v1/auth';

// 로그인
async function login(username, password) {
    try {
        const response = await fetch(`${AUTH_API}/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.success) {
            // 토큰 저장
            localStorage.setItem('auth_token', data.token);
            localStorage.setItem('user', JSON.stringify(data.user));

            console.log('Login successful:', data.user);
            return data;
        } else {
            console.error('Login failed:', data.message);
            return null;
        }
    } catch (error) {
        console.error('Login error:', error);
        return null;
    }
}

// 회원가입
async function register(username, password, email) {
    const response = await fetch(`${AUTH_API}/register`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password, email })
    });

    return response.json();
}

// 비밀번호 리셋
async function resetPassword(userId, newPassword) {
    // 취약점: userId를 직접 전달
    const response = await fetch(`${AUTH_API}/reset-password`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_id: userId,
            new_password: newPassword
        })
    });

    return response.json();
}

// 로그아웃
function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
    window.location.href = '/';
}

// 현재 사용자 확인
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// 인증 토큰 가져오기
function getAuthToken() {
    return localStorage.getItem('auth_token');
}

// 인증된 요청
async function authenticatedRequest(url, options = {}) {
    const token = getAuthToken();

    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };

    return fetch(url, {
        ...options,
        headers
    });
}

// Axios 스타일 인터셉터
const authAxios = {
    get: async (url) => {
        return authenticatedRequest(url, { method: 'GET' });
    },
    post: async (url, data) => {
        return authenticatedRequest(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },
    put: async (url, data) => {
        return authenticatedRequest(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },
    delete: async (url) => {
        return authenticatedRequest(url, { method: 'DELETE' });
    }
};

// 자동 로그인 (개발용)
if (document.location.search.includes('auto_login=true')) {
    login('admin', 'admin123').then(data => {
        console.log('Auto login completed:', data);
    });
}

// 내보내기
window.auth = {
    login,
    register,
    resetPassword,
    logout,
    getCurrentUser,
    getAuthToken
};

window.authAxios = authAxios;
