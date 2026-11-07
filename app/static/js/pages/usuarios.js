/* ============================================================================
   UniLibreTour — Módulo de Gestión de Usuarios (usuarios.js)
   Demostración de flujo asíncrono (async / await) y manejo de errores (try / catch).
   
   Flujo:
   Botón Modal -> Formulario submit -> async/await fetch -> Blueprint /api/usuarios
   -> Controller crear() -> UsuarioCreateSchema -> Modelo Usuario -> MySQL
   ============================================================================ */

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("modal-nuevo-usuario");
    const openBtn = document.getElementById("btn-open-modal");
    const closeBtn = document.getElementById("btn-close-modal");
    const cancelBtn = document.getElementById("btn-cancel-modal");
    const form = document.getElementById("userForm");
    const errorBox = document.getElementById("userform-error");
    const submitBtn = document.getElementById("btn-submit-user");

    function openModal() {
        if (!modal) return;
        if (errorBox) errorBox.classList.add("hidden");
        if (window.UI && UI.openModal) {
            UI.openModal(modal);
        } else {
            modal.classList.remove("hidden");
        }
    }

    function closeModal() {
        if (!modal) return;
        if (window.UI && UI.closeModal) {
            UI.closeModal(modal);
        } else {
            modal.classList.add("hidden");
        }
        form?.reset();
        if (errorBox) errorBox.classList.add("hidden");
    }

    if (openBtn) openBtn.addEventListener("click", openModal);
    if (closeBtn) closeBtn.addEventListener("click", closeModal);
    if (cancelBtn) cancelBtn.addEventListener("click", closeModal);

    if (!form) return;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();

        // 1. Obtención de valores desde los inputs con document.getElementById().value
        const formData = {
            nombre: document.getElementById("nombre").value.trim(),
            email: document.getElementById("email").value.trim().toLowerCase(),
            password: document.getElementById("password").value,
            rol: document.getElementById("rol").value,
        };

        if (errorBox) errorBox.classList.add("hidden");
        const originalBtnText = submitBtn.innerHTML;
        if (window.UI && UI.setBusy) {
            UI.setBusy(submitBtn, true, "Guardando…");
        } else {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Guardando...';
        }

        // 2. Manejador de errores try/catch para capturar excepciones
        try {
            // Petición HTTP POST asíncrona hacia el Blueprint 'usuarios' (Bearer JWT)
            const token = window.Museo && typeof Museo.getToken === "function" ? Museo.getToken() : null;
            const headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            };
            if (token) headers["Authorization"] = "Bearer " + token;

            const res = await fetch("/api/usuarios", {
                method: "POST",
                headers: headers,
                body: JSON.stringify(formData),
            });

            const data = await res.json().catch(() => ({}));

            // 3. Verificación de códigos de estado HTTP (200 / 201)
            if (res.ok && data.ok !== false) {
                closeModal();
                if (window.UI && typeof UI.toast === "function") {
                    UI.toast("¡Usuario creado y guardado en la base de datos!", "success");
                }
                // Recarga para reflejar el nuevo registro en la tabla
                setTimeout(() => {
                    window.location.reload();
                }, 800);
                return;
            }

            // Manejo de error de validación (Código 400 Bad Request)
            let msg = data.error || "No se pudo registrar el usuario.";
            if (typeof msg === "object") {
                msg = Object.entries(msg).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`).join(" | ");
            }

            if (errorBox) {
                errorBox.textContent = msg;
                errorBox.classList.remove("hidden");
            } else if (window.UI && typeof UI.toast === "function") {
                UI.toast(msg, "err");
            }
        } catch (error) {
            const netMsg = "Error al conectar con el servidor: " + error.message;
            if (errorBox) {
                errorBox.textContent = netMsg;
                errorBox.classList.remove("hidden");
            } else if (window.UI && typeof UI.toast === "function") {
                UI.toast(netMsg, "err");
            }
        } finally {
            if (window.UI && UI.setBusy) {
                UI.setBusy(submitBtn, false);
            } else {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        }
    });
});
