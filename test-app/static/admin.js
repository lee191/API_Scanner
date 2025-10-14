// Admin panel JavaScript
// Shadow API endpoints used in admin panel

const AdminAPI = {
    // Shadow API: 모든 사용자 정보 조회 (비밀번호 포함!)
    getAllUsers: async () => {
        const response = await fetch('/api/internal/admin/users');
        return response.json();
    },

    // Shadow API: 사용자 삭제
    deleteUser: async (userId) => {
        return fetch('/api/internal/admin/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_id: userId })
        });
    },

    // Shadow API: 시스템 설정 변경
    updateConfig: async (config) => {
        return fetch('/api/internal/admin/config', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
    }
};

console.log('Admin panel loaded - Shadow APIs available');
