from functools import wraps

from flask_jwt_extended import get_jwt, jwt_required

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
