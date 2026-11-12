from functools import wraps

from flask import redirect, request, url_for
from flask_jwt_extended import current_user, jwt_required, verify_jwt_in_request

from app.utils.response import json_error


def role_required(*roles: str):
    """Autoriza contra el rol actual en BD, no contra el claim del JWT.

    Si un admin cambia el rol de alguien, el cambio aplica al instante (el
    token viejo además queda invalidado por ``token_version``).
    """

    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            usuario = current_user
            if usuario is None or usuario.estado != "activo":
                return json_error("La sesión ya no es válida. Inicia sesión de nuevo.", 401)
            if roles and usuario.rol not in roles:
                return json_error("No tienes permiso", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def web_role_required(*roles: str):
    """Guarda para vistas HTML.

    El usuario se carga desde la BD validando la cookie httpOnly; sin sesión
    válida (o con la cuenta inactiva) se redirige a /login y con un rol no
    autorizado se redirige al inicio.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            destino = request.path
            if request.query_string:
                destino = f"{destino}?{request.query_string.decode('utf-8', 'ignore')}"
            try:
                verify_jwt_in_request(locations=["cookies"])
            except Exception:
                return redirect(url_for("web.login", next=destino))
            usuario = current_user
            if usuario is None or usuario.estado != "activo":
                return redirect(url_for("web.login", next=destino))
            if roles and usuario.rol not in roles:
                return redirect(url_for("web.home"))
            return fn(*args, **kwargs)

        return wrapper

    return decorator
