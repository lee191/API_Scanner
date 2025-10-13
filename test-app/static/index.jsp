<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ page import="java.sql.*" %>
<%@ page import="javax.servlet.http.*" %>
<!DOCTYPE html>
<html>
<head>
    <title>취약한 JSP 애플리케이션</title>
    <script>
        // API 엔드포인트 정의
        const API_BASE_URL = 'http://localhost:8080';
        const API_ENDPOINTS = {
            login: API_BASE_URL + '/api/auth/login',
            register: API_BASE_URL + '/api/auth/register',
            users: API_BASE_URL + '/api/users',
            products: API_BASE_URL + '/api/products',
            orders: API_BASE_URL + '/api/orders',
            admin: API_BASE_URL + '/api/admin'
        };

        // 로그인 함수
        function login(username, password) {
            fetch(API_ENDPOINTS.login, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username: username,
                    password: password
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    localStorage.setItem('token', data.token);
                    window.location.href = '/dashboard.jsp';
                }
            });
        }

        // 사용자 목록 조회
        function fetchUsers() {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', API_ENDPOINTS.users, true);
            xhr.onload = function() {
                if (xhr.status === 200) {
                    const users = JSON.parse(xhr.responseText);
                    displayUsers(users);
                }
            };
            xhr.send();
        }

        // Shadow API 호출
        function accessInternalAPI() {
            // 숨겨진 관리자 API
            fetch(API_BASE_URL + '/api/internal/admin/system-config')
                .then(r => r.json())
                .then(data => console.log('System config:', data));

            // 숨겨진 데이터베이스 API
            fetch(API_BASE_URL + '/api/internal/db/dump')
                .then(r => r.blob())
                .then(blob => console.log('Database dump:', blob));
        }
    </script>
</head>
<body>
    <h1>JSP 취약한 애플리케이션</h1>

    <%
        // SQL Injection 취약점
        String userId = request.getParameter("id");
        if (userId != null) {
            String query = "SELECT * FROM users WHERE id = " + userId;
            // Connection conn = DriverManager.getConnection(...);
            // Statement stmt = conn.createStatement();
            // ResultSet rs = stmt.executeQuery(query);
        }

        // XSS 취약점
        String userInput = request.getParameter("search");
        if (userInput != null) {
            out.println("<p>검색 결과: " + userInput + "</p>");
        }
    %>

    <form action="login.jsp" method="post">
        <input type="text" name="username" placeholder="사용자명" />
        <input type="password" name="password" placeholder="비밀번호" />
        <button type="submit">로그인</button>
    </form>
</body>
</html>
