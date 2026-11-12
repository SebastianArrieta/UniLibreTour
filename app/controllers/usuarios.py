from flask import Blueprint, request
from flask_jwt_extended import current_user, jwt_required
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.middleware.auth import role_required
from app.schemas.usuario import UsuarioCreateSchema, UsuarioSchema, UsuarioUpdateSchema
from app.services.usuario import (
    ReglaUsuarioError,
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


def _es_admin() -> bool:
    return current_user is not None and current_user.rol == "admin"


def _es_propio(usuario_id: int) -> bool:
    return current_user is not None and current_user.id == usuario_id


@usuarios_bp.get("")
@role_required("admin")
def listar():
    """Listar todos los usuarios
    ---
    tags: [Usuarios]
    summary: Catálogo completo de usuarios (solo administrador)
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de usuarios
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: array
              items:
                type: object
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Rol insuficiente (requiere admin)
        schema:
          $ref: '#/definitions/Error'
    """
    return json_ok(usuarios_schema.dump(listar_usuarios()))


@usuarios_bp.get("/<int:usuario_id>")
@jwt_required()
def obtener(usuario_id: int):
    """Obtener un usuario por id
    ---
    tags: [Usuarios]
    summary: Solo el propio usuario o un administrador
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
    responses:
      200:
        description: Usuario encontrado
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      403:
        description: No es el dueño ni admin
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Usuario no encontrado
        schema:
          $ref: '#/definitions/Error'
    """
    if not (_es_admin() or _es_propio(usuario_id)):
        return json_error("No tienes permiso", 403)
    usuario = obtener_usuario(usuario_id)
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    return json_ok(usuario_schema.dump(usuario))


@usuarios_bp.post("")
@role_required("admin")
def crear():
    """Crear usuario
    ---
    tags: [Usuarios]
    summary: Alta de usuario por parte del administrador
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/UsuarioCreate'
    responses:
      201:
        description: Usuario creado
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
      400:
        description: Validación fallida o email ya registrado
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Rol insuficiente (requiere admin)
        schema:
          $ref: '#/definitions/Error'
    """
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
@jwt_required()
def actualizar(usuario_id: int):
    """Actualizar usuario (PUT completo)
    ---
    tags: [Usuarios]
    summary: El usuario edita su nombre; el admin edita nombre, email y rol
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/UsuarioUpdate'
    responses:
      200:
        description: Usuario actualizado
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
      400:
        description: Validación fallida o email duplicado
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      403:
        description: No es el dueño ni admin
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Usuario no encontrado
        schema:
          $ref: '#/definitions/Error'
    """
    if not (_es_admin() or _es_propio(usuario_id)):
        return json_error("No tienes permiso", 403)

    usuario = obtener_usuario(usuario_id)
    if not usuario:
        return json_error("Usuario no encontrado", 404)

    try:
        data = update_schema.load(request.get_json(silent=True) or {})
        if not _es_admin():
            # Un usuario solo puede editar su propio nombre; email y rol son
            # campos administrativos.
            data = {campo: valor for campo, valor in data.items() if campo == "nombre"}
        usuario = actualizar_usuario(usuario, data)
        return json_ok(usuario_schema.dump(usuario))
    except ReglaUsuarioError as err:
        db.session.rollback()
        return json_error(str(err), 400)
    except ValidationError as err:
        return json_error(err.messages, 400)
    except IntegrityError:
        db.session.rollback()
        return json_error("El email ya está registrado", 400)


@usuarios_bp.patch("/<int:usuario_id>")
@jwt_required()
def actualizar_parcial(usuario_id: int):
    """Actualizar usuario (PATCH parcial)
    ---
    tags: [Usuarios]
    summary: Modifica solo los campos enviados; el resto queda intacto
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/UsuarioUpdate'
    responses:
      200:
        description: Usuario actualizado parcialmente
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
      400:
        description: Validación fallida o email duplicado
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      403:
        description: No es el dueño ni admin
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Usuario no encontrado
        schema:
          $ref: '#/definitions/Error'
    """
    if not (_es_admin() or _es_propio(usuario_id)):
        return json_error("No tienes permiso", 403)

    usuario = obtener_usuario(usuario_id)
    if not usuario:
        return json_error("Usuario no encontrado", 404)

    try:
        data = update_schema.load(request.get_json(silent=True) or {})
        if not _es_admin():
            data = {campo: valor for campo, valor in data.items() if campo == "nombre"}
        usuario = actualizar_usuario(usuario, data)
        return json_ok(usuario_schema.dump(usuario))
    except ReglaUsuarioError as err:
        db.session.rollback()
        return json_error(str(err), 400)
    except ValidationError as err:
        return json_error(err.messages, 400)
    except IntegrityError:
        db.session.rollback()
        return json_error("El email ya está registrado", 400)


@usuarios_bp.delete("/<int:usuario_id>")
@role_required("admin")
def eliminar(usuario_id: int):
    """Eliminar usuario
    ---
    tags: [Usuarios]
    summary: Baja definitiva de un usuario (solo administrador)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
    responses:
      200:
        description: Usuario eliminado
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
      400:
        description: Regla de negocio impedida (p. ej. no puede borrarse a sí mismo)
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      403:
        description: Rol insuficiente (requiere admin)
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Usuario no encontrado
        schema:
          $ref: '#/definitions/Error'
    """
    usuario = obtener_usuario(usuario_id)
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    try:
        resultado = eliminar_usuario(usuario, actor_id=current_user.id)
    except ReglaUsuarioError as err:
        db.session.rollback()
        return json_error(str(err), 400)
    return json_ok(resultado)
