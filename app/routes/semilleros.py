from flask import Blueprint, request

from app.extensions import db
from app.middleware.auth import role_required
from app.models.semillero import Semillero
from app.utils.response import json_error, json_ok

semilleros_bp = Blueprint("semilleros", __name__)

_CAMPOS = ("nombre", "categoria", "lider_id", "descripcion", "imagen")


@semilleros_bp.get("")
def listar():
    semilleros = db.session.execute(db.select(Semillero)).scalars().all()
    return json_ok([s.to_dict() for s in semilleros])


@semilleros_bp.get("/<int:semillero_id>")
def obtener(semillero_id: int):
    semillero = db.session.get(Semillero, semillero_id)
    if not semillero:
        return json_error("Semillero no encontrado", 404)
    return json_ok(semillero.to_dict())


@semilleros_bp.post("")
@role_required("admin")
def crear():
    data = request.get_json(silent=True) or {}
    if not data.get("nombre"):
        return json_error("El campo 'nombre' es obligatorio", 400)
    semillero = Semillero(**{k: v for k, v in data.items() if k in _CAMPOS})
    db.session.add(semillero)
    db.session.commit()
    return json_ok(semillero.to_dict(), 201)


@semilleros_bp.put("/<int:semillero_id>")
@role_required("admin")
def actualizar(semillero_id: int):
    semillero = db.session.get(Semillero, semillero_id)
    if not semillero:
        return json_error("Semillero no encontrado", 404)
    data = request.get_json(silent=True) or {}
    for campo in _CAMPOS:
        if campo in data:
            setattr(semillero, campo, data[campo])
    db.session.commit()
    return json_ok(semillero.to_dict())


@semilleros_bp.delete("/<int:semillero_id>")
@role_required("admin")
def eliminar(semillero_id: int):
    semillero = db.session.get(Semillero, semillero_id)
    if not semillero:
        return json_error("Semillero no encontrado", 404)
    db.session.delete(semillero)
    db.session.commit()
    return json_ok({"mensaje": "Semillero eliminado"})
