"""Favoritos persistentes por usuario (tabla favoritos)."""

from __future__ import annotations

from app.extensions import db
from app.models.contenido import Contenido, Favorito
from app.services import museo


def ids_de(usuario_id: int) -> list[int]:
    filas = (
        Favorito.query.filter_by(usuario_id=usuario_id)
        .order_by(Favorito.created_at.desc())
        .all()
    )
    return [f.contenido_id for f in filas]


def listar_contenidos(usuario_id: int) -> list[dict]:
    """Favoritos en la forma del contrato del museo (para las tarjetas)."""
    ids = ids_de(usuario_id)
    mapa = {int(c["id"]): c for c in museo.contenidos()}
    return [mapa[i] for i in ids if i in mapa]


def alternar(usuario_id: int, contenido_id: int) -> tuple[bool, list[int]]:
    existente = db.session.get(Favorito, (usuario_id, contenido_id))
    if existente:
        db.session.delete(existente)
        activo = False
    else:
        db.session.add(Favorito(usuario_id=usuario_id, contenido_id=contenido_id))
        activo = True
    db.session.commit()
    return activo, ids_de(usuario_id)


def quitar(usuario_id: int, contenido_id: int) -> list[int]:
    existente = db.session.get(Favorito, (usuario_id, contenido_id))
    if existente:
        db.session.delete(existente)
        db.session.commit()
    return ids_de(usuario_id)


def limpiar(usuario_id: int) -> None:
    Favorito.query.filter_by(usuario_id=usuario_id).delete()
    db.session.commit()


def existe_contenido(contenido_id: int) -> bool:
    return db.session.get(Contenido, contenido_id) is not None
