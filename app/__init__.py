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
    from app import models as _models  # noqa: F401 — registra todos los modelos para db.create_all()

    register_blueprints(app)

    with app.app_context():
        db.create_all()
        _migrar_columnas_faltantes()
        if app.config.get("SEED_DEMO", True):
            from app.services.usuario import seed_usuarios
            from app.services.seed_demo import seed_desde_demo

            try:
                seed_usuarios()
                seed_desde_demo()
            except Exception as exc:  # no bloquear el arranque; las vistas tienen fallback
                db.session.rollback()
                print(f"[seed] omitido (esquema desactualizado?): {exc}")

    return app


def _migrar_columnas_faltantes() -> None:
    """Parche idempotente de columnas nuevas (el proyecto no usa Alembic y
    ``db.create_all()`` no altera tablas existentes)."""
    from sqlalchemy import inspect, text

    try:
        inspector = inspect(db.engine)
        if "cronologia_hitos" in inspector.get_table_names():
            columnas = {c["name"] for c in inspector.get_columns("cronologia_hitos")}
            if "media" not in columnas:
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE cronologia_hitos ADD COLUMN media TEXT"))
                print("[schema] columna cronologia_hitos.media agregada")

        if "contenidos" in inspector.get_table_names():
            columnas = {c["name"] for c in inspector.get_columns("contenidos")}
            if "docente_id" not in columnas:
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE contenidos ADD COLUMN docente_id INT NULL"))
                print("[schema] columna contenidos.docente_id agregada")
    except Exception as exc:  # nunca bloquear el arranque por una migración
        print(f"[schema] no se pudo verificar/agregar columnas nuevas: {exc}")
