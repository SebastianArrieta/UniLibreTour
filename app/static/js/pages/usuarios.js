document.getElementById("userForm").addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = {
        nombre: document.getElementById("nombre").value,
        email: document.getElementById("email").value,
        password: document.getElementById("password").value,
        rol: document.getElementById("rol").value,
    };

    try {
        const res = await fetch("/api/usuarios", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData),
        });

        if (res.ok) {
            window.location.reload();
            return;
        }

        const err = await res.json();
        alert("Error: " + (typeof err.error === "string" ? err.error : "No se pudo crear el usuario"));
    } catch (error) {
        alert("Error al conectar con el servidor: " + error.message);
    }
});
