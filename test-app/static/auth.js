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
            localStorage.setItem('api_key', data.api_key);

            console.log('Login successful');
            console.log('Token:', data.token);
            console.log('API Key:', data.api_key);

            return data;
        } else {
            console.error('Login failed');
            return null;
        }
    } catch (error) {
        console.error('Login error:', error);
        return null;
    }
}

// 로그아웃
function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('api_key');
    window.location.href = '/';
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

// 자동 로그인 (개발용)
if (document.location.search.includes('auto_login=true')) {
    login('admin', 'admin123').then(data => {
        console.log('Auto login completed:', data);
    });
}

// 내보내기
window.auth = {
    login,
    logout,
    getAuthToken,
    authenticatedRequest
};
