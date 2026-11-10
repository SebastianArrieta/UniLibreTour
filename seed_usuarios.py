"""Seed opcional de usuarios de prueba para UniLibreTour.

Uso (con los contenedores levantados):
    docker compose cp seed_usuarios.py server:/app/seed_usuarios.py
    docker compose exec server python seed_usuarios.py

Es idempotente: si el email ya existe, actualiza nombre, rol, estado y
contraseña; si no existe, lo crea. Las contraseñas se guardan con el mismo
hash de Werkzeug que usa la aplicación.
"""

from app import create_app
from app.extensions import db
from app.models.usuario import Usuario
from app.services.auth import hash_password

USUARIOS = [
    {"nombre": "Administrador", "email": "admin@unilibretour.edu.co", "password": "admin123", "rol": "admin"},
    {"nombre": "Visitante Demo", "email": "estudiante@unilibretour.edu.co", "password": "visitante123", "rol": "visitante"},
    {"nombre": "Estudiante Demo", "email": "estudiante@unilibre.edu.co", "password": "123456", "rol": "estudiante"},
    {"nombre": "Docente Demo", "email": "docente@unilibre.edu.co", "password": "123456", "rol": "docente"},
    {"nombre": "Administrador Alterno", "email": "admin@unilibre.edu.co", "password": "123456", "rol": "admin"},
    {"nombre": "Egresado Demo", "email": "egresado@unilibre.edu.co", "password": "123456", "rol": "egresado"},
]


def main() -> None:
    app = create_app()
    with app.app_context():
        creados = 0
        actualizados = 0
        for datos in USUARIOS:
            email = datos["email"].strip().lower()
            usuario = Usuario.query.filter_by(email=email).first()
            if usuario is None:
                usuario = Usuario(
                    nombre=datos["nombre"],
                    email=email,
                    password_hash=hash_password(datos["password"]),
                    rol=datos["rol"],
                    estado="activo",
                )
                db.session.add(usuario)
                creados += 1
                print(f"[creado]     {email} ({datos['rol']})")
            else:
                usuario.nombre = datos["nombre"]
                usuario.password_hash = hash_password(datos["password"])
                usuario.rol = datos["rol"]
                usuario.estado = "activo"
                usuario.token_version = (usuario.token_version or 0) + 1
                actualizados += 1
                print(f"[actualizado] {email} ({datos['rol']})")
        db.session.commit()
        print(f"\nListo: {creados} creados, {actualizados} actualizados.")


if __name__ == "__main__":
    main()
