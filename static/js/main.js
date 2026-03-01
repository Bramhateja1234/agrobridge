/* ============================================================
   AgroBridge – Main JavaScript
   Handles: JWT auth, navbar population, token refresh
   ============================================================ */

const API_BASE = '/api';

// ── Auth Helpers ─────────────────────────────────────────────

function getToken() { return localStorage.getItem('accessToken'); }
function getUser() {
    try { return JSON.parse(localStorage.getItem('user') || '{}'); } catch { return {}; }
}
function isLoggedIn() { return !!getToken(); }
function logout() {
    const refresh = localStorage.getItem('refreshToken');
    if (refresh) {
        fetch(`${API_BASE}/auth/logout/`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${getToken()}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh })
        }).catch(() => { });
    }
    localStorage.clear();
    window.location.href = '/auth/login/';
}

// ── Navbar Population ─────────────────────────────────────────

function populateNav() {
    const container = document.getElementById('navAuthLinks');
    if (!container) return;
    const user = getUser();

    // Simple translation map for JS (MVP)
    let lang = document.documentElement.lang || 'en';
    if (lang.includes('-')) lang = lang.split('-')[0];
    const labels = {
        'en': { dashboard: 'Dashboard', orders: 'Orders & Payments', cart: 'Cart', logout: 'Logout', login: 'Login', getStarted: 'Get Started', account: 'Account', profile: 'My Profile' },
        'hi': { dashboard: 'डैशबोर्ड', orders: 'आदेश और भुगतान', cart: 'कार्ट', logout: 'लॉगआउट', login: 'लॉगिन', getStarted: 'शुरू करें', account: 'खाता', profile: 'मेरी प्रोफाइल' },
        'te': { dashboard: 'డాష్‌బోర్డ్', orders: 'ఆర్డర్లు & చెల్లింపులు', cart: 'కార్ట్', logout: 'లాగ్ అవుట్', login: 'లాగిన్', getStarted: 'మొదలుపెట్టండి', account: 'ఖాతా', profile: 'నా ప్రొఫైల్' }
    }[lang] || labels['en'];

    if (isLoggedIn()) {
        if (user.role === 'delivery') {
            const browseItem = document.getElementById('navBrowseCropsItem');
            if (browseItem) browseItem.style.display = 'none';
        }

        let dashLink = '/browse/';
        if (user.role === 'farmer' || user.role === 'admin') dashLink = '/farmer/dashboard/';
        else if (user.role === 'delivery') dashLink = '/delivery/dashboard/';

        const historyLink = '/orders/';
        container.innerHTML = `
            ${user.role === 'consumer' ? `
            <li class="nav-item"><a class="nav-link" href="/cart/"><i class="bi bi-cart3 me-1"></i>${labels.cart}</a></li>
            ` : ''}
            <li class="nav-item dropdown">
                <a class="nav-link dropdown-toggle d-flex align-items-center gap-1" href="#" data-bs-toggle="dropdown">
                    <i class="bi bi-person-circle"></i> ${user.name?.split(' ')[0] || labels.account}
                </a>
                <ul class="dropdown-menu dropdown-menu-end shadow-lg border-0 rounded-3 mt-2">
                    <li class="px-3 py-2 bg-light rounded-top d-flex align-items-center">
                        <i class="bi bi-person-circle fs-3 text-secondary me-2"></i>
                        <div>
                            <span class="d-block fw-bold text-dark lh-1">${user.name || 'User'}</span>
                            <small class="text-muted text-capitalize">${user.role}</small>
                        </div>
                    </li>
                    <li><hr class="dropdown-divider m-0"></li>
                    <li><a class="dropdown-item py-2 mt-1" href="/profile/"><i class="bi bi-person-badge me-2 text-primary"></i>${labels.profile}</a></li>
                    <li><a class="dropdown-item py-2" href="${dashLink}"><i class="bi bi-grid me-2 text-success"></i>${labels.dashboard}</a></li>
                    ${user.role === 'consumer' ? `<li><a class="dropdown-item py-2" href="${historyLink}"><i class="bi bi-bag-check me-2 text-info"></i>${labels.orders}</a></li>` : ''}
                    <li><hr class="dropdown-divider"></li>
                    <li><a class="dropdown-item text-danger py-2" href="#" onclick="logout()"><i class="bi bi-box-arrow-left me-2"></i>${labels.logout}</a></li>
                </ul>
            </li>`;
    } else {
        container.innerHTML = `
            <li class="nav-item"><a class="btn btn-outline-light btn-sm px-3" href="/auth/login/">${labels.login}</a></li>
            <li class="nav-item ms-2"><a class="btn btn-warning btn-sm px-3 fw-semibold" href="/auth/register/">${labels.getStarted}</a></li>`;
    }
}

// ── Token Refresh ────────────────────────────────────────────

async function refreshToken() {
    const refresh = localStorage.getItem('refreshToken');
    if (!refresh) return false;
    try {
        const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh })
        });
        if (res.ok) {
            const data = await res.json();
            localStorage.setItem('accessToken', data.access);
            return true;
        }
    } catch { }
    return false;
}

// ── Auth-aware Fetch ────────────────────────────────────────

async function authFetch(url, options = {}) {
    let token = getToken();
    options.headers = { ...options.headers, 'Authorization': `Bearer ${token}` };
    let res = await fetch(url, options);
    if (res.status === 401) {
        const refreshed = await refreshToken();
        if (refreshed) {
            options.headers['Authorization'] = `Bearer ${getToken()}`;
            res = await fetch(url, options);
        } else {
            logout();
        }
    }
    return res;
}

// ── Init ────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    populateNav();

    // Add scroll effect to navbar
    window.addEventListener('scroll', () => {
        const nav = document.getElementById('mainNav');
        if (nav) nav.classList.toggle('scrolled', window.scrollY > 50);
    });

    // Set current language in selector
    const langData = document.getElementById('languageData');
    if (langData) {
        const currentLang = langData.getAttribute('data-current-lang');
        const langSelect = document.querySelector('select[name="language"]');
        if (langSelect && currentLang) {
            langSelect.value = currentLang;
        }
    }
});
