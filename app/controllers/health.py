from flask import Blueprint, current_app
from sqlalchemy import text

from app.extensions import db
from app.utils.response import json_error, json_ok

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """Estado del servidor y de la base de datos
    ---
    tags: [Salud]
    responses:
      200:
        description: Servidor y BD operativos
        schema:
          type: object
          properties:
            ok:
              type: boolean
              example: true
            data:
              type: object
              properties:
                status:
                  type: string
                  example: ok
                servidor:
                  type: string
                  example: UniLibreTour
                db:
                  type: string
                  example: ok
      503:
        description: Base de datos no disponible
        schema:
          $ref: '#/definitions/Error'
    """
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("Health check: la base de datos no responde")
        return json_error("Base de datos no disponible", 503)
    return json_ok({"status": "ok", "servidor": "UniLibreTour", "db": "ok"})
