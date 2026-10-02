from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.usuario import Usuario


class Coleccion(db.Model):
    __tablename__ = "colecciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icono: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    imagen: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    contenidos: Mapped[list["Contenido"]] = relationship("Contenido", back_populates="coleccion")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "icono": self.icono,
            "imagen": self.imagen,
        }


class Etiqueta(db.Model):
    __tablename__ = "etiquetas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)

    def to_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre}


class ContenidoEtiqueta(db.Model):
    __tablename__ = "contenido_etiquetas"

    contenido_id: Mapped[int] = mapped_column(Integer, ForeignKey("contenidos.id"), primary_key=True)
    etiqueta_id: Mapped[int] = mapped_column(Integer, ForeignKey("etiquetas.id"), primary_key=True)


class Contenido(db.Model):
    __tablename__ = "contenidos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fecha: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Date stored as string (YYYY-MM-DD)
    imagen: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    autor: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    estado: Mapped[str] = mapped_column(String(20), default="borrador", nullable=False)
    observaciones: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    validado_por: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    fecha_validacion: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    creador_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("usuarios.id"), nullable=True)
    coleccion_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("colecciones.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    coleccion: Mapped[Optional["Coleccion"]] = relationship("Coleccion", back_populates="contenidos")
    creador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[creador_id], back_populates=None)
    validador: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[validado_por], back_populates=None)
    etiquetas: Mapped[list["Etiqueta"]] = relationship("Etiqueta", secondary="contenido_etiquetas")
    favoritos: Mapped[list["Favorito"]] = relationship("Favorito", back_populates="contenido")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "categoria": self.categoria,
            "descripcion": self.descripcion,
            "fecha": self.fecha,
            "imagen": self.imagen,
            "autor": self.autor,
            "estado": self.estado,
            "observaciones": self.observaciones,
            "validado_por": self.validado_por,
            "fecha_validacion": self.fecha_validacion.isoformat() if self.fecha_validacion else None,
            "creador_id": self.creador_id,
            "coleccion_id": self.coleccion_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Favorito(db.Model):
    __tablename__ = "favoritos"

    usuario_id: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.id"), primary_key=True)
    contenido_id: Mapped[int] = mapped_column(Integer, ForeignKey("contenidos.id"), primary_key=True)
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    usuario: Mapped["Usuario"] = relationship("Usuario", back_populates="favoritos")
    contenido: Mapped["Contenido"] = relationship("Contenido", back_populates="favoritos")

    def to_dict(self) -> dict:
        return {
            "usuario_id": self.usuario_id,
            "contenido_id": self.contenido_id,
            "fecha": self.fecha.isoformat() if self.fecha else None,
        }
