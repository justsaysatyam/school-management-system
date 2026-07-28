/* =====================================================
   Mid Point School - Main JavaScript Engine
   Mobile Responsiveness & Interactive Controls
   ===================================================== */

document.addEventListener('DOMContentLoaded', () => {
    initMobileSidebar();
    initPublicNavbar();
    initPortalDropdowns();
    initAutoDismissAlerts();
    initTableTouchScroll();
});

/**
 * Mobile Sidebar Drawer for Dashboard Portals (Admin, Teacher, Student)
 */
function initMobileSidebar() {
    const toggleBtns = document.querySelectorAll('.mobile-sidebar-toggle');
    const sidebar = document.querySelector('.sidebar');
    let overlay = document.querySelector('.sidebar-overlay');

    if (!sidebar) return;

    // Create overlay dynamically if missing in DOM
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }

    function openSidebar() {
        sidebar.classList.add('open');
        overlay.classList.add('active');
        document.body.classList.add('sidebar-active-lock');
    }

    function closeSidebar() {
        sidebar.classList.remove('open');
        overlay.classList.remove('active');
        document.body.classList.remove('sidebar-active-lock');
    }

    toggleBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (sidebar.classList.contains('open')) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    });

    overlay.addEventListener('click', closeSidebar);

    // Close sidebar when clicking any nav link inside on mobile
    const sidebarLinks = sidebar.querySelectorAll('.nav-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                closeSidebar();
            }
        });
    });

    // Handle screen resize
    window.addEventListener('resize', () => {
        if (window.innerWidth > 768 && sidebar.classList.contains('open')) {
            closeSidebar();
        }
    });
}

/**
 * Public Website Header Navbar & Mobile Hamburger Drawer
 */
function initPublicNavbar() {
    const navToggles = document.querySelectorAll('.public-nav-toggle');
    
    navToggles.forEach(toggle => {
        const targetId = toggle.getAttribute('data-target') || 'publicNavMenu';
        const navMenu = document.getElementById(targetId) || document.querySelector('.nav-menu');

        if (!navMenu) return;

        toggle.addEventListener('click', (e) => {
            e.stopPropagation();
            toggle.classList.toggle('active');
            navMenu.classList.toggle('mobile-active');
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        const navMenu = document.querySelector('.nav-menu.mobile-active');
        const navToggle = document.querySelector('.public-nav-toggle.active');
        if (navMenu && !navMenu.contains(e.target) && (!navToggle || !navToggle.contains(e.target))) {
            navMenu.classList.remove('mobile-active');
            if (navToggle) navToggle.classList.remove('active');
        }
    });
}

/**
 * Portal Dropdown Menu Toggles for Touch & Desktop
 */
function initPortalDropdowns() {
    const dropdowns = document.querySelectorAll('.portal-dropdown');

    dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('.portal-trigger') || dropdown.querySelector('.nav-link') || dropdown.children[0];
        const menu = dropdown.querySelector('.portal-menu');

        if (!trigger || !menu) return;

        trigger.addEventListener('click', (e) => {
            if (window.innerWidth <= 1024 || 'ontouchstart' in window) {
                e.preventDefault();
                e.stopPropagation();

                // Close other open dropdowns
                dropdowns.forEach(other => {
                    if (other !== dropdown) {
                        const otherMenu = other.querySelector('.portal-menu');
                        if (otherMenu) otherMenu.classList.remove('show');
                    }
                });

                menu.classList.toggle('show');
            }
        });
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.portal-dropdown')) {
            document.querySelectorAll('.portal-menu.show').forEach(m => m.classList.remove('show'));
        }
    });
}

/**
 * Auto Dismiss Alert Messages
 */
function initAutoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        // Add dismiss button if missing
        if (!alert.querySelector('.alert-close')) {
            const closeBtn = document.createElement('button');
            closeBtn.className = 'alert-close';
            closeBtn.innerHTML = '&times;';
            closeBtn.style.cssText = 'background:none; border:none; margin-left:auto; font-size:1.25rem; cursor:pointer; color:inherit; opacity:0.7;';
            closeBtn.addEventListener('click', () => {
                alert.style.opacity = '0';
                setTimeout(() => alert.remove(), 300);
            });
            alert.appendChild(closeBtn);
        }

        // Auto fade out after 6 seconds
        setTimeout(() => {
            if (document.body.contains(alert)) {
                alert.style.transition = 'opacity 0.5s ease';
                alert.style.opacity = '0';
                setTimeout(() => { if (document.body.contains(alert)) alert.remove(); }, 500);
            }
        }, 6000);
    });
}

/**
 * Touch Table Scroll Shadow Hints
 */
function initTableTouchScroll() {
    const containers = document.querySelectorAll('.table-container');
    containers.forEach(container => {
        if (container.scrollWidth > container.clientWidth) {
            container.classList.add('has-scroll');
        }
        container.addEventListener('scroll', () => {
            if (container.scrollLeft > 10) {
                container.classList.add('scrolling');
            } else {
                container.classList.remove('scrolling');
            }
        });
    });
}
