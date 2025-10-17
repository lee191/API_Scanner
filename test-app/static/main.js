/**
 * 메인 JavaScript 파일
 * 공통 기능 및 유틸리티
 */

const API_BASE = 'http://localhost:5000';
const API_VERSION = 'v1';

// API 유틸리티 함수
const api = {
    // GET 요청
    get: async (endpoint) => {
        const response = await fetch(`${API_BASE}/api/${API_VERSION}${endpoint}`);
        return response.json();
    },

    // POST 요청
    post: async (endpoint, data) => {
        const response = await fetch(`${API_BASE}/api/${API_VERSION}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        return response.json();
    }
};

// Shadow API 호출 (숨겨진 엔드포인트)
const shadowApi = {
    // 관리자용 전체 사용자 정보 (비밀번호, API 키 포함)
    getAdminUsers: () => {
        return fetch(`${API_BASE}/api/internal/admin/users`)
            .then(r => r.json());
    },

    // 디버그 설정 정보 (민감한 설정 값 포함)
    getDebugConfig: () => {
        return fetch(`${API_BASE}/api/internal/debug/config`)
            .then(r => r.json());
    },

    // 시스템 메트릭 정보 (새로 추가)
    getMetrics: () => {
        return fetch(`${API_BASE}/api/internal/metrics`)
            .then(r => r.json());
    },

    // 로그 조회 (새로 추가)
    getLogs: (type = 'all', limit = 50) => {
        return fetch(`${API_BASE}/api/internal/logs?type=${type}&limit=${limit}`)
            .then(r => r.json());
    }
};

// XMLHttpRequest를 사용하는 레거시 코드
function legacyGetUser(userId) {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', `${API_BASE}/api/${API_VERSION}/user/${userId}`, true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            const user = JSON.parse(xhr.responseText);
            console.log('User loaded:', user);
        }
    };
    xhr.send();
}

// 로컬 스토리지 유틸리티
const storage = {
    set: (key, value) => localStorage.setItem(key, JSON.stringify(value)),
    get: (key) => {
        const item = localStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    },
    remove: (key) => localStorage.removeItem(key),
    clear: () => localStorage.clear()
};

// DOM이 로드되면 실행
document.addEventListener('DOMContentLoaded', () => {
    console.log('Main app loaded');

    // 사용자 정보 로드
    const token = storage.get('auth_token');
    if (token) {
        console.log('User is authenticated');
    }
});

// 내보내기
window.api = api;
window.shadowApi = shadowApi;
window.storage = storage;
window.legacyGetUser = legacyGetUser;
