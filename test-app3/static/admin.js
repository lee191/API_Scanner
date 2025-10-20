// admin.js - Level 2 APIs
console.log('✅ admin.js loaded (Level 2)');

// API calls for Level 2 - Admin
async function loadLevel2AdminAPIs() {
    try {
        // Get admin stats
        const statsRes = await fetch('/api/admin/stats');
        const statsData = await statsRes.json();
        console.log('📊 /api/admin/stats:', statsData);
        
        // Get admin users
        const usersRes = await fetch('/api/admin/users');
        const usersData = await usersRes.json();
        console.log('👥 /api/admin/users:', usersData);
        
        // Get admin config
        const configRes = await fetch('/api/admin/config');
        const configData = await configRes.json();
        console.log('⚙️ /api/admin/config:', configData);
        
        // Get admin logs
        const logsRes = await fetch('/api/admin/logs');
        const logsData = await logsRes.json();
        console.log('📝 /api/admin/logs:', logsData);
        
    } catch (error) {
        console.error('❌ Error loading Level 2 Admin APIs:', error);
    }
}

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Page loaded: Level 2 (Admin)');
    loadLevel2AdminAPIs();
});
