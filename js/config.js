/**
 * TRAVEL ECOSYSTEM — GLOBAL CONFIGURATION
 * ------------------------------------
 * This file centralizes the API URL and other environment-specific settings.
 */

(function() {
    // 1. Check for injected URL (from Vercel build script)
    if (window.ELITE_API_URL) {
        console.log("Elite API Sync: Injected URL detected.");
        return;
    }

    // 2. Local vs Production Auto-Detection
    const isLocal = window.location.hostname === 'localhost' || 
                    window.location.hostname === '127.0.0.1' || 
                    window.location.hostname.includes('192.168.');

    if (isLocal) {
        if (window.location.hostname.includes('192.168.')) {
            window.ELITE_API_URL = `http://${window.location.hostname}:10000`;
        } else {
            window.ELITE_API_URL = 'http://localhost:10000';
        }
    } else {
        // PRODUCTION FALLBACK
        // We use the primary Render backend URL
        window.ELITE_API_URL = 'https://gotrip-backend.onrender.com';
    }

    console.log(`Elite API Sync: Targeted at ${window.ELITE_API_URL}`);
})();

// Restore native right-click context menu blocked by the Three.js WebGL canvas
document.addEventListener('contextmenu', function(e) {
  Object.defineProperty(e, 'preventDefault', {
    value: function() {},
    writable: true,
    configurable: true
  });
}, true /* capture phase runs before Three.js */);
