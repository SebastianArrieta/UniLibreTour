/* ============================================================================
   UniLibreTour — App shell (port del prototipo React: DataContext + Layout
   + Auth). Estado global gestionado en localStorage igual que el mockup.

   API global: window.Museo
   Estado (claves localStorage):
     museo-theme   : 'dark' | 'light'
     museo-rol     : Role  ('visitante' por defecto)
     museo-favs    : string[] ids de contenido favorito
     museo-datos-v1: snapshot del dataset demo (cache de /api/demo-data)
     museo-perfil  : objeto con preferencias del usuario (opcional)

   Datos:
     Museo.loadData()          -> Promise<Object> (fetch /api/demo-data, cachea)
     Museo.data()              -> dataset actual (null hasta cargar)
     Museo.getUser()           -> Promise<User|undefined> (demo por rol)
     Museo.getContributions(pt) -> filtro de aportes (author/submittedBy)

   Estado / sesión:
     Museo.role                -> rol actual (string)
     Museo.login(role)         -> persiste rol y redirige al dashboard
     Museo.logout()            -> limpia rol y redirige a '/'
     Museo.redirectForRole(role)

   Header dinámico (apunta al HTML del partial header.html):
     #museo-role-nav   -> enlace "Mi Espacio"/"Panel Admin" por rol
     #museo-auth-area  -> botón "Ingresar" | (pill perfil + "Salir")

   Puntos y niveles (igual a data.ts):
     Museo.levelInfo(points)   -> { level, pointsIntoLevel, progressPct, ... }

   Favoritos:
     Museo.getFavs() / isFav(id) / toggleFav(id) / bindFavButtons(root)
   ============================================================================ */

(function (global) {
    'use strict';

    var KEYS = {
        THEME: 'museo-theme',
        ROLE: 'museo-rol',
        FAVS: 'museo-favs',
        DATA: 'museo-datos-v1',
        PERFIL: 'museo-perfil',
    };

    var DATA_ENDPOINT = '/api/demo-data';
    var POINTS_PER_LEVEL = 500;
    var MAX_LEVEL = 20;

    var ROLE_HOME = {
        estudiante: '/estudiante',
        egresado: '/egresado',
        docente: '/docente',
        admin: '/admin',
        visitante: '/',
    };

    var ROLE_DASH = {
        estudiante: { label: 'Mi Espacio', href: '/estudiante' },
        egresado: { label: 'Mi Espacio', href: '/egresado' },
        docente: { label: 'Mi Espacio', href: '/docente' },
        admin: { label: 'Panel Admin', href: '/admin' },
    };

    var USER_EMAIL = {
        estudiante: 'ana.bermudez@unilibre.edu.co',
        egresado: 'egresado@unilibre.edu.co',
        docente: 'h.casas@unilibre.edu.co',
        admin: 'admin@unilibre.edu.co',
    };

    /* ---------- utilidades ---------- */
    function lsGet(key) {
        try { return JSON.parse(localStorage.getItem(key)); } catch (e) { return null; }
    }
    function lsSet(key, value) {
        try { localStorage.setItem(key, JSON.stringify(value)); } catch (e) { /* noop */ }
    }
    function lsRemove(key) {
        try { localStorage.removeItem(key); } catch (e) { /* noop */ }
    }
    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
    function isAuthRole(role) { return role !== 'visitante'; }

    /* ---------- datos demo ---------- */
    var _data = null;
    var _fetching = null;

    function loadData(force) {
        if (!force && _data) return Promise.resolve(_data);
        if (_fetching) return _fetching;
        _fetching = fetch(DATA_ENDPOINT, { headers: { Accept: 'application/json' } })
            .then(function (r) { if (!r.ok) throw new Error('demo-data ' + r.status); return r.json(); })
            .then(function (json) {
                _data = json;
                try { localStorage.setItem(KEYS.DATA, JSON.stringify(json)); } catch (e) { /* noop */ }
                return json;
            })
            .catch(function () {
                var cached = lsGet(KEYS.DATA);
                if (cached) { _data = cached; return cached; }
                throw new Error('No hay datos demo disponibles');
            })
            .finally(function () { _fetching = null; });
        return _fetching;
    }

    function cachedOrLoaded() {
        if (_data) return _data;
        var cached = lsGet(KEYS.DATA);
        if (cached) { _data = cached; return cached; }
        return null;
    }

    function getUser() {
        return loadData().then(function (d) {
            var emails = USER_EMAIL;
            var u = (d.users || []).find(function (x) {
                return x.email === emails[Museo.role] || x.email === USER_EMAIL[Museo.role];
            });
            return u;
        });
    }

    function contributionsOf(user) {
        var d = cachedOrLoaded();
        if (!user || !user.name || !d) return [];
        var seen = {};
        var result = [];
        var all = (d.contentItems || []).concat(d.contentQueue || []);
        all.forEach(function (item) {
            if ((item.author === user.name || item.submittedBy === user.name) && !seen[item.id]) {
                seen[item.id] = 1;
                result.push(item);
            }
        });
        return result;
    }

    /* ---------- tema ---------- */
    function getTheme() {
        try {
            var t = localStorage.getItem(KEYS.THEME);
            return t === 'light' ? 'light' : 'dark';
        } catch (e) { return 'dark'; }
    }
    function setTheme(t) {
        var theme = t === 'light' ? 'light' : 'dark';
        try { localStorage.setItem(KEYS.THEME, theme); } catch (e) { /* noop */ }
        document.documentElement.setAttribute('data-theme', theme);
        syncThemeToggleUI(theme);
    }
    function toggleTheme() { setTheme(getTheme() === 'dark' ? 'light' : 'dark'); }

    function syncThemeToggleUI(theme) {
        var btn = document.querySelector('.theme-toggle');
        if (!btn) return;
        var knob = btn.querySelector('.theme-toggle-knob');
        var icon = btn.querySelector('[data-theme-icon]');
        if (knob) knob.style.left = theme === 'dark' ? '18px' : '2px';
        if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
        btn.setAttribute('data-theme', theme);
    }

    /* ---------- rol ---------- */
    function getRole() {
        try {
            var r = localStorage.getItem(KEYS.ROLE);
            return r || 'visitante';
        } catch (e) { return 'visitante'; }
    }
    function setRole(role) {
        try { localStorage.setItem(KEYS.ROLE, role || 'visitante'); } catch (e) { /* noop */ }
        renderRoleNav();
        renderAuth();
    }
    function redirectForRole(role) {
        window.location.href = ROLE_HOME[role] || '/';
    }
    function login(role) {
        setRole(role);
        redirectForRole(role);
    }
    function logout() {
        lsRemove(KEYS.ROLE);
        lsRemove(KEYS.FAVS);
        lsRemove(KEYS.PERFIL);
        window.location.href = '/';
    }

    /* ---------- header dinámico ---------- */
    function pathActive(href) {
        var p = window.location.pathname;
        if (href === '/') return p === '/';
        return p === href || p.indexOf(href + '/') === 0;
    }

    function renderRoleNav() {
        var nav = document.getElementById('museo-role-nav');
        if (!nav) return;
        var role = Museo.role;
        var dash = ROLE_DASH[role];
        if (!dash) {
            nav.innerHTML = '';
            return;
        }
        var active = pathActive(dash.href);
        nav.innerHTML = '<a class="nav-link' + (active ? ' active' : '') + '" href="' + dash.href + '">' + esc(dash.label) + '</a>';
    }

    function renderAuth() {
        var area = document.getElementById('museo-auth-area');
        if (!area) return;
        var role = Museo.role;
        if (!isAuthRole(role)) {
            area.innerHTML = '<a href="/login" class="text-sm px-4 py-1.5 rounded btn-primary btn-float">Ingresar</a>';
            return;
        }
        getUser().then(function (me) {
            var label = (me && me.name) || role;
            area.innerHTML =
                '<a href="/perfil" class="hidden sm:flex items-center gap-1.5 text-xs px-2 py-0.5 rounded-full font-mono transition-colors museo-profile-pill" ' +
                'style="background:rgba(211,47,47,0.12);color:#d32f2f;border:1px solid rgba(211,47,47,0.25)" title="Ver mi perfil">' +
                '<span class="truncate max-w-[120px]">' + esc(label) + '</span></a>' +
                '<button type="button" data-action="logout" class="text-xs px-3 py-1.5 rounded btn-outline-primary">Salir</button>';
        }).catch(function () {
            area.innerHTML = '<button type="button" data-action="logout" class="text-xs px-3 py-1.5 rounded btn-outline-primary">Salir</button>';
        });
    }

    function bindAuthClicks() {
        document.addEventListener('click', function (e) {
            var t = e.target && e.target.closest ? e.target.closest('[data-action]') : null;
            if (t && t.getAttribute('data-action') === 'logout') {
                e.preventDefault();
                Museo.logout();
            }
        });
    }

    /* ---------- favoritos ---------- */
    function getFavs() {
        var v = lsGet(KEYS.FAVS);
        return Array.isArray(v) ? v : [];
    }
    function isFav(id) { return getFavs().indexOf(String(id)) !== -1; }
    function setFavs(list) { lsSet(KEYS.FAVS, list); }
    function toggleFav(id) {
        var list = getFavs();
        var i = list.indexOf(String(id));
        if (i === -1) { list.push(String(id)); } else { list.splice(i, 1); }
        setFavs(list);
        return list;
    }
    function countFavs() { return getFavs().length; }

    function bindFavButtons(root, onChanged) {
        root = root || document;
        root.querySelectorAll('.fav-toggle').forEach(function (btn) {
            var id = btn.getAttribute('data-id');
            if (!id) return;
            btn.setAttribute('aria-pressed', Museo.isFav(id) ? 'true' : 'false');
            btn.classList.toggle('is-fav', Museo.isFav(id));
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                Museo.toggleFav(id);
                btn.classList.toggle('is-fav', Museo.isFav(id));
                btn.setAttribute('aria-pressed', Museo.isFav(id) ? 'true' : 'false');
                var icon = btn.querySelector('[data-fav-icon]');
                if (icon) icon.textContent = Museo.isFav(id) ? '♥' : '♡';
                if (typeof onChanged === 'function') onChanged(Museo.countFavs());
            });
        });
    }

    /* ---------- niveles y progreso ---------- */
    function levelInfo(points) {
        points = Number(points) || 0;
        var level = Math.min(MAX_LEVEL, Math.floor(points / POINTS_PER_LEVEL) + 1);
        var pointsIntoLevel = points - (level - 1) * POINTS_PER_LEVEL;
        var progressPct = level >= MAX_LEVEL ? 100 : (pointsIntoLevel / POINTS_PER_LEVEL) * 100;
        return {
            level: level,
            pointsIntoLevel: pointsIntoLevel,
            pointsForNextLevel: POINTS_PER_LEVEL,
            progressPct: progressPct,
            maxLevel: MAX_LEVEL,
        };
    }

    /* ---------- búsqueda ---------- */
    function searchAll(query) {
        var d = cachedOrLoaded();
        if (!d) return [];
        var q = String(query || '').trim().toLowerCase();
        if (!q) return [];
        var hits = [];
        function push(items, extra) {
            (items || []).forEach(function (item) {
                if (!item) return;
                var haystack = [item.title, item.description, item.author, item.category]
                    .concat(item.tags || []).join(' ').toLowerCase();
                if (haystack.indexOf(q) !== -1) {
                    hits.push({ item: item, extra: extra });
                }
            });
        }
        push(d.contentItems);
        push(d.collections, true);
        push(d.news, true);
        return hits;
    }

    /* ---------- init ---------- */
    function init() {
        setTheme(getTheme());
        renderRoleNav();
        renderAuth();
        bindAuthClicks();

        var toggleBtn = document.querySelector('.theme-toggle');
        if (toggleBtn) toggleBtn.addEventListener('click', toggleTheme);

        loadData().catch(function () { /* sin datos: la app sigue */ });
    }

    var Museo = {
        KEYS: KEYS,
        POINTS_PER_LEVEL: POINTS_PER_LEVEL,
        MAX_LEVEL: MAX_LEVEL,
        ROLE_DASH: ROLE_DASH,
        esc: esc,
        isAuthRole: isAuthRole,
        data: cachedOrLoaded,
        loadData: loadData,
        getUser: getUser,
        contributionsOf: contributionsOf,
        role: getRole(),
        setRole: setRole,
        redirectForRole: redirectForRole,
        login: login,
        logout: logout,
        theme: getTheme(),
        setTheme: setTheme,
        toggleTheme: toggleTheme,
        getFavs: getFavs,
        setFavs: setFavs,
        isFav: isFav,
        toggleFav: toggleFav,
        countFavs: countFavs,
        bindFavButtons: bindFavButtons,
        levelInfo: levelInfo,
        searchAll: searchAll,
        init: init,
    };

    global.Museo = Museo;

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})(window);