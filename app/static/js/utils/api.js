/* ============================================================================
   UniLibreTour — Módulo Cliente API (api.js)
   Configuración base de la API, headers y autorización con Bearer token.
   
   Flujo de peticiones:
   1. Construcción de Headers (Content-Type, Accept, Authorization Bearer).
   2. Petición HTTP Asíncrona (async/await) con manejo de métodos:
      - GET: Consultar recursos.
      - POST: Enviar o guardar recursos.
      - PUT: Actualizar recursos existentes.
      - DELETE: Eliminar recursos.
   3. Manejo de Errores con try/catch para capturar excepciones del servidor.
   ============================================================================ */

(function (global) {
    'use strict';

    var TOKEN_KEY = 'museo-token';

    function getToken() {
        try {
            return JSON.parse(localStorage.getItem(TOKEN_KEY));
        } catch (e) {
            return localStorage.getItem(TOKEN_KEY);
        }
    }

    /**
     * Realiza una petición asíncrona hacia el backend Flask.
     * @param {string} url - Ruta del endpoint (ej. /api/auth/login)
     * @param {string} method - Método HTTP (GET, POST, PUT, DELETE)
     * @param {object|null} body - Datos a enviar en el payload (JSON)
     * @param {string|null} customToken - Token opcional (si no se pasa, lee del localStorage)
     * @returns {Promise<any>} Datos devueltos por el backend
     */
    async function request(url, method = 'GET', body = null, customToken = null) {
        const token = customToken || getToken();
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const options = {
            method: method.toUpperCase(),
            headers: headers,
        };

        if (body && ['POST', 'PUT', 'PATCH'].includes(options.method)) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);
            const json = await response.json().catch(() => ({}));

            if (!response.ok || json.ok === false) {
                // RNF de Seguridad: Si el token expiró o es inválido (401), invalidar sesión
                if (response.status === 401 && token) {
                    console.warn('[API Auth] Sesión caducada o inválida (401). Limpiando credenciales...');
                    localStorage.removeItem(TOKEN_KEY);
                    localStorage.removeItem('museo-usuario');
                    localStorage.removeItem('museo-rol');
                    if (window.UI && typeof UI.toast === 'function') {
                        UI.toast('Tu sesión ha expirado. Por favor ingresa nuevamente.', 'err');
                    }
                }

                let errorMsg = json.error || `Error ${response.status}: ${response.statusText}`;
                if (typeof errorMsg === 'object') {
                    // Si viene un diccionario de validación de Marshmallow
                    errorMsg = Object.entries(errorMsg)
                        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`)
                        .join(' | ');
                }
                const error = new Error(errorMsg);
                error.status = response.status;
                error.data = json;
                throw error;
            }

            return json.data !== undefined ? json.data : json;
        } catch (err) {
            // Captura de excepción para registrar y relanzar con mensaje legible
            console.error(`[API Error] ${method} ${url}:`, err.message);
            throw err;
        }
    }

    const API = {
        getToken: getToken,
        request: request,
        get: (url, token) => request(url, 'GET', null, token),
        post: (url, data, token) => request(url, 'POST', data, token),
        put: (url, data, token) => request(url, 'PUT', data, token),
        delete: (url, token) => request(url, 'DELETE', null, token),
    };

    global.API = API;
})(window);

