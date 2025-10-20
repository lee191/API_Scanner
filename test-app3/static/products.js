// products.js - Level 1 APIs
console.log('✅ products.js loaded (Level 1)');

// API calls for Level 1 - Products
async function loadLevel1ProductAPIs() {
    try {
        // Get all products
        const productsRes = await fetch('/api/products');
        const productsData = await productsRes.json();
        console.log('📦 /api/products:', productsData);
        
        // Get specific product
        const productRes = await fetch('/api/products/1');
        const productData = await productRes.json();
        console.log('📦 /api/products/1:', productData);
        
        // Search products
        const searchRes = await fetch('/api/products/search?q=laptop');
        const searchData = await searchRes.json();
        console.log('🔍 /api/products/search:', searchData);
        
    } catch (error) {
        console.error('❌ Error loading Level 1 Product APIs:', error);
    }
}

// Auto-load on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('📄 Page loaded: Level 1 (Products)');
    loadLevel1ProductAPIs();
});
