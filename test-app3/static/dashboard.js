// dashboard.js - Level 3 APIs
console.log('✅ dashboard.js loaded (Level 3 - FINAL)');

// API calls for Level 3 - Dashboard
async function loadLevel3DashboardAPIs() {
    try {
        // Get dashboard widgets
        const widgetsRes = await fetch('/api/dashboard/widgets');
        const widgetsData = await widgetsRes.json();
        console.log('📊 /api/dashboard/widgets:', widgetsData);
        
        // Get dashboard summary
        const summaryRes = await fetch('/api/dashboard/summary');
        const summaryData = await summaryRes.json();
        console.log('📈 /api/dashboard/summary:', summaryData);
        
        // Get realtime data
        const realtimeRes = await fetch('/api/dashboard/realtime');
        const realtimeData = await realtimeRes.json();
        console.log('⚡ /api/dashboard/realtime:', realtimeData);
        
        console.log('🏁 Level 3 reached - Maximum depth!');
        
    } catch (error) {
        console.error('❌ Error loading Level 3 Dashboard APIs:', error);
    }
}

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Page loaded: Level 3 (Dashboard - FINAL DEPTH)');
    loadLevel3DashboardAPIs();
});
