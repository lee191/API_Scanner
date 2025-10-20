// analytics.js - Level 3 APIs
console.log('✅ analytics.js loaded (Level 3 - FINAL)');

// API calls for Level 3 - Analytics
async function loadLevel3AnalyticsAPIs() {
    try {
        // Get analytics events
        const eventsRes = await fetch('/api/analytics/events');
        const eventsData = await eventsRes.json();
        console.log('📊 /api/analytics/events:', eventsData);
        
        // Get analytics metrics
        const metricsRes = await fetch('/api/analytics/metrics');
        const metricsData = await metricsRes.json();
        console.log('📈 /api/analytics/metrics:', metricsData);
        
        // Get funnel data
        const funnelRes = await fetch('/api/analytics/funnel');
        const funnelData = await funnelRes.json();
        console.log('🎯 /api/analytics/funnel:', funnelData);
        
        console.log('🏁 Level 3 reached - Maximum depth!');
        
    } catch (error) {
        console.error('❌ Error loading Level 3 Analytics APIs:', error);
    }
}

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Page loaded: Level 3 (Analytics - FINAL DEPTH)');
    loadLevel3AnalyticsAPIs();
});
