"""API de notificaciones del usuario autenticado."""

from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.schemas.admin import NotificacionUpdateSchema
from app.services import notificacion as notificacion_svc
from app.utils.response import json_error, json_ok

notificaciones_bp = Blueprint("notificaciones", __name__)
update_schema = NotificacionUpdateSchema()


def _usuario_id() -> int:
    return int(get_jwt_identity())


@notificaciones_bp.get("")
@jwt_required()
def listar():
    return json_ok([n.to_dict() for n in notificacion_svc.listar(_usuario_id())])


@notificaciones_bp.put("/leidas")
@jwt_required()
def marcar_todas():
    actualizadas = notificacion_svc.marcar_todas(_usuario_id())
    return json_ok({"actualizadas": actualizadas})


@notificaciones_bp.put("/<int:notificacion_id>")
@jwt_required()
def marcar(notificacion_id: int):
    try:
        data = update_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return json_error(err.messages, 400)

    notificacion = notificacion_svc.marcar(
        _usuario_id(), notificacion_id, data.get("leido")
    )
    if notificacion is None:
        return json_error("Notificación no encontrada", 404)
    return json_ok(notificacion.to_dict())
