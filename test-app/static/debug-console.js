// Debug console JavaScript

const DebugConsole = {
    // Shadow API: 디버그 설정 조회
    getConfig: () => fetch('/api/internal/debug/config').then(r => r.json()),

    // Shadow API: 환경 변수 조회
    getEnv: () => fetch('/api/internal/debug/env').then(r => r.json()),

    // Shadow API: 메모리 덤프
    memoryDump: () => fetch('/api/internal/debug/memory').then(r => r.json()),

    // Shadow API: 스택 트레이스
    getStackTrace: () => fetch('/api/internal/debug/stack').then(r => r.json())
};

console.log('Debug console loaded');
