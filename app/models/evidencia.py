from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Evidencia(db.Model):
    __tablename__ = "evidencias"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    entidad_tipo: Mapped[str] = mapped_column(String(50), nullable=False)
    entidad_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tipo_archivo: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "entidad_tipo": self.entidad_tipo,
            "entidad_id": self.entidad_id,
            "tipo_archivo": self.tipo_archivo,
            "url": self.url,
            "descripcion": self.descripcion,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
