import os
from datetime import datetime

from flask import Flask

from app.config import config_by_name
from app.extensions import db, jwt

MESES_ABREV = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGO = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

DAY_SUFFIX = ""

def _parse_fecha(value):
    if isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def _fmt_mes(value):
    dt = _parse_fecha(value)
    if dt is None:
        return value
    return f"{MESES_ABREV[dt.month - 1]} {dt.year}"


def _fmt_fecha(value):
    dt = _parse_fecha(value)
    if dt is None:
        return value
    return f"{dt.day} de {MESES_LARGO[dt.month - 1]} de {dt.year}"


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    env_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env_name, config_by_name["development"]))

    app.url_map.strict_slashes = False

    db.init_app(app)
    jwt.init_app(app)

    app.jinja_env.filters["fmt_mes"] = _fmt_mes
    app.jinja_env.filters["fmt_fecha"] = _fmt_fecha

    from app.controllers import register_blueprints
    from app.models import Usuario  # noqa: F401

    register_blueprints(app)

    with app.app_context():
        db.create_all()
        from app.services.usuario import seed_usuarios

        seed_usuarios()

    return app
