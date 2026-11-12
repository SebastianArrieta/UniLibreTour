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
    """Listar notificaciones del usuario
    ---
    tags: [Notificaciones]
    summary: Avisos del usuario autenticado
    security:
      - Bearer: []
    responses:
      200:
        description: Lista de notificaciones
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
    """
    return json_ok([n.to_dict() for n in notificacion_svc.listar(_usuario_id())])


@notificaciones_bp.put("/leidas")
@jwt_required()
def marcar_todas():
    """Marcar todas como leídas
    ---
    tags: [Notificaciones]
    summary: Pone leídas todas las notificaciones del usuario
    security:
      - Bearer: []
    responses:
      200:
        description: Número de notificaciones actualizadas
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
              properties:
                actualizadas:
                  type: integer
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
    """
    actualizadas = notificacion_svc.marcar_todas(_usuario_id())
    return json_ok({"actualizadas": actualizadas})


@notificaciones_bp.put("/<int:notificacion_id>")
@jwt_required()
def marcar(notificacion_id: int):
    """Marcar una notificación como leída o no leída
    ---
    tags: [Notificaciones]
    summary: Cambia el estado de una notificación concreta
    security:
      - Bearer: []
    parameters:
      - in: path
        name: notificacion_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [leido]
          properties:
            leido:
              type: boolean
    responses:
      200:
        description: Notificación actualizada
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
      404:
        description: Notificación no encontrada
        schema:
          $ref: '#/definitions/Error'
    """
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
