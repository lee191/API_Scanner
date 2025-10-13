<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ page import="java.util.*" %>
<!DOCTYPE html>
<html>
<head>
    <title>대시보드</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script>
        const API_URL = 'http://localhost:8080/api';

        // jQuery AJAX 요청
        $(document).ready(function() {
            // 대시보드 데이터 로드
            $.ajax({
                url: API_URL + '/dashboard/stats',
                method: 'GET',
                success: function(data) {
                    $('#stats').html(JSON.stringify(data));
                }
            });

            // 사용자 프로필 업데이트
            $('#updateProfile').click(function() {
                $.post(API_URL + '/user/profile', {
                    name: $('#name').val(),
                    email: $('#email').val(),
                    role: $('#role').val()  // 취약점: role 수정 가능
                }, function(response) {
                    alert('프로필 업데이트 완료');
                });
            });
        });

        // Fetch API를 사용한 주문 조회
        async function fetchOrders() {
            try {
                const response = await fetch(API_URL + '/orders', {
                    method: 'GET',
                    headers: {
                        'Authorization': 'Bearer ' + localStorage.getItem('token')
                    }
                });
                const orders = await response.json();
                displayOrders(orders);
            } catch (error) {
                console.error('주문 조회 실패:', error);
            }
        }

        // XMLHttpRequest를 사용한 결제 처리
        function processPayment(orderId, cardNumber, cvv) {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', API_URL + '/payments/process', true);
            xhr.setRequestHeader('Content-Type', 'application/json');

            xhr.onload = function() {
                if (xhr.status === 200) {
                    alert('결제 완료');
                }
            };

            xhr.send(JSON.stringify({
                order_id: orderId,
                card_number: cardNumber,
                cvv: cvv,
                amount: 100000
            }));
        }

        // Axios 스타일 API 호출
        const axiosLike = {
            get: (url) => fetch(API_URL + url).then(r => r.json()),
            post: (url, data) => fetch(API_URL + url, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(r => r.json()),
            put: (url, data) => fetch(API_URL + url, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            }).then(r => r.json()),
            delete: (url) => fetch(API_URL + url, {method: 'DELETE'}).then(r => r.json())
        };

        // 상품 관리
        function loadProducts() {
            axiosLike.get('/products')
                .then(products => {
                    products.forEach(product => {
                        console.log('상품:', product);
                    });
                });
        }

        // 관리자 기능 (Shadow API)
        function adminFunctions() {
            // 숨겨진 사용자 관리 API
            fetch(API_URL + '/internal/admin/users/all')
                .then(r => r.json())
                .then(users => console.log('모든 사용자:', users));

            // 숨겨진 시스템 설정 API
            fetch(API_URL + '/internal/system/config')
                .then(r => r.json())
                .then(config => console.log('시스템 설정:', config));

            // 숨겨진 로그 API
            fetch(API_URL + '/internal/logs/access')
                .then(r => r.json())
                .then(logs => console.log('접근 로그:', logs));

            // 숨겨진 백업 API
            fetch(API_URL + '/internal/backup/create', {method: 'POST'})
                .then(r => r.json())
                .then(result => console.log('백업 생성:', result));
        }

        // 파일 업로드
        function uploadFile() {
            const formData = new FormData();
            formData.append('file', document.getElementById('fileInput').files[0]);

            fetch(API_URL + '/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => alert('업로드 완료: ' + data.filename));
        }
    </script>
</head>
<body>
    <h1>대시보드</h1>

    <%
        // 세션 체크 없이 민감한 정보 노출
        String username = (String) session.getAttribute("username");
        String role = (String) session.getAttribute("role");
    %>

    <div id="stats"></div>

    <h2>프로필 업데이트</h2>
    <input type="text" id="name" placeholder="이름" />
    <input type="email" id="email" placeholder="이메일" />
    <input type="text" id="role" placeholder="역할" />
    <button id="updateProfile">업데이트</button>

    <h2>파일 업로드</h2>
    <input type="file" id="fileInput" />
    <button onclick="uploadFile()">업로드</button>

    <h2>관리자 기능</h2>
    <button onclick="adminFunctions()">관리자 API 호출</button>

    <script>
        // 페이지 로드 시 실행
        fetchOrders();
        loadProducts();
    </script>
</body>
</html>
