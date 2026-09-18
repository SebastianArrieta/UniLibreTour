from flask import Flask

from app.controllers.auth import auth_bp
from app.controllers.health import health_bp
from app.controllers.prototipo import prototipo_bp
from app.controllers.usuarios import usuarios_bp
from app.controllers.views import views_bp


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(views_bp)
    app.register_blueprint(prototipo_bp)
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(usuarios_bp, url_prefix="/api/usuarios")
