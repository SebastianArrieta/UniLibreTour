from flask import Blueprint, request

from app.extensions import db
from app.middleware.auth import role_required
from app.models.evidencia import Evidencia
from app.utils.response import json_error, json_ok

evidencias_bp = Blueprint("evidencias", __name__)


@evidencias_bp.get("")
def listar():
    entidad_tipo = request.args.get("entidad_tipo")
    entidad_id = request.args.get("entidad_id", type=int)
    query = db.select(Evidencia)
    if entidad_tipo:
        query = query.where(Evidencia.entidad_tipo == entidad_tipo)
    if entidad_id:
        query = query.where(Evidencia.entidad_id == entidad_id)
    evidencias = db.session.execute(query).scalars().all()
    return json_ok([e.to_dict() for e in evidencias])


@evidencias_bp.get("/<int:evidencia_id>")
def obtener(evidencia_id: int):
    evidencia = db.session.get(Evidencia, evidencia_id)
    if not evidencia:
        return json_error("Evidencia no encontrada", 404)
    return json_ok(evidencia.to_dict())


@evidencias_bp.post("")
@role_required("admin", "guia")
def crear():
    data = request.get_json(silent=True) or {}
    if not all(k in data for k in ("entidad_tipo", "entidad_id", "url")):
        return json_error("Se requiere 'entidad_tipo', 'entidad_id' y 'url'", 400)
    evidencia = Evidencia(
        entidad_tipo=data["entidad_tipo"],
        entidad_id=data["entidad_id"],
        url=data["url"],
        tipo_archivo=data.get("tipo_archivo"),
        descripcion=data.get("descripcion"),
    )
    db.session.add(evidencia)
    db.session.commit()
    return json_ok(evidencia.to_dict(), 201)


@evidencias_bp.delete("/<int:evidencia_id>")
@role_required("admin", "guia")
def eliminar(evidencia_id: int):
    evidencia = db.session.get(Evidencia, evidencia_id)
    if not evidencia:
        return json_error("Evidencia no encontrada", 404)
    db.session.delete(evidencia)
    db.session.commit()
    return json_ok({"mensaje": "Evidencia eliminada"})
