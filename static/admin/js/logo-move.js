// logo-move.js
document.addEventListener('DOMContentLoaded', function() {
    // Small delay to ensure Jazzmin is fully loaded
    setTimeout(function() {
        try {
            console.log('Logo mover script starting...');
            
            // Find the navbar first
            const navbar = document.querySelector('.navbar');
            if (!navbar) {
                console.error('Navbar not found');
                return;
            }

            // Find or create the logo container
            let logoContainer = document.querySelector('.nag-header-logo-container');
            if (!logoContainer) {
                logoContainer = document.createElement('div');
                logoContainer.className = 'nag-header-logo-container';
            }

            // Find the user menu to position the logo before it
            const userMenu = document.querySelector('.navbar-nav.ml-auto');
            if (userMenu) {
                // Only insert if it's not already there
                if (!logoContainer.parentNode) {
                    userMenu.parentNode.insertBefore(logoContainer, userMenu);
                }
            } else {
                console.log('User menu not found, appending to navbar');
                navbar.appendChild(logoContainer);
            }

            // Create or update logo
            let logo = logoContainer.querySelector('.nag-logo');
            if (!logo) {
                logo = document.createElement('img');
                logo.className = 'nag-logo';
                
                // Set correct static path
                logo.src = '/static/admin/img/logo.png';
                console.log('Attempting to load logo from:', logo.src);
                
                logo.alt = 'NAG Logo';
                logo.style.cssText = 'display: block !important; visibility: visible !important; opacity: 1 !important;';
                
                // Add load and error event handlers
                logo.onload = function() {
                    console.log('Logo image loaded successfully');
                    console.log('Natural size:', logo.naturalWidth, 'x', logo.naturalHeight);
                    console.log('Display size:', logo.offsetWidth, 'x', logo.offsetHeight);
                    console.log('Computed style:', window.getComputedStyle(logo).display, window.getComputedStyle(logo).visibility);
                };
                logo.onerror = function() {
                    console.error('Failed to load logo image from:', logo.src);
                    // Try alternative path
                    logo.src = '/static/admin/img/logo.png';
                    console.log('Trying alternative path:', logo.src);
                };
                
                // Create a link wrapper
                const link = document.createElement('a');
                link.href = '';
                link.style.display = 'block';
                link.appendChild(logo);
                logoContainer.appendChild(link);
                
                console.log('Logo element created and inserted');
            }
        } catch (err) {
            console.error('logo-move error:', err);
        }
    }, 500); // 500ms delay to ensure everything is loaded
});
