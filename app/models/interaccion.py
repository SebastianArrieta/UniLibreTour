from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Comentario(db.Model):
    __tablename__ = "comentarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=False)
    entidad_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    entidad_id: Mapped[int] = mapped_column(Integer, nullable=False)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="comentarios")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "entidad_tipo": self.entidad_tipo,
            "entidad_id": self.entidad_id,
            "texto": self.texto,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Reaccion(db.Model):
    __tablename__ = "reacciones"

    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    entidad_tipo: Mapped[str] = mapped_column(String(50), primary_key=True)
    entidad_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="reacciones")

    def to_dict(self) -> dict:
        return {
            "usuario_id": self.usuario_id,
            "entidad_tipo": self.entidad_tipo,
            "entidad_id": self.entidad_id,
            "tipo": self.tipo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
