// main.js - Level 0 APIs
console.log('✅ main.js loaded (Level 0)');

// API calls for Level 0
async function loadLevel0APIs() {
    try {
        // Health check
        const healthRes = await fetch('/api/health');
        const healthData = await healthRes.json();
        console.log('🏥 /api/health:', healthData);
        
        // Server info
        const infoRes = await fetch('/api/info');
        const infoData = await infoRes.json();
        console.log('ℹ️ /api/info:', infoData);
        
    } catch (error) {
        console.error('❌ Error loading Level 0 APIs:', error);
    }
}

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Page loaded: Level 0 (Home)');
    loadLevel0APIs();
});
