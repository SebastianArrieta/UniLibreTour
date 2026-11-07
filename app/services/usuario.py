from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.usuario import Usuario
from app.services.auth import hash_password


class ReglaUsuarioError(ValueError):
    """Operación rechazada por una regla de negocio sobre usuarios."""


def _hay_mas_de_un_admin_activo() -> bool:
    admins = (
        Usuario.query.filter_by(rol="admin", estado="activo")
        .with_for_update()
        .all()
    )
    return len(admins) > 1


def validar_cambio_admin(
    usuario: Usuario,
    *,
    nuevo_rol: str | None = None,
    nuevo_estado: str | None = None,
) -> None:
    """Impide dejar el sistema sin administradores activos.

    Bloquea las filas de admins (``FOR UPDATE``) para que dos bajas/degradaciones
    simultáneas no pasen ambas la comprobación.
    """
    if usuario.rol != "admin" or usuario.estado != "activo":
        return

    rol_final = usuario.rol if nuevo_rol is None else nuevo_rol
    estado_final = usuario.estado if nuevo_estado is None else nuevo_estado
    if rol_final == "admin" and estado_final == "activo":
        return
    if not _hay_mas_de_un_admin_activo():
        raise ReglaUsuarioError(
            "No puedes dejar el sistema sin administradores activos."
        )


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


def actualizar_usuario(usuario: Usuario, data: dict) -> Usuario:
    if data.get("rol") is not None:
        validar_cambio_admin(usuario, nuevo_rol=data["rol"])
    cambio_de_rol = "rol" in data and data.get("rol") != usuario.rol
    for campo in ("nombre", "email", "rol"):
        if campo in data:
            setattr(usuario, campo, data[campo])
    if cambio_de_rol:
        _invalidar_sesiones(usuario)
    db.session.commit()
    return usuario


def _invalidar_sesiones(usuario: Usuario) -> None:
    """Fuerza re-login: los JWT emitidos antes del cambio dejan de valer."""
    usuario.token_version = (usuario.token_version or 0) + 1


def _desvincular_referencias(usuario_id: int) -> None:
    """Quita las referencias al usuario sin perder el contenido del museo."""
    from app.models.contenido import Contenido, Favorito
    from app.models.cronologia import CronologiaHito, Evento
    from app.models.insignia import UsuarioInsignia
    from app.models.interaccion import Comentario, Reaccion
    from app.models.notificacion import Notificacion
    from app.models.premio import Premio, PremioParticipante
    from app.models.proyecto import Proyecto, ProyectoIntegrante
    from app.models.publicacion import HallFama, Noticia
    from app.models.semillero import Semillero

    # Contenido institucional: se conserva, solo se quita autor/revisor.
    for modelo in (Contenido, CronologiaHito, Evento, Premio, HallFama, Noticia):
        if hasattr(modelo, "creador_id"):
            db.session.query(modelo).filter(modelo.creador_id == usuario_id).update(
                {"creador_id": None}, synchronize_session=False
            )
        if hasattr(modelo, "validado_por"):
            db.session.query(modelo).filter(modelo.validado_por == usuario_id).update(
                {"validado_por": None}, synchronize_session=False
            )
        if hasattr(modelo, "docente_id"):
            db.session.query(modelo).filter(modelo.docente_id == usuario_id).update(
                {"docente_id": None}, synchronize_session=False
            )

    db.session.query(Proyecto).filter(Proyecto.docente_id == usuario_id).update(
        {"docente_id": None}, synchronize_session=False
    )
    db.session.query(Proyecto).filter(Proyecto.creador_id == usuario_id).update(
        {"creador_id": None}, synchronize_session=False
    )
    db.session.query(Semillero).filter(Semillero.lider_id == usuario_id).update(
        {"lider_id": None}, synchronize_session=False
    )

    # Filas propias del usuario: se eliminan.
    for modelo in (
        Favorito,
        Notificacion,
        Comentario,
        Reaccion,
        UsuarioInsignia,
        PremioParticipante,
        ProyectoIntegrante,
    ):
        db.session.query(modelo).filter(modelo.usuario_id == usuario_id).delete(
            synchronize_session=False
        )


def eliminar_usuario(usuario: Usuario, actor_id: int | None = None) -> dict:
    """Elimina al usuario. Si quedan referencias no previstas, lo desactiva
    en lugar de romper con un error de integridad de la base de datos."""
    if actor_id is not None and usuario.id == actor_id:
        raise ReglaUsuarioError(
            "No puedes eliminar tu propia cuenta. Pide a otro administrador que lo haga."
        )
    validar_cambio_admin(usuario, nuevo_estado="inactivo")

    usuario_id = usuario.id
    try:
        _desvincular_referencias(usuario_id)
        db.session.delete(usuario)
        db.session.commit()
        return {"eliminado": True, "mensaje": "Usuario eliminado"}
    except IntegrityError:
        db.session.rollback()
        usuario = db.session.get(Usuario, usuario_id)
        if usuario is None:
            return {"eliminado": True, "mensaje": "Usuario eliminado"}
        usuario.estado = "inactivo"
        _invalidar_sesiones(usuario)
        db.session.commit()
        return {
            "eliminado": False,
            "mensaje": "Usuario desactivado: tenía registros asociados que no se pudieron desvincular",
        }
