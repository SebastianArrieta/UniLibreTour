import os

from flask import Flask

from app.config import config_by_name
from app.extensions import db, jwt


def create_app(config_name: str | None = None) -> Flask:
    app = Flask(__name__)
    env_name = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_by_name.get(env_name, config_by_name["development"]))

    app.url_map.strict_slashes = False

    db.init_app(app)
    jwt.init_app(app)

    from app.controllers import register_blueprints
    from app.models import Usuario  # noqa: F401

    register_blueprints(app)

    with app.app_context():
        db.create_all()
        from app.services.usuario import seed_usuarios

        seed_usuarios()

    return app
