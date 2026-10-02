from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Premio(db.Model):
    __tablename__ = "premios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    anio: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    lugar: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="borrador", nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validado_por: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_validacion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    creador_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    creador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[creador_id], back_populates=None)
    validador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[validado_por], back_populates=None)
    participantes: Mapped[list["PremioParticipante"]] = relationship("PremioParticipante", back_populates="premio")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "anio": self.anio,
            "lugar": self.lugar,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "observaciones": self.observaciones,
            "validado_por": self.validado_por,
            "fecha_validacion": self.fecha_validacion.isoformat() if self.fecha_validacion else None,
            "creador_id": self.creador_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PremioParticipante(db.Model):
    __tablename__ = "premio_participantes"

    premio_id: Mapped[int] = mapped_column(Integer, ForeignKey("premios.id"), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), primary_key=True)

    # Relationships
    premio: Mapped["Premio"] = relationship("Premio", back_populates="participantes")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="premios_como_participante")

    def to_dict(self) -> dict:
        return {"premio_id": self.premio_id, "usuario_id": self.usuario_id}
