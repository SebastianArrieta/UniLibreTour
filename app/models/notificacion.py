from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Notificacion(db.Model):
    __tablename__ = "notificaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    mensaje: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    referencia_tipo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    referencia_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    leido: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="notificaciones")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "mensaje": self.mensaje,
            "tipo": self.tipo,
            "referencia_tipo": self.referencia_tipo,
            "referencia_id": self.referencia_id,
            "leido": self.leido,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
