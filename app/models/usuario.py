from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db

if TYPE_CHECKING:
    from app.models.semillero import Semillero
    from app.models.notificacion import Notificacion
    from app.models.interaccion import Comentario, Reaccion
    from app.models.contenido import Favorito
    from app.models.insignia import UsuarioInsignia
    from app.models.proyecto import ProyectoIntegrante
    from app.models.premio import PremioParticipante


class Usuario(db.Model):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[str] = mapped_column(String(20), default="visitante", nullable=False)
    estado: Mapped[str] = mapped_column(String(20), default="activo", nullable=False)
    puntos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nivel: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    semillero_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("semilleros.id", use_alter=True, name="fk_usuarios_semillero"),
        nullable=True,
    )
    two_factor_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    anio_grado: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cargo_actual: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    semillero: Mapped[Optional["Semillero"]] = relationship(
        "Semillero", back_populates="miembros", foreign_keys=[semillero_id]
    )
    notificaciones: Mapped[list["Notificacion"]] = relationship("Notificacion", back_populates="usuario")
    comentarios: Mapped[list["Comentario"]] = relationship("Comentario", back_populates="usuario")
    reacciones: Mapped[list["Reaccion"]] = relationship("Reaccion", back_populates="usuario")
    favoritos: Mapped[list["Favorito"]] = relationship("Favorito", back_populates="usuario")
    insignias: Mapped[list["UsuarioInsignia"]] = relationship("UsuarioInsignia", back_populates="usuario")
    proyectos_como_integrante: Mapped[list["ProyectoIntegrante"]] = relationship(
        "ProyectoIntegrante", back_populates="usuario"
    )
    premios_como_participante: Mapped[list["PremioParticipante"]] = relationship(
        "PremioParticipante", back_populates="usuario"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "email": self.email,
            "rol": self.rol,
            "estado": self.estado,
            "puntos": self.puntos,
            "nivel": self.nivel,
            "semillero_id": self.semillero_id,
            "two_factor_enabled": self.two_factor_enabled,
            "anio_grado": self.anio_grado,
            "cargo_actual": self.cargo_actual,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
