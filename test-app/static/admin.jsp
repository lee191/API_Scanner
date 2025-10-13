<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ page import="java.sql.*" %>
<%@ page import="java.io.*" %>
<!DOCTYPE html>
<html>
<head>
    <title>관리자 페이지</title>
    <script>
        const ADMIN_API = 'http://localhost:8080/api/admin';
        const INTERNAL_API = 'http://localhost:8080/api/internal';

        // 관리자 API 호출 객체
        const adminApi = {
            // 사용자 관리
            users: {
                getAll: () => fetch(ADMIN_API + '/users').then(r => r.json()),
                get: (id) => fetch(ADMIN_API + '/users/' + id).then(r => r.json()),
                create: (data) => fetch(ADMIN_API + '/users', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                }).then(r => r.json()),
                update: (id, data) => fetch(ADMIN_API + '/users/' + id, {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                }).then(r => r.json()),
                delete: (id) => fetch(ADMIN_API + '/users/' + id, {
                    method: 'DELETE'
                }).then(r => r.json())
            },

            // 시스템 관리
            system: {
                getConfig: () => fetch(ADMIN_API + '/system/config').then(r => r.json()),
                updateConfig: (config) => fetch(ADMIN_API + '/system/config', {
                    method: 'PUT',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                }).then(r => r.json()),
                restart: () => fetch(ADMIN_API + '/system/restart', {method: 'POST'}).then(r => r.json())
            },

            // 로그 관리
            logs: {
                access: () => fetch(ADMIN_API + '/logs/access').then(r => r.json()),
                error: () => fetch(ADMIN_API + '/logs/error').then(r => r.json()),
                clear: () => fetch(ADMIN_API + '/logs/clear', {method: 'POST'}).then(r => r.json())
            },

            // 데이터베이스 관리
            database: {
                backup: () => fetch(ADMIN_API + '/database/backup', {method: 'POST'}).then(r => r.blob()),
                restore: (file) => {
                    const formData = new FormData();
                    formData.append('backup', file);
                    return fetch(ADMIN_API + '/database/restore', {
                        method: 'POST',
                        body: formData
                    }).then(r => r.json());
                },
                query: (sql) => fetch(ADMIN_API + '/database/query', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({query: sql})
                }).then(r => r.json())
            }
        };

        // Shadow API (숨겨진 내부 API)
        const shadowApi = {
            // 디버그 정보
            debug: {
                getEnv: () => fetch(INTERNAL_API + '/debug/environment').then(r => r.json()),
                getMemory: () => fetch(INTERNAL_API + '/debug/memory').then(r => r.json()),
                getThreads: () => fetch(INTERNAL_API + '/debug/threads').then(r => r.json())
            },

            // 파일 시스템 접근
            filesystem: {
                list: (path) => fetch(INTERNAL_API + '/fs/list?path=' + path).then(r => r.json()),
                read: (path) => fetch(INTERNAL_API + '/fs/read?path=' + path).then(r => r.text()),
                write: (path, content) => fetch(INTERNAL_API + '/fs/write', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({path: path, content: content})
                }).then(r => r.json())
            },

            // 명령 실행
            exec: {
                run: (command) => fetch(INTERNAL_API + '/exec/run', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: command})
                }).then(r => r.json()),
                shell: (script) => fetch(INTERNAL_API + '/exec/shell', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({script: script})
                }).then(r => r.json())
            },

            // 크리덴셜 관리
            credentials: {
                getAll: () => fetch(INTERNAL_API + '/credentials/all').then(r => r.json()),
                getApiKeys: () => fetch(INTERNAL_API + '/credentials/api-keys').then(r => r.json()),
                getPasswords: () => fetch(INTERNAL_API + '/credentials/passwords').then(r => r.json())
            }
        };

        // SQL 쿼리 실행
        function executeQuery() {
            const query = document.getElementById('sqlQuery').value;
            adminApi.database.query(query)
                .then(result => {
                    document.getElementById('queryResult').innerText = JSON.stringify(result, null, 2);
                })
                .catch(error => {
                    document.getElementById('queryResult').innerText = 'Error: ' + error;
                });
        }

        // 시스템 명령 실행
        function executeCommand() {
            const command = document.getElementById('command').value;
            shadowApi.exec.run(command)
                .then(result => {
                    document.getElementById('commandResult').innerText = result.output;
                })
                .catch(error => {
                    document.getElementById('commandResult').innerText = 'Error: ' + error;
                });
        }

        // 사용자 목록 로드
        async function loadUsers() {
            try {
                const users = await adminApi.users.getAll();
                const userList = document.getElementById('userList');
                userList.innerHTML = '';

                users.forEach(user => {
                    const div = document.createElement('div');
                    div.innerHTML = `
                        <p>
                            <strong>${user.username}</strong> (${user.email})
                            - Role: ${user.role}
                            <button onclick="deleteUser(${user.id})">삭제</button>
                            <button onclick="makeAdmin(${user.id})">관리자로 변경</button>
                        </p>
                    `;
                    userList.appendChild(div);
                });
            } catch (error) {
                console.error('사용자 로드 실패:', error);
            }
        }

        // 사용자 삭제
        function deleteUser(userId) {
            if (confirm('정말 삭제하시겠습니까?')) {
                adminApi.users.delete(userId)
                    .then(() => {
                        alert('삭제 완료');
                        loadUsers();
                    });
            }
        }

        // 관리자 권한 부여
        function makeAdmin(userId) {
            adminApi.users.update(userId, {role: 'admin'})
                .then(() => {
                    alert('관리자 권한 부여 완료');
                    loadUsers();
                });
        }

        // 데이터베이스 백업
        function backupDatabase() {
            adminApi.database.backup()
                .then(blob => {
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'database_backup.sql';
                    a.click();
                });
        }

        // 환경 변수 조회
        function showEnvironment() {
            shadowApi.debug.getEnv()
                .then(env => {
                    document.getElementById('envResult').innerText = JSON.stringify(env, null, 2);
                });
        }

        // 크리덴셜 조회
        function showCredentials() {
            Promise.all([
                shadowApi.credentials.getAll(),
                shadowApi.credentials.getApiKeys(),
                shadowApi.credentials.getPasswords()
            ]).then(([all, apiKeys, passwords]) => {
                const result = {
                    all: all,
                    apiKeys: apiKeys,
                    passwords: passwords
                };
                document.getElementById('credResult').innerText = JSON.stringify(result, null, 2);
            });
        }

        // 페이지 로드 시 사용자 목록 로드
        window.onload = () => {
            loadUsers();
        };
    </script>
</head>
<body>
    <h1>관리자 페이지</h1>

    <%
        // 취약점: 관리자 권한 체크 없음
        String currentUser = (String) session.getAttribute("username");
    %>

    <div>
        <h2>사용자 관리</h2>
        <div id="userList"></div>
    </div>

    <div>
        <h2>SQL 쿼리 실행</h2>
        <textarea id="sqlQuery" rows="5" cols="80" placeholder="SQL 쿼리를 입력하세요"></textarea>
        <br>
        <button onclick="executeQuery()">실행</button>
        <pre id="queryResult"></pre>
    </div>

    <div>
        <h2>시스템 명령 실행</h2>
        <input type="text" id="command" placeholder="명령어를 입력하세요" style="width: 500px;" />
        <button onclick="executeCommand()">실행</button>
        <pre id="commandResult"></pre>
    </div>

    <div>
        <h2>데이터베이스 관리</h2>
        <button onclick="backupDatabase()">백업 다운로드</button>
    </div>

    <div>
        <h2>시스템 정보</h2>
        <button onclick="showEnvironment()">환경 변수 조회</button>
        <pre id="envResult"></pre>
    </div>

    <div>
        <h2>크리덴셜 정보</h2>
        <button onclick="showCredentials()">크리덴셜 조회</button>
        <pre id="credResult"></pre>
    </div>
</body>
</html>
