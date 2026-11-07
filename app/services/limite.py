"""Rate limit persistente con ventana deslizante, compartido entre workers.

Cada evento se guarda en la tabla ``intentos_fallidos`` con su epoch, de modo
que el límite es el mismo para todos los procesos de gunicorn y sobrevive a
los reinicios (antes era un dict en memoria por proceso).
"""

from __future__ import annotations

import time

from app.extensions import db
from app.models.token import IntentoFallido


_ULTIMA_LIMPIEZA = 0


def _ahora() -> int:
    return int(time.time())


def registrar(clave: str) -> None:
    global _ULTIMA_LIMPIEZA
    try:
        db.session.add(IntentoFallido(clave=clave, ts=_ahora()))
        db.session.commit()
    except Exception:
        db.session.rollback()
        return
    # Poda periódica (como máximo una vez por hora y worker) para que la tabla
    # no crezca sin límite en procesos de larga vida.
    ahora = _ahora()
    if ahora - _ULTIMA_LIMPIEZA > 3600:
        _ULTIMA_LIMPIEZA = ahora
        limpiar_expirados()


def registrar_fallo(clave: str) -> None:
    """Compatibilidad con el flujo de login/2FA: cuenta un evento fallido."""
    registrar(clave)


def bloqueado(clave: str, maximo: int, ventana_seg: int) -> bool:
    """¿La clave alcanzó ``maximo`` eventos dentro de la ventana?"""
    desde = _ahora() - int(ventana_seg)
    try:
        total = (
            db.session.query(IntentoFallido)
            .filter(IntentoFallido.clave == clave, IntentoFallido.ts >= desde)
            .count()
        )
    except Exception:
        # Sin BD no se puede contar: no bloquear el acceso (fail-open) y avisar.
        db.session.rollback()
        return False
    return total >= int(maximo)


def limpiar(clave: str) -> None:
    try:
        db.session.query(IntentoFallido).filter(
            IntentoFallido.clave == clave
        ).delete(synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()


def limpiar_expirados(ventana_seg: int = 3600) -> None:
    try:
        db.session.query(IntentoFallido).filter(
            IntentoFallido.ts < _ahora() - int(ventana_seg)
        ).delete(synchronize_session=False)
        db.session.commit()
    except Exception:
        db.session.rollback()
