// settings.js - Level 3 APIs
console.log('✅ settings.js loaded (Level 3 - FINAL)');

// API calls for Level 3 - Settings
async function loadLevel3SettingsAPIs() {
    try {
        // Get general settings
        const generalRes = await fetch('/api/settings/general');
        const generalData = await generalRes.json();
        console.log('⚙️ /api/settings/general:', generalData);
        
        // Get security settings
        const securityRes = await fetch('/api/settings/security');
        const securityData = await securityRes.json();
        console.log('🔐 /api/settings/security:', securityData);
        
        // Get notification settings
        const notifRes = await fetch('/api/settings/notifications');
        const notifData = await notifRes.json();
        console.log('🔔 /api/settings/notifications:', notifData);
        
        // Hidden API call (not documented)
        const debugRes = await fetch('/api/internal/debug');
        const debugData = await debugRes.json();
        console.log('🕵️ /api/internal/debug (HIDDEN):', debugData);
        
        console.log('🏁 Level 3 reached - Maximum depth!');
        
    } catch (error) {
        console.error('❌ Error loading Level 3 Settings APIs:', error);
    }
}

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Page loaded: Level 3 (Settings - FINAL DEPTH)');
    loadLevel3SettingsAPIs();
});
