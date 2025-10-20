// users.js - Level 1 APIs
console.log('✅ users.js loaded (Level 1)');

// API calls for Level 1 - Users
async function loadLevel1UserAPIs() {
    try {
        // Get all users
        const usersRes = await fetch('/api/users');
        const usersData = await usersRes.json();
        console.log('👥 /api/users:', usersData);
        
        // Get specific user
        const userRes = await fetch('/api/users/1');
        const userData = await userRes.json();
        console.log('👤 /api/users/1:', userData);
        
        // Get user profile
        const profileRes = await fetch('/api/users/1/profile');
        const profileData = await profileRes.json();
        console.log('👤 /api/users/1/profile:', profileData);
        
    } catch (error) {
        console.error('❌ Error loading Level 1 User APIs:', error);
    }
}

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Page loaded: Level 1 (Users)');
    loadLevel1UserAPIs();
});
