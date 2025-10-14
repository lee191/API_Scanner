// Admin dashboard functionality

class AdminDashboard {
    constructor() {
        this.apiBase = '/api/internal/admin';
    }

    // Shadow API: 대시보드 통계
    async getStats() {
        return fetch(`${this.apiBase}/stats`).then(r => r.json());
    }

    // Shadow API: 활성 세션 목록
    async getActiveSessions() {
        return fetch(`${this.apiBase}/sessions`).then(r => r.json());
    }

    // Shadow API: 로그 조회
    async getLogs() {
        return fetch(`${this.apiBase}/logs`).then(r => r.json());
    }
}

const dashboard = new AdminDashboard();
