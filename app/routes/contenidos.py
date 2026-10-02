from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.middleware.auth import role_required
from app.models.contenido import Coleccion, Contenido, Etiqueta, Favorito
from app.utils.response import json_error, json_ok

contenidos_bp = Blueprint("contenidos", __name__)


# ── Colecciones ──────────────────────────────────────────────────────────────

@contenidos_bp.get("/colecciones")
def listar_colecciones():
    colecciones = db.session.execute(db.select(Coleccion)).scalars().all()
    return json_ok([c.to_dict() for c in colecciones])


@contenidos_bp.get("/colecciones/<int:coleccion_id>")
def obtener_coleccion(coleccion_id: int):
    col = db.session.get(Coleccion, coleccion_id)
    if not col:
        return json_error("Colección no encontrada", 404)
    return json_ok(col.to_dict())


@contenidos_bp.post("/colecciones")
@role_required("admin", "guia")
def crear_coleccion():
    data = request.get_json(silent=True) or {}
    if not data.get("titulo"):
        return json_error("El campo 'titulo' es obligatorio", 400)
    col = Coleccion(**{k: v for k, v in data.items() if k in ("titulo", "descripcion", "icono", "imagen")})
    db.session.add(col)
    db.session.commit()
    return json_ok(col.to_dict(), 201)


@contenidos_bp.put("/colecciones/<int:coleccion_id>")
@role_required("admin", "guia")
def actualizar_coleccion(coleccion_id: int):
    col = db.session.get(Coleccion, coleccion_id)
    if not col:
        return json_error("Colección no encontrada", 404)
    data = request.get_json(silent=True) or {}
    for campo in ("titulo", "descripcion", "icono", "imagen"):
        if campo in data:
            setattr(col, campo, data[campo])
    db.session.commit()
    return json_ok(col.to_dict())


@contenidos_bp.delete("/colecciones/<int:coleccion_id>")
@role_required("admin")
def eliminar_coleccion(coleccion_id: int):
    col = db.session.get(Coleccion, coleccion_id)
    if not col:
        return json_error("Colección no encontrada", 404)
    db.session.delete(col)
    db.session.commit()
    return json_ok({"mensaje": "Colección eliminada"})


# ── Etiquetas ─────────────────────────────────────────────────────────────────

@contenidos_bp.get("/etiquetas")
def listar_etiquetas():
    etiquetas = db.session.execute(db.select(Etiqueta)).scalars().all()
    return json_ok([e.to_dict() for e in etiquetas])


@contenidos_bp.post("/etiquetas")
@role_required("admin", "guia")
def crear_etiqueta():
    data = request.get_json(silent=True) or {}
    nombre = data.get("nombre", "").strip()
    if not nombre:
        return json_error("El campo 'nombre' es obligatorio", 400)
    try:
        etiqueta = Etiqueta(nombre=nombre)
        db.session.add(etiqueta)
        db.session.commit()
        return json_ok(etiqueta.to_dict(), 201)
    except IntegrityError:
        db.session.rollback()
        return json_error("La etiqueta ya existe", 400)


# ── Contenidos ────────────────────────────────────────────────────────────────

_CAMPOS_CONTENIDO = ("titulo", "categoria", "descripcion", "fecha", "imagen",
                     "autor", "estado", "observaciones", "coleccion_id")


@contenidos_bp.get("")
def listar_contenidos():
    contenidos = db.session.execute(db.select(Contenido)).scalars().all()
    return json_ok([c.to_dict() for c in contenidos])


@contenidos_bp.get("/<int:contenido_id>")
def obtener_contenido(contenido_id: int):
    contenido = db.session.get(Contenido, contenido_id)
    if not contenido:
        return json_error("Contenido no encontrado", 404)
    return json_ok(contenido.to_dict())


@contenidos_bp.post("")
@role_required("admin", "guia")
def crear_contenido():
    data = request.get_json(silent=True) or {}
    if not data.get("titulo"):
        return json_error("El campo 'titulo' es obligatorio", 400)
    from flask_jwt_extended import get_jwt_identity
    contenido = Contenido(**{k: v for k, v in data.items() if k in _CAMPOS_CONTENIDO})
    contenido.creador_id = int(get_jwt_identity())
    db.session.add(contenido)
    db.session.commit()
    return json_ok(contenido.to_dict(), 201)


@contenidos_bp.put("/<int:contenido_id>")
@role_required("admin", "guia")
def actualizar_contenido(contenido_id: int):
    contenido = db.session.get(Contenido, contenido_id)
    if not contenido:
        return json_error("Contenido no encontrado", 404)
    data = request.get_json(silent=True) or {}
    for campo in _CAMPOS_CONTENIDO:
        if campo in data:
            setattr(contenido, campo, data[campo])
    db.session.commit()
    return json_ok(contenido.to_dict())


@contenidos_bp.delete("/<int:contenido_id>")
@role_required("admin")
def eliminar_contenido(contenido_id: int):
    contenido = db.session.get(Contenido, contenido_id)
    if not contenido:
        return json_error("Contenido no encontrado", 404)
    db.session.delete(contenido)
    db.session.commit()
    return json_ok({"mensaje": "Contenido eliminado"})


# ── Favoritos ─────────────────────────────────────────────────────────────────

@contenidos_bp.post("/<int:contenido_id>/favorito")
@role_required("visitante", "guia", "admin")
def agregar_favorito(contenido_id: int):
    from flask_jwt_extended import get_jwt_identity
    usuario_id = int(get_jwt_identity())
    existente = db.session.get(Favorito, (usuario_id, contenido_id))
    if existente:
        return json_error("Ya está en favoritos", 400)
    fav = Favorito(usuario_id=usuario_id, contenido_id=contenido_id)
    db.session.add(fav)
    db.session.commit()
    return json_ok(fav.to_dict(), 201)


@contenidos_bp.delete("/<int:contenido_id>/favorito")
@role_required("visitante", "guia", "admin")
def quitar_favorito(contenido_id: int):
    from flask_jwt_extended import get_jwt_identity
    usuario_id = int(get_jwt_identity())
    fav = db.session.get(Favorito, (usuario_id, contenido_id))
    if not fav:
        return json_error("No está en favoritos", 404)
    db.session.delete(fav)
    db.session.commit()
    return json_ok({"mensaje": "Eliminado de favoritos"})
