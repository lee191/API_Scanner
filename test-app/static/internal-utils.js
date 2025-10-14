// Internal utility functions

const InternalUtils = {
    // Shadow API: 캐시 클리어
    clearCache: () => fetch('/api/internal/cache/clear', { method: 'POST' }),

    // Shadow API: 백그라운드 작업 실행
    runBackgroundJob: (jobName) => 
        fetch('/api/internal/jobs/run', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job: jobName })
        }),

    // Shadow API: 데이터베이스 쿼리 실행
    executeQuery: (query) =>
        fetch('/api/internal/db/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query })
        })
};
