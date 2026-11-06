from functools import wraps

from flask import redirect, request, url_for
from flask_jwt_extended import get_jwt, jwt_required, verify_jwt_in_request

from app.utils.response import json_error


def role_required(*roles: str):
    def decorator(fn):
        @wraps(fn)
        @jwt_required()
        def wrapper(*args, **kwargs):
            claims = get_jwt()
            if claims.get("rol") not in roles:
                return json_error("No tienes permiso", 403)
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def web_role_required(*roles: str):
    """Guarda para vistas HTML.

    El rol se verifica contra el JWT firmado que viaja en la cookie httpOnly,
    nunca contra localStorage. Sin sesión válida se redirige a /login; con un
    rol no autorizado se redirige al inicio.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            destino = request.path
            if request.query_string:
                destino = f"{destino}?{request.query_string.decode('utf-8', 'ignore')}"
            try:
                verify_jwt_in_request(locations=["cookies"])
                claims = get_jwt()
            except Exception:
                return redirect(url_for("web.login", next=destino))
            if roles and claims.get("rol") not in roles:
                return redirect(url_for("web.home"))
            return fn(*args, **kwargs)

        return wrapper

    return decorator
