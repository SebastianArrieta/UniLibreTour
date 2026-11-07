/* ============================================================================
   UniLibreTour — App shell (DataContext + Layout + Auth).
   Estado global institucional y sesión de usuario.

   API global: window.Museo
   Estado (claves localStorage):
     museo-theme   : 'dark' | 'light'
     museo-rol     : Role  ('visitante' por defecto)
     museo-favs    : string[] ids de contenido favorito
     museo-datos-v2: snapshot del dataset (cache de /api/museo/data)
     museo-perfil  : objeto con preferencias del usuario (opcional)

   Datos:
     Museo.loadData()          -> Promise<Object> (fetch /api/museo/data, cachea)
     Museo.data()              -> dataset actual (null hasta cargar)
     Museo.getUser()           -> Promise<User|undefined> (demo por rol)
     Museo.getContributions(pt) -> filtro de aportes (author/submittedBy)

   Estado / sesión:
     Museo.role                -> rol actual (string)
     Museo.login(role)         -> persiste rol y redirige al dashboard
     Museo.logout()            -> limpia rol y redirige a '/'
     Museo.redirectForRole(role)

   Header dinámico (apunta al HTML del partial header.html):
     #museo-auth-area  -> "Ingresar" | (píldora "Mi espacio" + menú de cuenta)

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
        DATA: 'museo-datos-v2',
        TOKEN: 'museo-token',
        USUARIO: 'museo-usuario',
        PEND_TOKEN: 'museo-pending-token',
        PEND_USUARIO: 'museo-pending-usuario',
    };

    var DATA_ENDPOINT = '/api/museo/data';
    var POINTS_PER_LEVEL = 500;
    var MAX_LEVEL = 20;

    var ROLE_HOME = {
        estudiante: '/estudiante',
        egresado: '/egresado',
        docente: '/docente',
        admin: '/admin',
        visitante: '/',
    };

    /* Mismo estilo (rojo) para todos los roles; solo cambian etiqueta, ruta e icono. */
    var DASH_STYLE = {
        color: 'var(--primary)',
        bg: 'var(--primary-soft)',
        border: 'var(--primary-border)',
        activeBg: 'var(--primary-solid)',
        activeBorder: 'var(--primary-solid)',
    };
    function dashEntry(label, href, icon) {
        return {
            label: label, href: href, icon: icon,
            color: DASH_STYLE.color, bg: DASH_STYLE.bg, border: DASH_STYLE.border,
            activeBg: DASH_STYLE.activeBg, activeBorder: DASH_STYLE.activeBorder,
        };
    }
    var ROLE_DASH = {
        admin: dashEntry('Panel Admin', '/admin', 'fa-solid fa-gauge-high'),
        docente: dashEntry('Mi Espacio Docente', '/docente', 'fa-solid fa-chalkboard-user'),
        estudiante: dashEntry('Mi Espacio', '/estudiante', 'fa-solid fa-graduation-cap'),
        egresado: dashEntry('Mi Espacio', '/egresado', 'fa-solid fa-user-tie'),
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
            .then(function (r) { if (!r.ok) throw new Error('museo-data ' + r.status); return r.json(); })
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

    function getUserPorRol() {
        return loadData().then(function (d) {
            return (d.users || []).find(function (x) {
                return x.email === USER_EMAIL[Museo.role];
            });
        });
    }

    function getUser() {
        var tok = lsGet(KEYS.TOKEN);
        if (!tok) return getUserPorRol();
        return apiJson('/api/auth/me', 'GET', null, tok).then(function (u) {
            if (u) lsSet(KEYS.USUARIO, u);
            return u || lsGet(KEYS.USUARIO) || getUserPorRol();
        }).catch(function () {
            return lsGet(KEYS.USUARIO) || getUserPorRol();
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
        var oscuro = theme === 'dark';
        btn.setAttribute('aria-checked', oscuro ? 'true' : 'false');
        btn.title = oscuro ? 'Modo oscuro — cambiar a claro' : 'Modo claro — cambiar a oscuro';
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
        function limpiarYRedirigir() {
            lsRemove(KEYS.ROLE);
            lsRemove(KEYS.FAVS);
            lsRemove(KEYS.TOKEN);
            lsRemove(KEYS.USUARIO);
            lsRemove(KEYS.PEND_TOKEN);
            lsRemove(KEYS.PEND_USUARIO);
            try {
                localStorage.removeItem('museo-pending-role');
                localStorage.removeItem('museo-pending-email');
                localStorage.removeItem('museo-pending-devcode');
            } catch (e) { /* noop */ }

            if (window.UI && typeof UI.toast === 'function') {
                UI.toast('Sesión cerrada con éxito. Redirigiendo...', 'info');
            }
            setTimeout(function () {
                window.location.href = '/';
            }, 400);
        }

        // Invalida también la cookie de sesión httpOnly en el servidor.
        try {
            fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin' })
                .then(limpiarYRedirigir)
                .catch(limpiarYRedirigir);
        } catch (e) {
            limpiarYRedirigir();
        }
    }

    /* ---------- sesión real (JWT) ---------- */
    function apiJson(url, method, body, token) {
        if (window.API && typeof window.API.request === 'function') {
            return window.API.request(url, method, body, token);
        }
        var headers = { 'Content-Type': 'application/json', Accept: 'application/json' };
        if (token) headers.Authorization = 'Bearer ' + token;
        return fetch(url, {
            method: method,
            headers: headers,
            body: body ? JSON.stringify(body) : undefined,
        }).then(function (r) {
            return r.json().catch(function () { return {}; }).then(function (j) {
                if (!r.ok || j.ok === false) {
                    var msg = j.error;
                    if (msg && typeof msg === 'object') msg = 'Datos inválidos en el formulario';
                    var err = new Error(msg || ('Error ' + r.status));
                    err.status = r.status;
                    throw err;
                }
                return j.data;
            });
        });
    }

    function isAuthenticated() { return !!lsGet(KEYS.TOKEN); }
    function getToken() { return lsGet(KEYS.TOKEN); }
    function getSesion() { return lsGet(KEYS.USUARIO); }

    /* Login: Valida credenciales contra el backend.
       Si la cuenta tiene 2FA activo, el servidor NO entrega sesión: devuelve un
       token de desafío y el código debe verificarse en /api/auth/2fa/verify. */
    function iniciarSesion(email, password) {
        return apiJson('/api/auth/login', 'POST', { email: email, password: password })
            .then(function (data) {
                var usuario = data.usuario || {};

                if (data.requires_2fa) {
                    lsSet(KEYS.PEND_TOKEN, data.pending_token);
                    lsSet(KEYS.PEND_USUARIO, usuario);
                    try {
                        localStorage.setItem('museo-pending-role', usuario.rol || 'estudiante');
                        localStorage.setItem('museo-pending-email', usuario.email || email);
                        if (data.dev_code) {
                            localStorage.setItem('museo-pending-devcode', data.dev_code);
                        }
                    } catch (e) { /* noop */ }
                    return { requires2FA: true, usuario: usuario };
                }

                var token = data.access_token;
                lsSet(KEYS.TOKEN, token);
                lsSet(KEYS.USUARIO, usuario);
                var rol = usuario.rol || 'visitante';
                Museo.role = rol;
                setRole(rol);
                var dest = ROLE_HOME[rol] || '/';
                return { requires2FA: false, usuario: usuario, redirectUrl: dest };
            });
    }

    /* Paso 2 (2fa.html): el servidor ya validó el código y entregó la sesión. */
    function completarInicioSesion(data) {
        if (!data || !data.access_token) {
            window.location.href = '/login';
            return;
        }
        lsSet(KEYS.TOKEN, data.access_token);
        lsSet(KEYS.USUARIO, data.usuario || null);
        lsRemove(KEYS.PEND_TOKEN);
        lsRemove(KEYS.PEND_USUARIO);
        try {
            localStorage.removeItem('museo-pending-role');
            localStorage.removeItem('museo-pending-email');
            localStorage.removeItem('museo-pending-devcode');
        } catch (e) { /* noop */ }
        var rol = (data.usuario && data.usuario.rol) || getRole();
        Museo.role = rol;
        setRole(rol);
        redirectForRole(rol);
    }

    /* registro.html: el alta queda pendiente de aprobación, sin sesión. */
    function registrarse(nombre, email, password, rol) {
        return apiJson('/api/auth/register', 'POST', {
            nombre: nombre, email: email, password: password, rol: rol,
        }).then(function (data) {
            return data.usuario || data;
        });
    }

    /* estudiante_contribuir / docente_evidencia: aporte → cola de validación. */
    function crearContenido(payload) {
        if (!isAuthenticated()) {
            window.location.href = '/login';
            return Promise.reject(new Error('Inicia sesión para aportar'));
        }
        return apiJson('/api/museo/contenidos', 'POST', payload, getToken());
    }

    /* ---------- header dinámico ---------- */
    function pathActive(href) {
        var p = window.location.pathname;
        if (href === '/') return p === '/';
        return p === href || p.indexOf(href + '/') === 0;
    }

    var ROLE_LABEL = {
        admin: 'Administrador',
        docente: 'Docente',
        estudiante: 'Estudiante',
        egresado: 'Egresado',
        visitante: 'Visitante',
    };

    function iniciales(nombre) {
        var partes = String(nombre || '').trim().split(/\s+/).filter(Boolean);
        if (!partes.length) return '?';
        if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
        return (partes[0].charAt(0) + partes[partes.length - 1].charAt(0)).toUpperCase();
    }

    function closeUserMenu(devolverFoco) {
        var menu = document.getElementById('museo-user-menu');
        var btn = document.querySelector('[data-action="user-menu"]');
        if (!menu || menu.hasAttribute('hidden')) return;
        menu.setAttribute('hidden', '');
        if (btn) {
            btn.setAttribute('aria-expanded', 'false');
            if (devolverFoco) btn.focus();
        }
    }

    function toggleUserMenu() {
        var menu = document.getElementById('museo-user-menu');
        var btn = document.querySelector('[data-action="user-menu"]');
        if (!menu || !btn) return;
        if (!menu.hasAttribute('hidden')) {
            closeUserMenu(true);
            return;
        }
        menu.removeAttribute('hidden');
        btn.setAttribute('aria-expanded', 'true');
        var primero = menu.querySelector('[role="menuitem"]');
        if (primero) primero.focus();
    }

    function renderAuth() {
        var area = document.getElementById('museo-auth-area');
        if (!area) return;
        var role = Museo.role;
        if (!isAuthRole(role)) {
            area.innerHTML = '<a href="/login" class="text-sm px-4 py-1.5 rounded btn-primary btn-float">Ingresar</a>';
            return;
        }

        function pintarMenu(me) {
            var nombre = (me && me.name) || role;
            var rolLabel = ROLE_LABEL[role] || role;
            var ini = iniciales(nombre);
            var dash = ROLE_DASH[role];
            var dashPill = '';
            if (dash) {
                var activo = pathActive(dash.href);
                dashPill =
                    '<a href="' + esc(dash.href) + '" class="museo-dash-pill' + (activo ? ' is-active' : '') + '"' +
                    (activo ? ' aria-current="page"' : '') +
                    ' title="' + esc(dash.label) + '">' +
                    '<i class="' + dash.icon + '" aria-hidden="true"></i>' +
                    '<span class="museo-dash-label">' + esc(dash.label) + '</span>' +
                    '</a>';
            }

            area.innerHTML = dashPill +
                '<div class="museo-user-menu-wrap">' +
                    '<button type="button" class="museo-user-btn" data-action="user-menu" aria-haspopup="menu" aria-expanded="false" aria-controls="museo-user-menu" title="Abrir menú de cuenta">' +
                        '<span class="museo-user-avatar" aria-hidden="true">' + esc(ini) + '</span>' +
                        '<span class="museo-user-name">' + esc(nombre) + '</span>' +
                        '<i class="fa-solid fa-chevron-down museo-user-caret" aria-hidden="true"></i>' +
                    '</button>' +
                    '<div id="museo-user-menu" class="museo-user-menu" role="menu" aria-label="Cuenta" hidden>' +
                        '<div class="museo-user-menu-head">' +
                            '<span class="museo-user-avatar museo-user-avatar-lg" aria-hidden="true">' + esc(ini) + '</span>' +
                            '<div class="museo-user-menu-id">' +
                                '<div class="museo-user-menu-name">' + esc(nombre) + '</div>' +
                                '<div class="museo-user-menu-role">' + esc(rolLabel) + '</div>' +
                            '</div>' +
                        '</div>' +
                        '<a role="menuitem" href="/perfil" class="museo-user-item">' +
                            '<i class="fa-regular fa-user" aria-hidden="true"></i><span>Mi perfil</span></a>' +
                        '<div class="museo-user-menu-sep" role="separator"></div>' +
                        '<button type="button" role="menuitem" data-action="logout" class="museo-user-item museo-user-item-danger">' +
                            '<i class="fa-solid fa-arrow-right-from-bracket" aria-hidden="true"></i><span>Cerrar sesión</span></button>' +
                    '</div>' +
                '</div>';
        }

        getUser().then(pintarMenu).catch(function () { pintarMenu(null); });
    }

    function showLogoutModal() {
        var m = document.getElementById('modal-confirm-logout');
        if (!m) return;
        if (window.UI && UI.openModal) {
            UI.openModal(m);
        } else {
            m.classList.remove('hidden');
            m.style.display = 'flex';
        }
    }

    function hideLogoutModal() {
        var m = document.getElementById('modal-confirm-logout');
        if (!m || m.classList.contains('hidden')) return;
        if (window.UI && UI.closeModal) {
            UI.closeModal(m);
        } else {
            m.classList.add('hidden');
            m.style.display = 'none';
        }
    }

    function bindAuthClicks() {
        document.addEventListener('click', function (e) {
            var t = e.target && e.target.closest ? e.target.closest('[data-action]') : null;

            if (t && t.getAttribute('data-action') === 'user-menu') {
                e.preventDefault();
                toggleUserMenu();
                return;
            }

            var dentroDelMenu = e.target && e.target.closest ? e.target.closest('.museo-user-menu-wrap') : null;
            if (!dentroDelMenu) closeUserMenu(false);

            if (t && t.getAttribute('data-action') === 'logout') {
                e.preventDefault();
                closeUserMenu(false);
                showLogoutModal();
                return;
            }

            if (e.target && e.target.id === 'btn-cancel-logout') {
                e.preventDefault();
                hideLogoutModal();
                return;
            }

            if (e.target && (e.target.id === 'btn-confirm-logout' || (e.target.closest && e.target.closest('#btn-confirm-logout')))) {
                e.preventDefault();
                var btn = document.getElementById('btn-confirm-logout');
                if (btn) {
                    btn.disabled = true;
                    btn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Saliendo...';
                }
                Museo.logout();
                return;
            }

            var modal = document.getElementById('modal-confirm-logout');
            if (modal && e.target === modal) {
                hideLogoutModal();
            }
        });

        // RNF: Accesibilidad - Tecla ESC para cerrar menús y modales
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                closeUserMenu(true);
                hideLogoutModal();
                var userModal = document.getElementById('modal-nuevo-usuario');
                if (userModal) userModal.classList.add('hidden');
                return;
            }

            var menu = document.getElementById('museo-user-menu');
            if (!menu || menu.hasAttribute('hidden')) return;
            if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
            var items = Array.prototype.slice.call(menu.querySelectorAll('[role="menuitem"]'));
            if (!items.length) return;
            e.preventDefault();
            var actual = items.indexOf(document.activeElement);
            var siguiente = e.key === 'ArrowDown'
                ? (actual + 1) % items.length
                : (actual - 1 + items.length) % items.length;
            items[siguiente].focus();
        });
    }

    /* ---------- favoritos (persistentes por usuario) ---------- */
    function getFavs() {
        var v = lsGet(KEYS.FAVS);
        return Array.isArray(v) ? v.map(String) : [];
    }
    function setFavs(list) { lsSet(KEYS.FAVS, (list || []).map(String)); }
    function isFav(id) { return getFavs().indexOf(String(id)) !== -1; }
    function countFavs() { return getFavs().length; }

    function sincronizarFavs() {
        if (!isAuthenticated()) return Promise.resolve(getFavs());
        return apiJson('/api/museo/favoritos', 'GET', null, getToken())
            .then(function (data) {
                var ids = (data && data.ids) || [];
                setFavs(ids);
                return ids;
            })
            .catch(function () { return getFavs(); });
    }

    function toggleFav(id) {
        var sid = String(id);
        var estaba = isFav(sid);
        var list = getFavs();
        if (estaba) list.splice(list.indexOf(sid), 1);
        else list.push(sid);
        setFavs(list);

        if (isAuthenticated()) {
            apiJson('/api/museo/favoritos/' + encodeURIComponent(sid), 'POST', {}, getToken())
                .then(function (data) {
                    if (data && data.ids) setFavs(data.ids);
                })
                .catch(function () {
                    // revertir el cambio optimista
                    var actuales = getFavs();
                    var idx = actuales.indexOf(sid);
                    if (estaba && idx === -1) actuales.push(sid);
                    if (!estaba && idx !== -1) actuales.splice(idx, 1);
                    setFavs(actuales);
                    if (window.UI && UI.toast) UI.toast('No se pudo guardar el favorito', 'err');
                });
        }
        return getFavs();
    }

    function pintarFavBtn(btn, id) {
        var on = isFav(id);
        btn.setAttribute('aria-pressed', on ? 'true' : 'false');
        btn.classList.toggle('is-fav', on);
        var icon = btn.querySelector('[data-fav-icon]');
        if (icon) {
            icon.innerHTML = on
                ? '<i class="fa-solid fa-heart" style="color:var(--primary)"></i>'
                : '<i class="fa-regular fa-heart"></i>';
        }
    }

    function pedirSesionParaFavorito() {
        var destino = window.location.pathname + window.location.search;
        if (window.UI && UI.toast) UI.toast('Inicia sesión para guardar en favoritos', 'info');
        setTimeout(function () {
            window.location.href = '/login?next=' + encodeURIComponent(destino);
        }, 700);
    }

    function bindFavButtons(root, onChanged) {
        root = root || document;
        var botones = Array.prototype.slice.call(root.querySelectorAll('.fav-toggle'));
        botones.forEach(function (btn) {
            var id = btn.getAttribute('data-id');
            if (!id) return;
            pintarFavBtn(btn, id);
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                e.stopPropagation();
                if (!isAuthenticated() || !isAuthRole(getRole())) {
                    pedirSesionParaFavorito();
                    return;
                }
                toggleFav(id);
                pintarFavBtn(btn, id);
                if (typeof onChanged === 'function') onChanged(countFavs());
            });
        });
        if (botones.length && isAuthenticated()) {
            sincronizarFavs().then(function () {
                botones.forEach(function (btn) { pintarFavBtn(btn, btn.getAttribute('data-id')); });
                if (typeof onChanged === 'function') onChanged(countFavs());
            });
        }
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
    /* Imágenes rotas (URL caída): se ocultan para que se vea el fondo neutro
       del contenedor en vez del icono roto y el texto alternativo. */
    function ocultarImagenRota(img) { img.style.visibility = 'hidden'; }
    function vigilarImagenes() {
        document.addEventListener('error', function (e) {
            if (e.target && e.target.tagName === 'IMG') ocultarImagenRota(e.target);
        }, true);
        Array.prototype.forEach.call(document.images, function (img) {
            if (img.complete && img.naturalWidth === 0 && img.getAttribute('src')) ocultarImagenRota(img);
        });
    }

    function init() {
        vigilarImagenes();
        setTheme(getTheme());
        renderAuth();
        bindAuthClicks();

        var toggleBtn = document.querySelector('.theme-toggle');
        if (toggleBtn) toggleBtn.addEventListener('click', toggleTheme);

        if (isAuthenticated()) sincronizarFavs();
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
        apiJson: apiJson,
        isAuthenticated: isAuthenticated,
        getToken: getToken,
        getSesion: getSesion,
        iniciarSesion: iniciarSesion,
        completarInicioSesion: completarInicioSesion,
        registrarse: registrarse,
        crearContenido: crearContenido,
        getTheme: getTheme,
        setTheme: setTheme,
        toggleTheme: toggleTheme,
        getFavs: getFavs,
        setFavs: setFavs,
        isFav: isFav,
        toggleFav: toggleFav,
        countFavs: countFavs,
        sincronizarFavs: sincronizarFavs,
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