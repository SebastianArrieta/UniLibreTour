"""Revocación de JWT por ``jti`` (logout) con almacenamiento en base de datos."""

from __future__ import annotations

import time

from app.extensions import db
from app.models.token import TokenRevocado

_ULTIMA_LIMPIEZA = 0


def revocar(jti: str | None, expira: int | None) -> None:
    global _ULTIMA_LIMPIEZA
    if not jti:
        return
    try:
        if db.session.get(TokenRevocado, jti) is None:
            db.session.add(TokenRevocado(jti=jti, expira=int(expira or 0)))
            db.session.commit()
    except Exception:
        db.session.rollback()
        return
    ahora = int(time.time())
    if ahora - _ULTIMA_LIMPIEZA > 3600:
        _ULTIMA_LIMPIEZA = ahora
        limpiar_expirados()


def revocado(jti: str | None) -> bool:
    if not jti:
        return False
    try:
        fila = db.session.get(TokenRevocado, jti)
    except Exception:
        db.session.rollback()
        return False
    if fila is None:
        return False
    if fila.expira and fila.expira < int(time.time()):
        try:
            db.session.delete(fila)
            db.session.commit()
        except Exception:
            db.session.rollback()
        return False
    return True


def limpiar_expirados() -> None:
    try:
        db.session.query(TokenRevocado).filter(
            TokenRevocado.expira < int(time.time())
        ).delete(synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()
