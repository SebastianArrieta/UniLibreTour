from flask import Blueprint, current_app
from sqlalchemy import text

from app.extensions import db
from app.utils.response import json_error, json_ok

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
    except Exception:
        current_app.logger.exception("Health check: la base de datos no responde")
        return json_error("Base de datos no disponible", 503)
    return json_ok({"status": "ok", "servidor": "UniLibreTour", "db": "ok"})
