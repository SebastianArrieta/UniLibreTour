from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class CronologiaHito(db.Model):
    __tablename__ = "cronologia_hitos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    anio: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tipo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "anio": self.anio,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "estado": self.estado,
            "observaciones": self.observaciones,
            "validado_por": self.validado_por,
            "fecha_validacion": self.fecha_validacion.isoformat() if self.fecha_validacion else None,
            "creador_id": self.creador_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Evento(db.Model):
    __tablename__ = "eventos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    fecha: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Date stored as string
    hora: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)   # Time stored as string HH:MM
    ubicacion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    tipo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "fecha": self.fecha,
            "hora": self.hora,
            "ubicacion": self.ubicacion,
            "tipo": self.tipo,
            "descripcion": self.descripcion,
            "estado": self.estado,
            "observaciones": self.observaciones,
            "validado_por": self.validado_por,
            "fecha_validacion": self.fecha_validacion.isoformat() if self.fecha_validacion else None,
            "creador_id": self.creador_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
