from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Proyecto(db.Model):
    __tablename__ = "proyectos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    anio: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    linea_investigacion: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    docente_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tecnologias: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resultados_impacto: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    docente: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[docente_id], back_populates=None)
    creador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[creador_id], back_populates=None)
    validador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[validado_por], back_populates=None)
    integrantes: Mapped[list["ProyectoIntegrante"]] = relationship("ProyectoIntegrante", back_populates="proyecto")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "anio": self.anio,
            "linea_investigacion": self.linea_investigacion,
            "docente_id": self.docente_id,
            "descripcion": self.descripcion,
            "tecnologias": self.tecnologias,
            "resultados_impacto": self.resultados_impacto,
            "estado": self.estado,
            "observaciones": self.observaciones,
            "validado_por": self.validado_por,
            "fecha_validacion": self.fecha_validacion.isoformat() if self.fecha_validacion else None,
            "creador_id": self.creador_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ProyectoIntegrante(db.Model):
    __tablename__ = "proyecto_integrantes"

    proyecto_id: Mapped[int] = mapped_column(Integer, ForeignKey("proyectos.id"), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    rol_en_proyecto: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    proyecto: Mapped["Proyecto"] = relationship("Proyecto", back_populates="integrantes")
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="proyectos_como_integrante")

    def to_dict(self) -> dict:
        return {
            "proyecto_id": self.proyecto_id,
            "usuario_id": self.usuario_id,
            "rol_en_proyecto": self.rol_en_proyecto,
        }
