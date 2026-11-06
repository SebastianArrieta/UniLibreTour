from app.extensions import db
from app.models.notificacion import Notificacion


def listar(usuario_id: int) -> list[Notificacion]:
    return (
        Notificacion.query.filter_by(usuario_id=usuario_id)
        .order_by(Notificacion.created_at.desc(), Notificacion.id.desc())
        .all()
    )


def crear(usuario_id: int, mensaje: str, tipo: str | None = None,
          referencia_tipo: str | None = None, referencia_id: int | None = None) -> Notificacion:
    notificacion = Notificacion(
        usuario_id=usuario_id,
        mensaje=mensaje[:255],
        tipo=tipo,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
    )
    db.session.add(notificacion)
    return notificacion


def marcar(usuario_id: int, notificacion_id: int, leido: bool | None) -> Notificacion | None:
    notificacion = Notificacion.query.filter_by(
        id=notificacion_id, usuario_id=usuario_id
    ).first()
    if notificacion is None:
        return None
    notificacion.leido = not bool(notificacion.leido) if leido is None else bool(leido)
    db.session.commit()
    return notificacion


def marcar_todas(usuario_id: int) -> int:
    actualizadas = (
        Notificacion.query.filter_by(usuario_id=usuario_id, leido=False)
        .update({"leido": True}, synchronize_session=False)
    )
    db.session.commit()
    return actualizadas
