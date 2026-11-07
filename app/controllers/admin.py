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
from app.services.usuario import obtener_usuario
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
    try:
        data = _cargar(hito_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_hito(data, admin).to_dict(), 201)


@admin_bp.post("/premios")
@role_required("admin")
def crear_premio():
    try:
        data = _cargar(premio_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_premio(data, admin).to_dict(), 201)


@admin_bp.post("/proyectos")
@role_required("admin")
def crear_proyecto():
    try:
        data = _cargar(proyecto_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_proyecto(data, admin).to_dict(), 201)


@admin_bp.post("/hall")
@role_required("admin")
def crear_hall():
    try:
        data = _cargar(hall_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_hall(data, admin).to_dict(), 201)


@admin_bp.post("/eventos")
@role_required("admin")
def crear_evento():
    try:
        data = _cargar(evento_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_evento(data, admin).to_dict(), 201)


@admin_bp.post("/noticias")
@role_required("admin")
def crear_noticia():
    try:
        data = _cargar(noticia_schema)
    except ValidationError as err:
        return json_error(err.messages, 400)
    admin = _admin_actual()
    return json_ok(admin_svc.crear_noticia(data, admin).to_dict(), 201)


@admin_bp.post("/semilleros")
@role_required("admin")
def crear_semillero():
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
    usuario = obtener_usuario(usuario_id)
    if usuario is None:
        return json_error("Usuario no encontrado", 404)

    try:
        data = _cargar(usuario_schema)
        usuario = admin_svc.actualizar_usuario(usuario, data)
    except ValidationError as err:
        return json_error(err.messages, 400)
    except IntegrityError:
        db.session.rollback()
        return json_error("El email ya está registrado", 400)
    return json_ok(usuario.to_dict())


@admin_bp.put("/usuarios/<int:usuario_id>/aprobar")
@role_required("admin")
def aprobar_usuario(usuario_id: int):
    usuario = obtener_usuario(usuario_id)
    if usuario is None:
        return json_error("Usuario no encontrado", 404)
    return json_ok(admin_svc.aprobar_usuario(usuario).to_dict())
