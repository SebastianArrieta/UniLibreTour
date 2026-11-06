from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.usuario import Usuario
from app.services.auth import hash_password
from app.services.cuentas import CUENTAS_DEMO


def listar_usuarios() -> list[Usuario]:
    return Usuario.query.order_by(Usuario.id.asc()).all()


def obtener_usuario(usuario_id: int) -> Usuario | None:
    return db.session.get(Usuario, usuario_id)


def obtener_por_email(email: str) -> Usuario | None:
    return Usuario.query.filter_by(email=email).first()


def crear_usuario(data: dict) -> Usuario:
    usuario = Usuario(
        nombre=data["nombre"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
        rol=data.get("rol", "visitante"),
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


def registrar_usuario(data: dict) -> Usuario:
    """Alta pública (registro): queda pendiente de aprobación del administrador."""
    usuario = Usuario(
        nombre=data["nombre"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
        rol=data.get("rol", "estudiante"),
        estado="pendiente",
    )
    db.session.add(usuario)
    db.session.commit()
    return usuario


def actualizar_usuario(usuario: Usuario, data: dict) -> Usuario:
    for campo in ("nombre", "email", "rol"):
        if campo in data:
            setattr(usuario, campo, data[campo])
    db.session.commit()
    return usuario


def eliminar_usuario(usuario: Usuario) -> None:
    db.session.delete(usuario)
    db.session.commit()


def seed_usuarios() -> None:
    """Crea las cuentas demo canónicas que ya no existan (idempotente por email)."""
    existentes = {u.email for u in Usuario.query.all()}
    nuevas = [
        Usuario(
            nombre=f"{cuenta['etiqueta']} Demo",
            email=cuenta["email"],
            password_hash=hash_password(cuenta["password"]),
            rol=cuenta["rol"],
        )
        for cuenta in CUENTAS_DEMO
        if cuenta["email"] not in existentes
    ]
    if not nuevas:
        return

    try:
        db.session.add_all(nuevas)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
