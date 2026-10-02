from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Semillero(db.Model):
    __tablename__ = "semilleros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    categoria: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    lider_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    imagen: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    lider: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[lider_id], back_populates=None
    )
    miembros: Mapped[list["Usuario"]] = relationship(
        "Usuario", back_populates="semillero", foreign_keys="Usuario.semillero_id"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "lider_id": self.lider_id,
            "descripcion": self.descripcion,
            "imagen": self.imagen,
        }
