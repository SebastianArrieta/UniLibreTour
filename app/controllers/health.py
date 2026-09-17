from flask import Blueprint

from app.utils.response import json_ok

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return json_ok({"status": "ok", "servidor": "UniLibreTour"})
