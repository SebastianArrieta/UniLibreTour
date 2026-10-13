from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Insignia(db.Model):
    __tablename__ = "insignias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[Optional[str]] = mapped_column(String(100), unique=True, nullable=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icono: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    usuarios: Mapped[list["UsuarioInsignia"]] = relationship("UsuarioInsignia", back_populates="insignia")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "icono": self.icono,
        }


class UsuarioInsignia(db.Model):
    __tablename__ = "usuarios_insignias"

    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    insignia_id: Mapped[int] = mapped_column(Integer, ForeignKey("insignias.id"), primary_key=True)
    fecha_obtenida: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="insignias")
    insignia: Mapped["Insignia"] = relationship("Insignia", back_populates="usuarios")

    def to_dict(self) -> dict:
        return {
            "usuario_id": self.usuario_id,
            "insignia_id": self.insignia_id,
            "fecha_obtenida": self.fecha_obtenida.isoformat() if self.fecha_obtenida else None,
        }
