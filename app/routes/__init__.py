from flask import Flask

from app.routes.agenda import cronologia_bp, eventos_bp
from app.routes.contenidos import contenidos_bp
from app.routes.evidencias import evidencias_bp
from app.routes.premios import premios_bp
from app.routes.proyectos import proyectos_bp
from app.routes.publicaciones import hall_fama_bp, noticias_bp
from app.routes.semilleros import semilleros_bp
from app.routes.social import insignias_bp, notificaciones_bp, social_bp


def register_routes(app: Flask) -> None:
    """Registra todos los blueprints de la API REST."""
    prefix = "/api"

    app.register_blueprint(contenidos_bp,      url_prefix=f"{prefix}/contenidos")
    app.register_blueprint(proyectos_bp,        url_prefix=f"{prefix}/proyectos")
    app.register_blueprint(premios_bp,          url_prefix=f"{prefix}/premios")
    app.register_blueprint(eventos_bp,          url_prefix=f"{prefix}/eventos")
    app.register_blueprint(cronologia_bp,       url_prefix=f"{prefix}/cronologia")
    app.register_blueprint(noticias_bp,         url_prefix=f"{prefix}/noticias")
    app.register_blueprint(hall_fama_bp,        url_prefix=f"{prefix}/hall-de-la-fama")
    app.register_blueprint(semilleros_bp,       url_prefix=f"{prefix}/semilleros")
    app.register_blueprint(notificaciones_bp,   url_prefix=f"{prefix}/notificaciones")
    app.register_blueprint(insignias_bp,        url_prefix=f"{prefix}/insignias")
    app.register_blueprint(social_bp,           url_prefix=f"{prefix}/social")
    app.register_blueprint(evidencias_bp,       url_prefix=f"{prefix}/evidencias")
