from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from marshmallow import ValidationError

from app.schemas.auth import LoginSchema
from app.services.auth import verify_password
from app.services.usuario import obtener_por_email
from app.utils.response import json_error, json_ok

auth_bp = Blueprint("auth", __name__)
login_schema = LoginSchema()


@auth_bp.post("/login")
def login():
    try:
        data = login_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return json_error(err.messages, 400)

    usuario = obtener_por_email(data["email"])
    if not usuario or not verify_password(data["password"], usuario.password_hash):
        return json_error("Credenciales inválidas", 401)

    token = create_access_token(
        identity=str(usuario.id),
        additional_claims={"rol": usuario.rol, "email": usuario.email},
    )
    return json_ok({"access_token": token, "usuario": usuario.to_dict()})
