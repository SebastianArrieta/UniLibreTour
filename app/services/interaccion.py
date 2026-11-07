"""Interacciones del museo — comentarios reales ligados a usuario y contenido."""

from __future__ import annotations

from app.extensions import db
from app.models.interaccion import Comentario
from app.models.usuario import Usuario

ENTIDAD_CONTENIDO = "contenido"
TEXTO_MIN = 2
TEXTO_MAX = 1000


def _serializar(c: Comentario, usuario: Usuario | None = None) -> dict:
    u = usuario or db.session.get(Usuario, c.usuario_id)
    return {
        "id": c.id,
        "texto": c.texto,
        "created_at": c.created_at.isoformat() if c.created_at else None,
        "usuario": {
            "id": c.usuario_id,
            "nombre": u.nombre if u else "Usuario",
            "rol": u.rol if u else "visitante",
        },
    }


def comentarios_de(entidad_id: int, entidad_tipo: str = ENTIDAD_CONTENIDO) -> list[dict]:
    q = (
        Comentario.query.filter_by(entidad_tipo=entidad_tipo, entidad_id=entidad_id)
        .order_by(Comentario.created_at.asc(), Comentario.id.asc())
        .all()
    )
    return [_serializar(c) for c in q]


def crear_comentario(usuario: Usuario, entidad_id: int, texto: str,
                     entidad_tipo: str = ENTIDAD_CONTENIDO) -> dict:
    limpio = (texto or "").strip()
    if len(limpio) < TEXTO_MIN:
        raise ValueError("El comentario es demasiado corto")
    if len(limpio) > TEXTO_MAX:
        raise ValueError(f"El comentario supera los {TEXTO_MAX} caracteres")

    comentario = Comentario(
        usuario_id=usuario.id,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        texto=limpio,
    )
    db.session.add(comentario)
    db.session.commit()
    return _serializar(comentario, usuario)


def eliminar_comentario(usuario: Usuario, comentario_id: int) -> bool:
    comentario = db.session.get(Comentario, comentario_id)
    if comentario is None:
        return False
    if comentario.usuario_id != usuario.id and usuario.rol != "admin":
        return False
    db.session.delete(comentario)
    db.session.commit()
    return True
