"""Tokens JWT revocados (logout) y límites de intentos persistentes."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class TokenRevocado(db.Model):
    __tablename__ = "tokens_revocados"

    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    expira: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )


class IntentoFallido(db.Model):
    """Eventos contados por la ventana deslizante del rate limit.

    ``ts`` es epoch en segundos: funciona igual en SQLite y MySQL y es
    consistente entre los workers de gunicorn (a diferencia del estado en
    memoria de un solo proceso).
    """

    __tablename__ = "intentos_fallidos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    clave: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    ts: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
