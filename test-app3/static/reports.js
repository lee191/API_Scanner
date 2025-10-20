// reports.js - Level 2 APIs
console.log('✅ reports.js loaded (Level 2)');

// API calls for Level 2 - Reports
async function loadLevel2ReportAPIs() {
    try {
        // Get sales report
        const salesRes = await fetch('/api/reports/sales');
        const salesData = await salesRes.json();
        console.log('💰 /api/reports/sales:', salesData);
        
        // Get monthly report
        const monthlyRes = await fetch('/api/reports/monthly');
        const monthlyData = await monthlyRes.json();
        console.log('📅 /api/reports/monthly:', monthlyData);
        
        // Get export info
        const exportRes = await fetch('/api/reports/export');
        const exportData = await exportRes.json();
        console.log('📥 /api/reports/export:', exportData);
        
    } catch (error) {
        console.error('❌ Error loading Level 2 Report APIs:', error);
    }
}

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Page loaded: Level 2 (Reports)');
    loadLevel2ReportAPIs();
});
