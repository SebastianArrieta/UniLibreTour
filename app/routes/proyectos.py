from flask import Blueprint, request

from app.extensions import db
from app.middleware.auth import role_required
from app.models.proyecto import Proyecto, ProyectoIntegrante
from app.utils.response import json_error, json_ok

proyectos_bp = Blueprint("proyectos", __name__)

_CAMPOS = ("titulo", "anio", "linea_investigacion", "docente_id", "descripcion",
           "tecnologias", "resultados_impacto", "estado", "observaciones")


@proyectos_bp.get("")
def listar():
    proyectos = db.session.execute(db.select(Proyecto)).scalars().all()
    return json_ok([p.to_dict() for p in proyectos])


@proyectos_bp.get("/<int:proyecto_id>")
def obtener(proyecto_id: int):
    proyecto = db.session.get(Proyecto, proyecto_id)
    if not proyecto:
        return json_error("Proyecto no encontrado", 404)
    return json_ok(proyecto.to_dict())


@proyectos_bp.post("")
@role_required("admin", "guia")
def crear():
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    if not data.get("titulo"):
        return json_error("El campo 'titulo' es obligatorio", 400)
    proyecto = Proyecto(**{k: v for k, v in data.items() if k in _CAMPOS})
    proyecto.creador_id = int(get_jwt_identity())
    db.session.add(proyecto)
    db.session.commit()
    return json_ok(proyecto.to_dict(), 201)


@proyectos_bp.put("/<int:proyecto_id>")
@role_required("admin", "guia")
def actualizar(proyecto_id: int):
    proyecto = db.session.get(Proyecto, proyecto_id)
    if not proyecto:
        return json_error("Proyecto no encontrado", 404)
    data = request.get_json(silent=True) or {}
    for campo in _CAMPOS:
        if campo in data:
            setattr(proyecto, campo, data[campo])
    db.session.commit()
    return json_ok(proyecto.to_dict())


@proyectos_bp.delete("/<int:proyecto_id>")
@role_required("admin")
def eliminar(proyecto_id: int):
    proyecto = db.session.get(Proyecto, proyecto_id)
    if not proyecto:
        return json_error("Proyecto no encontrado", 404)
    db.session.delete(proyecto)
    db.session.commit()
    return json_ok({"mensaje": "Proyecto eliminado"})


# ── Integrantes ───────────────────────────────────────────────────────────────

@proyectos_bp.get("/<int:proyecto_id>/integrantes")
def listar_integrantes(proyecto_id: int):
    integrantes = db.session.execute(
        db.select(ProyectoIntegrante).where(ProyectoIntegrante.proyecto_id == proyecto_id)
    ).scalars().all()
    return json_ok([i.to_dict() for i in integrantes])


@proyectos_bp.post("/<int:proyecto_id>/integrantes")
@role_required("admin", "guia")
def agregar_integrante(proyecto_id: int):
    data = request.get_json(silent=True) or {}
    usuario_id = data.get("usuario_id")
    if not usuario_id:
        return json_error("Se requiere 'usuario_id'", 400)
    existente = db.session.get(ProyectoIntegrante, (proyecto_id, usuario_id))
    if existente:
        return json_error("El usuario ya es integrante", 400)
    integrante = ProyectoIntegrante(
        proyecto_id=proyecto_id,
        usuario_id=usuario_id,
        rol_en_proyecto=data.get("rol_en_proyecto"),
    )
    db.session.add(integrante)
    db.session.commit()
    return json_ok(integrante.to_dict(), 201)


@proyectos_bp.delete("/<int:proyecto_id>/integrantes/<int:usuario_id>")
@role_required("admin", "guia")
def quitar_integrante(proyecto_id: int, usuario_id: int):
    integrante = db.session.get(ProyectoIntegrante, (proyecto_id, usuario_id))
    if not integrante:
        return json_error("Integrante no encontrado", 404)
    db.session.delete(integrante)
    db.session.commit()
    return json_ok({"mensaje": "Integrante eliminado"})
