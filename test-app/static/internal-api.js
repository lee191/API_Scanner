// Internal API client for employee dashboards

const InternalAPI = {
    baseUrl: '/api/internal',

    // Shadow API: 내부 통계
    getStats: () => fetch(`/api/internal/stats`).then(r => r.json()),

    // Shadow API: 직원 목록
    getEmployees: () => fetch(`/api/internal/employees`).then(r => r.json()),

    // Shadow API: 프로젝트 정보
    getProjects: () => fetch(`/api/internal/projects`).then(r => r.json()),

    // Shadow API: 데이터 내보내기
    exportData: (type) => fetch(`/api/internal/export/${type}`).then(r => r.blob())
};

console.log('Internal API client loaded');
