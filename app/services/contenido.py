"""Servicio de contenidos — escritura fase 2 (aporte → cola de validación)."""

from __future__ import annotations

from datetime import date

from app.extensions import db
from app.models.contenido import Coleccion, Contenido, Etiqueta
from app.models.usuario import Usuario

# Roles autorizados a aportar contenido (visitante es anónimo/solo lectura)
ROLES_CONTRIBUYENTES = ("estudiante", "docente", "egresado", "admin")


def _obtener_o_crear_etiqueta(nombre: str) -> Etiqueta:
    et = Etiqueta.query.filter_by(nombre=nombre).first()
    if et is None:
        et = Etiqueta(nombre=nombre)
        db.session.add(et)
        db.session.flush()
    return et


def puede_aportar(usuario: Usuario) -> bool:
    return usuario.rol in ROLES_CONTRIBUYENTES


def crear_contenido(data: dict, usuario: Usuario) -> Contenido:
    """Crea una pieza en estado 'pendiente': entra directo a la cola de
    validación del flujo general del museo (registro → validación → publicación)."""
    categoria = (data.get("category") or "").strip()
    coleccion = Coleccion.query.filter_by(slug=categoria).first() if categoria else None

    contenido = Contenido(
        titulo=data["title"].strip(),
        categoria=categoria or None,
        descripcion=data["description"].strip(),
        fecha=data.get("date") or date.today().isoformat(),
        imagen=data.get("image"),
        autor=(data.get("author") or usuario.nombre).strip(),
        estado="pendiente",
        creador_id=usuario.id,
        coleccion_id=coleccion.id if coleccion else None,
    )
    db.session.add(contenido)
    db.session.flush()

    nombres = [str(t).strip() for t in data.get("tags") or [] if str(t).strip()]
    contenido.etiquetas = [_obtener_o_crear_etiqueta(n) for n in dict.fromkeys(nombres)]

    db.session.commit()
    return contenido
