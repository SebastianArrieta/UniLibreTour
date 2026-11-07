import logging
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


def _img(value, archivo="images/placeholder.svg"):
    """URL de la imagen o un marcador local neutro si no hay ninguna."""
    from flask import url_for

    valor = (str(value).strip() if value else "")
    if not valor or valor == "None":
        return url_for("static", filename=archivo)
    return valor


def _img_persona(value):
    return _img(value, "images/persona.svg")


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    env_name = config_name or os.getenv("FLASK_ENV", "development")
    config_cls = config_by_name.get(env_name, config_by_name["development"])
    if hasattr(config_cls, "validar"):
        config_cls.validar()
    app.config.from_object(config_cls)

    app.url_map.strict_slashes = False

    db.init_app(app)
    jwt.init_app(app)

    app.jinja_env.filters["fmt_mes"] = _fmt_mes
    app.jinja_env.filters["fmt_fecha"] = _fmt_fecha
    app.jinja_env.filters["img"] = _img
    app.jinja_env.filters["img_persona"] = _img_persona

    from app.controllers import register_blueprints
    from app import models as _models  # noqa: F401 — registra todos los modelos para db.create_all()

    register_blueprints(app)

    with app.app_context():
        _esperar_bd(app)
        db.create_all()
        _migrar_columnas_faltantes()
        from app.services.catalogo import bootstrap_admin, seed_catalogo

        try:
            seed_catalogo()
            bootstrap_admin()
        except Exception:  # no bloquear el arranque
            db.session.rollback()
            app.logger.exception("No se pudo preparar el catálogo base / administrador inicial")

    @app.context_processor
    def _anio_actual():
        ahora = datetime.now()
        return {"anio_actual": ahora.year, "hoy_iso": ahora.strftime("%Y-%m-%d")}

    return app


def _esperar_bd(app, intentos: int = 30, pausa: float = 2.0) -> None:
    """Espera a que la BD acepte conexiones (arranque simultáneo con MySQL)."""
    import time

    from sqlalchemy import text

    for intento in range(1, intentos + 1):
        try:
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as exc:
            if intento == intentos:
                raise
            app.logger.warning("BD no disponible (%s/%s): %s", intento, intentos, exc.__class__.__name__)
            time.sleep(pausa)


def _migrar_columnas_faltantes() -> None:
    """Parche idempotente de columnas nuevas (el proyecto no usa Alembic y
    ``db.create_all()`` no altera tablas existentes)."""
    from sqlalchemy import inspect, text

    log = logging.getLogger("app.schema")

    try:
        inspector = inspect(db.engine)
        if "cronologia_hitos" in inspector.get_table_names():
            columnas = {c["name"] for c in inspector.get_columns("cronologia_hitos")}
            if "media" not in columnas:
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE cronologia_hitos ADD COLUMN media TEXT"))
                log.info("columna cronologia_hitos.media agregada")

        if "contenidos" in inspector.get_table_names():
            columnas = {c["name"] for c in inspector.get_columns("contenidos")}
            if "docente_id" not in columnas:
                with db.engine.begin() as conn:
                    conn.execute(text("ALTER TABLE contenidos ADD COLUMN docente_id INT NULL"))
                log.info("columna contenidos.docente_id agregada")

        if "favoritos" in inspector.get_table_names():
            columnas = {c["name"] for c in inspector.get_columns("favoritos")}
            if "created_at" not in columnas:
                with db.engine.begin() as conn:
                    if "fecha" in columnas:
                        # Esquema antiguo: renombrar conservando los datos.
                        conn.execute(text(
                            "ALTER TABLE favoritos CHANGE COLUMN fecha created_at "
                            "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                        ))
                    else:
                        conn.execute(text(
                            "ALTER TABLE favoritos ADD COLUMN created_at "
                            "DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP"
                        ))
                log.info("columna favoritos.created_at normalizada")
    except Exception as exc:  # nunca bloquear el arranque por una migración
        log.warning("No se pudo verificar/agregar columnas nuevas: %s", exc)
