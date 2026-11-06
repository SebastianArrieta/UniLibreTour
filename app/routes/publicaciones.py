from flask import Blueprint, request

from app.extensions import db
from app.middleware.auth import role_required
from app.models.publicacion import HallFama, Noticia
from app.utils.response import json_error, json_ok

noticias_bp = Blueprint("noticias", __name__)
hall_fama_bp = Blueprint("hall_fama", __name__)

# ── Noticias ──────────────────────────────────────────────────────────────────

_CAMPOS_NOTICIA = ("titulo", "resumen", "fecha", "categoria", "imagen",
                   "estado", "observaciones")


@noticias_bp.get("")
def listar_noticias():
    noticias = db.session.execute(db.select(Noticia)).scalars().all()
    return json_ok([n.to_dict() for n in noticias])


@noticias_bp.get("/<int:noticia_id>")
def obtener_noticia(noticia_id: int):
    noticia = db.session.get(Noticia, noticia_id)
    if not noticia:
        return json_error("Noticia no encontrada", 404)
    return json_ok(noticia.to_dict())


@noticias_bp.post("")
@role_required("admin", "guia")
def crear_noticia():
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    if not data.get("titulo"):
        return json_error("El campo 'titulo' es obligatorio", 400)
    noticia = Noticia(**{k: v for k, v in data.items() if k in _CAMPOS_NOTICIA})
    noticia.creador_id = int(get_jwt_identity())
    db.session.add(noticia)
    db.session.commit()
    return json_ok(noticia.to_dict(), 201)


@noticias_bp.put("/<int:noticia_id>")
@role_required("admin", "guia")
def actualizar_noticia(noticia_id: int):
    noticia = db.session.get(Noticia, noticia_id)
    if not noticia:
        return json_error("Noticia no encontrada", 404)
    data = request.get_json(silent=True) or {}
    for campo in _CAMPOS_NOTICIA:
        if campo in data:
            setattr(noticia, campo, data[campo])
    db.session.commit()
    return json_ok(noticia.to_dict())


@noticias_bp.delete("/<int:noticia_id>")
@role_required("admin")
def eliminar_noticia(noticia_id: int):
    noticia = db.session.get(Noticia, noticia_id)
    if not noticia:
        return json_error("Noticia no encontrada", 404)
    db.session.delete(noticia)
    db.session.commit()
    return json_ok({"mensaje": "Noticia eliminada"})


# ── Hall de la Fama ───────────────────────────────────────────────────────────

_CAMPOS_HALL = ("nombre", "titulo", "anio", "logro", "categoria",
                "imagen", "estado", "observaciones")


@hall_fama_bp.get("")
def listar_hall():
    entradas = db.session.execute(db.select(HallFama)).scalars().all()
    return json_ok([e.to_dict() for e in entradas])


@hall_fama_bp.get("/<int:entrada_id>")
def obtener_hall(entrada_id: int):
    entrada = db.session.get(HallFama, entrada_id)
    if not entrada:
        return json_error("Entrada no encontrada", 404)
    return json_ok(entrada.to_dict())


@hall_fama_bp.post("")
@role_required("admin", "guia")
def crear_hall():
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    if not data.get("nombre"):
        return json_error("El campo 'nombre' es obligatorio", 400)
    entrada = HallFama(**{k: v for k, v in data.items() if k in _CAMPOS_HALL})
    entrada.creador_id = int(get_jwt_identity())
    db.session.add(entrada)
    db.session.commit()
    return json_ok(entrada.to_dict(), 201)


@hall_fama_bp.put("/<int:entrada_id>")
@role_required("admin", "guia")
def actualizar_hall(entrada_id: int):
    entrada = db.session.get(HallFama, entrada_id)
    if not entrada:
        return json_error("Entrada no encontrada", 404)
    data = request.get_json(silent=True) or {}
    for campo in _CAMPOS_HALL:
        if campo in data:
            setattr(entrada, campo, data[campo])
    db.session.commit()
    return json_ok(entrada.to_dict())


@hall_fama_bp.delete("/<int:entrada_id>")
@role_required("admin")
def eliminar_hall(entrada_id: int):
    entrada = db.session.get(HallFama, entrada_id)
    if not entrada:
        return json_error("Entrada no encontrada", 404)
    db.session.delete(entrada)
    db.session.commit()
    return json_ok({"mensaje": "Entrada eliminada"})
