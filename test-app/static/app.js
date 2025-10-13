// 취약한 JavaScript 코드 - Shadow API Scanner 테스트용

// API 베이스 URL
const API_BASE = 'http://localhost:5000';

// 다양한 API 호출 패턴들 (Scanner가 탐지해야 함)

// 1. fetch API 사용
async function loadProducts() {
    const response = await fetch(`${API_BASE}/api/v1/products`);
    const data = await response.json();
    return data;
}

// 2. 민감한 데이터를 URL에 포함 (취약점)
function login(username, password) {
    return fetch(`${API_BASE}/api/v1/auth/login?username=${username}&password=${password}`, {
        method: 'POST'
    });
}

// 3. axios 스타일 (주석 처리된 코드지만 Scanner가 탐지해야 함)
// axios.get('/api/v1/users')
//     .then(response => console.log(response.data));

// axios.post('/api/v1/user/delete', { user_id: 123 });

// 4. XMLHttpRequest 사용
function getUserData(userId) {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', `/api/v1/user/${userId}`, true);
    xhr.onload = function() {
        if (xhr.status === 200) {
            console.log(JSON.parse(xhr.responseText));
        }
    };
    xhr.send();
}

// 5. jQuery 스타일 (주석이지만 탐지 대상)
// $.get('/api/v1/products', function(data) {
//     console.log(data);
// });

// $.ajax({
//     url: '/api/v1/secure/data',
//     method: 'GET',
//     headers: {
//         'Authorization': 'Bearer fake_token'
//     }
// });

// 6. 숨겨진 내부 API 호출 (Shadow API)
function getAdminUsers() {
    // 문서화되지 않은 내부 API
    return fetch('/api/internal/admin/users');
}

function getDebugConfig() {
    // 문서화되지 않은 디버그 엔드포인트
    return fetch('/api/internal/debug/config');
}

// 7. 검색 API (XSS 취약점)
function searchItems(query) {
    fetch(`/api/v1/search?q=${query}`)
        .then(r => r.json())
        .then(data => {
            // 취약점: innerHTML 사용
            document.getElementById('results').innerHTML = data.results;
        });
}

// 8. 파일 업로드
function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/v1/upload', {
        method: 'POST',
        body: formData
    });
}

// 9. 사용자 삭제 (CSRF 취약점)
function deleteUser(userId) {
    fetch('/api/v1/user/delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ user_id: userId })
    });
}

// 10. 템플릿 리터럴로 된 URL
const userId = 123;
fetch(`${API_BASE}/api/v1/user/${userId}`)
    .then(response => response.json());

// 11. 동적으로 생성된 엔드포인트
function getResource(resourceType, resourceId) {
    const endpoint = `/api/v1/${resourceType}/${resourceId}`;
    return fetch(endpoint);
}

// 12. Rate limiting 없는 반복 요청 (취약점 테스트)
async function spamAPI() {
    for (let i = 0; i < 100; i++) {
        await fetch('/api/v1/products');
    }
}

// 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', function() {
    console.log('App loaded');
    loadProducts();
});
