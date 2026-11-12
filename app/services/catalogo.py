"""Catálogo base del museo: colecciones e insignias de referencia.

No es contenido: son las categorías institucionales en las que se clasifican
los aportes y las insignias que se pueden otorgar. Se crean al arrancar si
faltan (idempotente) y nunca se sobrescriben las que ya existen.

También crea el primer administrador desde variables de entorno
(ADMIN_EMAIL / ADMIN_PASSWORD) cuando todavía no existe ninguno.
"""

from __future__ import annotations

import logging
import os

from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.contenido import Coleccion
from app.models.insignia import Insignia
from app.models.usuario import Usuario
from app.services.auth import hash_password

log = logging.getLogger(__name__)

COLECCIONES = [
    ("historia", "Historia del Programa", "🏛️",
     "Documentos fundacionales, actas e hitos que marcaron la trayectoria académica del programa."),
    ("investigacion", "Investigación", "🔬",
     "Publicaciones, artículos indexados y resultados de los grupos de investigación."),
    ("proyectos", "Proyectos de Grado", "🎓",
     "Trabajos de grado meritorios y laureados con impacto en la industria y la academia."),
    ("eventos", "Eventos Académicos", "📅",
     "Congresos, simposios, semilleros y actividades que enriquecen la vida universitaria."),
    ("logros", "Logros y Reconocimientos", "🏆",
     "Premios, acreditaciones y distinciones obtenidas por docentes, estudiantes y egresados."),
    ("docentes", "Docentes Destacados", "👨‍🏫",
     "Perfiles de investigadores, directores de grupo y mentores del programa."),
]

INSIGNIAS = [
    ("primer-paso", "Primer Paso", "🏛️"),
    ("explorador", "Explorador", "🔍"),
    ("comentarista", "Comentarista", "💬"),
    ("favoritos", "Favoritos", "⭐"),
    ("lector-avido", "Lector Ávido", "📊"),
    ("punteria", "Puntería", "🎯"),
    ("colaborador", "Colaborador", "🤝"),
    ("campeon", "Campeón", "🏆"),
    ("critica-de-arte", "Crítica de Arte", "🎨"),
    ("enciclopedia", "Enciclopedia", "📚"),
    ("embajador", "Embajador", "📣"),
    ("global", "Global", "🌐"),
]


def seed_catalogo() -> None:
    """Crea las colecciones e insignias de referencia que falten."""
    existentes = {c.slug for c in Coleccion.query.all()}
    for slug, titulo, icono, descripcion in COLECCIONES:
        if slug not in existentes:
            db.session.add(Coleccion(slug=slug, titulo=titulo, descripcion=descripcion,
                                     icono=icono, imagen=None))
    existentes = {i.slug for i in Insignia.query.all()}
    for slug, nombre, icono in INSIGNIAS:
        if slug not in existentes:
            db.session.add(Insignia(slug=slug, nombre=nombre, icono=icono, descripcion=None))
    try:
        db.session.commit()
    except IntegrityError:
        # Otro worker de gunicorn lo creó a la vez.
        db.session.rollback()


def bootstrap_admin() -> None:
    """Crea el primer admin desde ADMIN_EMAIL/ADMIN_PASSWORD si no hay ninguno."""
    if Usuario.query.filter_by(rol="admin").first() is not None:
        return
    email = (os.getenv("ADMIN_EMAIL") or "").strip().lower()
    password = os.getenv("ADMIN_PASSWORD") or ""
    if not email or not password:
        log.warning("No hay ningún administrador: define ADMIN_EMAIL y ADMIN_PASSWORD para crearlo.")
        return
    if len(password) < 8:
        log.error("ADMIN_PASSWORD debe tener al menos 8 caracteres; no se creó el administrador.")
        return
    existente = Usuario.query.filter_by(email=email).first()
    if existente is not None:
        # La cuenta ya existía: se promueve a admin y se le asigna ADMIN_PASSWORD.
        existente.rol = "admin"
        existente.estado = "activo"
        existente.password_hash = hash_password(password)
    else:
        db.session.add(Usuario(
            nombre=os.getenv("ADMIN_NOMBRE", "Administrador"),
            email=email,
            password_hash=hash_password(password),
            rol="admin",
            estado="activo",
        ))
    try:
        db.session.commit()
        log.info("Administrador inicial listo: %s", email)
    except IntegrityError:
        db.session.rollback()
