"""API administrativa — altas directas y validación de contenido."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.middleware.auth import role_required
from app.models.usuario import Usuario
from app.schemas.admin import (
    EventoCreateSchema,
    HallCreateSchema,
    HitoCreateSchema,
    NoticiaCreateSchema,
    PremioCreateSchema,
    ProyectoCreateSchema,
    SemilleroCreateSchema,
    UsuarioAdminUpdateSchema,
    ValidacionSchema,
)
from app.services import admin as admin_svc
from app.services.usuario import ReglaUsuarioError, obtener_usuario
from app.utils.response import json_error, json_ok

admin_bp = Blueprint("admin", __name__)

hito_schema = HitoCreateSchema()
premio_schema = PremioCreateSchema()
proyecto_schema = ProyectoCreateSchema()
hall_schema = HallCreateSchema()
evento_schema = EventoCreateSchema()
noticia_schema = NoticiaCreateSchema()
semillero_schema = SemilleroCreateSchema()
validacion_schema = ValidacionSchema()
usuario_schema = UsuarioAdminUpdateSchema()


def _admin_actual() -> Usuario | None:
    identidad = get_jwt_identity()
    if identidad is None:
        return None
    return db.session.get(Usuario, int(identidad))


def _cargar(schema, request_obj=request):
    return schema.load(request_obj.get_json(silent=True) or {})


@admin_bp.post("/hitos")
@role_required("admin")
def crear_hito():
    """Crear hito de cronología
    ---
    tags: [Admin]
    summary: Alta de hito para la línea de tiempo
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [type, title, description]
          properties:
            type:
              type: string
              maxLength: 50
            title:
              type: string
              minLength: 3
              maxLength: 200
            description:
              type: string
              minLength: 3
    responses:
      201:
        description: Hito creado
        schema:
          type: object
      400:
        description: Validación fallida
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
        data = _cargar(hito_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_hito(data, admin).to_dict(), 201)


@admin_bp.post("/premios")
@role_required("admin")
def crear_premio():
    """Crear premio o logro
    ---
    tags: [Admin]
    summary: Alta de premio/logro para el museo
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [title, institution, description]
          properties:
            title:
              type: string
            institution:
              type: string
            description:
              type: string
            category:
              type: string
    responses:
      201:
        description: Premio creado
        schema:
          type: object
      400:
        description: Validación fallida
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
        data = _cargar(premio_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_premio(data, admin).to_dict(), 201)


@admin_bp.post("/proyectos")
@role_required("admin")
def crear_proyecto():
    """Crear proyecto
    ---
    tags: [Admin]
    summary: Alta de proyecto de investigación
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [title, author, category, description]
          properties:
            title:
              type: string
            author:
              type: string
            category:
              type: string
            description:
              type: string
    responses:
      201:
        description: Proyecto creado
        schema:
          type: object
      400:
        description: Validación fallida
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
        data = _cargar(proyecto_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_proyecto(data, admin).to_dict(), 201)


@admin_bp.post("/hall")
@role_required("admin")
def crear_hall():
    """Crear miembro del Hall de la Fama
    ---
    tags: [Admin]
    summary: Alta en el Salón de la Fama
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, title, achievement]
          properties:
            name:
              type: string
            title:
              type: string
            achievement:
              type: string
            category:
              type: string
    responses:
      201:
        description: Miembro creado
        schema:
          type: object
      400:
        description: Validación fallida
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
        data = _cargar(hall_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_hall(data, admin).to_dict(), 201)


@admin_bp.post("/eventos")
@role_required("admin")
def crear_evento():
    """Crear evento
    ---
    tags: [Admin]
    summary: Alta de evento para el calendario del museo
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [title, date, time, type, location]
          properties:
            title:
              type: string
            date:
              type: string
            time:
              type: string
            type:
              type: string
            location:
              type: string
    responses:
      201:
        description: Evento creado
        schema:
          type: object
      400:
        description: Validación fallida
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
        data = _cargar(evento_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_evento(data, admin).to_dict(), 201)


@admin_bp.post("/noticias")
@role_required("admin")
def crear_noticia():
    """Crear noticia
    ---
    tags: [Admin]
    summary: Alta de noticia publicada en el museo
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [title, category, date, excerpt]
          properties:
            title:
              type: string
            category:
              type: string
            date:
              type: string
            excerpt:
              type: string
    responses:
      201:
        description: Noticia creada
        schema:
          type: object
      400:
        description: Validación fallida
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
        data = _cargar(noticia_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_noticia(data, admin).to_dict(), 201)


@admin_bp.post("/semilleros")
@role_required("admin")
def crear_semillero():
    """Crear semillero o grupo de investigación
    ---
    tags: [Admin]
    summary: Alta de semillero; el líder debe ser un docente existente
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [name, description]
          properties:
            name:
              type: string
            description:
              type: string
            leader_id:
              type: integer
              description: id de un usuario con rol docente
    responses:
      201:
        description: Semillero creado
        schema:
          type: object
      400:
        description: Validación fallida o líder no es docente
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
        data = _cargar(semillero_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    semillero = admin_svc.crear_semillero(data, _admin_actual())
    if semillero is None:
        return json_error("El líder seleccionado debe ser un docente existente", 400)
    return json_ok(semillero.to_dict(), 201)


@admin_bp.put("/contenidos/<int:contenido_id>/validar")
@role_required("admin")
def validar_contenido(contenido_id: int):
    """Validar un contenido de la cola
    ---
    tags: [Admin]
    summary: Aprueba o devuelve un aporte pendiente (decisión final)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: contenido_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [estado]
          properties:
            estado:
              type: string
              enum: [publicado, rechazado]
            observaciones:
              type: string
    responses:
      200:
        description: Contenido actualizado
        schema:
          type: object
      400:
        description: Validación fallida
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
        description: Contenido no encontrado
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        data = _cargar(validacion_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)

    admin = _admin_actual()
    contenido = admin_svc.validar_contenido(contenido_id, data, admin)
    if contenido is None:
        return json_error("Contenido no encontrado", 404)
    return json_ok(contenido.to_dict())


@admin_bp.put("/usuarios/<int:usuario_id>")
@role_required("admin")
def actualizar_usuario(usuario_id: int):
    """Editar usuario como administrador
    ---
    tags: [Admin]
    summary: Cambia nombre, email o rol de cualquier usuario
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
      400:
        description: Validación fallida, email duplicado o regla de negocio
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
    if usuario is None:
        return json_error("Usuario no encontrado", 404)

    try:
        data = _cargar(usuario_schema)
        usuario = admin_svc.actualizar_usuario(usuario, data)
    except ReglaUsuarioError as err:
        db.session.rollback()
        return json_error(str(err), 400)
    except ValidationError as err:
        return json_error(err.messages, 400)
    except IntegrityError:
        db.session.rollback()
        return json_error("El email ya está registrado", 400)
    return json_ok(usuario.to_dict())


@admin_bp.put("/usuarios/<int:usuario_id>/aprobar")
@role_required("admin")
def aprobar_usuario(usuario_id: int):
    """Aprobar cuenta pendiente
    ---
    tags: [Admin]
    summary: Pasa el estado de la cuenta a activo (permite login)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: usuario_id
        required: true
        type: integer
    responses:
      200:
        description: Usuario aprobado
        schema:
          type: object
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
    if usuario is None:
        return json_error("Usuario no encontrado", 404)
    return json_ok(admin_svc.aprobar_usuario(usuario).to_dict())
