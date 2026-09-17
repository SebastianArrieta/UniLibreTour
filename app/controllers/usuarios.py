from flask import Blueprint, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.middleware.auth import role_required
from app.schemas.usuario import UsuarioCreateSchema, UsuarioSchema, UsuarioUpdateSchema
from app.services.usuario import (
    actualizar_usuario,
    crear_usuario,
    eliminar_usuario,
    listar_usuarios,
    obtener_usuario,
)
from app.utils.response import json_error, json_ok

usuarios_bp = Blueprint("usuarios", __name__)
usuario_schema = UsuarioSchema()
usuarios_schema = UsuarioSchema(many=True)
create_schema = UsuarioCreateSchema()
update_schema = UsuarioUpdateSchema()


@usuarios_bp.get("")
def listar():
    return json_ok(usuarios_schema.dump(listar_usuarios()))


@usuarios_bp.get("/<int:usuario_id>")
def obtener(usuario_id: int):
    usuario = obtener_usuario(usuario_id)
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    return json_ok(usuario_schema.dump(usuario))


@usuarios_bp.post("")
def crear():
    try:
        data = create_schema.load(request.get_json(silent=True) or {})
        usuario = crear_usuario(data)
        return json_ok(usuario_schema.dump(usuario), 201)
    except ValidationError as err:
        return json_error(err.messages, 400)
    except IntegrityError:
        db.session.rollback()
        return json_error("El email ya está registrado", 400)


@usuarios_bp.put("/<int:usuario_id>")
def actualizar(usuario_id: int):
    usuario = obtener_usuario(usuario_id)
    if not usuario:
        return json_error("Usuario no encontrado", 404)

    try:
        data = update_schema.load(request.get_json(silent=True) or {})
        usuario = actualizar_usuario(usuario, data)
        return json_ok(usuario_schema.dump(usuario))
    except ValidationError as err:
        return json_error(err.messages, 400)
    except IntegrityError:
        db.session.rollback()
        return json_error("El email ya está registrado", 400)


@usuarios_bp.delete("/<int:usuario_id>")
@role_required("admin")
def eliminar(usuario_id: int):
    usuario = obtener_usuario(usuario_id)
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    eliminar_usuario(usuario)
    return json_ok({"mensaje": "Usuario eliminado"})
