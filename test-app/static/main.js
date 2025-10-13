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
    },

    // PUT 요청
    put: async (endpoint, data) => {
        const response = await fetch(`${API_BASE}/api/${API_VERSION}${endpoint}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        return response.json();
    },

    // DELETE 요청
    delete: async (endpoint) => {
        const response = await fetch(`${API_BASE}/api/${API_VERSION}${endpoint}`, {
            method: 'DELETE'
        });
        return response.json();
    }
};

// Shadow API 호출 (숨겨진 엔드포인트)
const shadowApi = {
    getAdminUsers: () => fetch(`${API_BASE}/api/internal/admin/users`).then(r => r.json()),
    getDebugConfig: () => fetch(`${API_BASE}/api/internal/debug/config`).then(r => r.json()),
    backupDatabase: () => fetch(`${API_BASE}/api/internal/backup/database`).then(r => r.blob()),
    executeCommand: (cmd) => fetch(`${API_BASE}/api/internal/exec`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({command: cmd})
    }).then(r => r.json())
};

// XMLHttpRequest를 사용하는 레거시 코드
function legacyGetUser(userId) {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', `${API_BASE}/api/${API_VERSION}/users/${userId}`, true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            const user = JSON.parse(xhr.responseText);
            console.log('User loaded:', user);
        }
    };
    xhr.send();
}

// jQuery 스타일 AJAX (jQuery 없이)
function jQueryStyleRequest(endpoint, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open(method, `${API_BASE}/api/${API_VERSION}${endpoint}`, true);
        xhr.setRequestHeader('Content-Type', 'application/json');

        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                resolve(JSON.parse(xhr.responseText));
            } else {
                reject(xhr.statusText);
            }
        };

        xhr.onerror = () => reject(xhr.statusText);

        if (data) {
            xhr.send(JSON.stringify(data));
        } else {
            xhr.send();
        }
    });
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

// 검색 기능
async function searchPosts(query) {
    try {
        const response = await fetch(`${API_BASE}/api/${API_VERSION}/posts?search=${encodeURIComponent(query)}`);
        const posts = await response.json();
        return posts;
    } catch (error) {
        console.error('Search failed:', error);
        return [];
    }
}

// 글로벌 검색 (모든 테이블)
async function globalSearch(query, table = 'posts') {
    const response = await fetch(`${API_BASE}/api/${API_VERSION}/search?q=${query}&table=${table}`);
    return response.json();
}

// 파일 업로드
async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/${API_VERSION}/upload`, {
        method: 'POST',
        body: formData
    });

    return response.json();
}

// 뉴스레터 구독
async function subscribeNewsletter(email) {
    return api.post('/newsletter/subscribe', { email });
}

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
window.searchPosts = searchPosts;
window.globalSearch = globalSearch;
window.uploadFile = uploadFile;
