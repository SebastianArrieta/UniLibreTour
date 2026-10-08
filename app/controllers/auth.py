from flask import Blueprint, request
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.schemas.auth import LoginSchema, RegisterSchema
from app.services import museo
from app.services.auth import verify_password
from app.services.usuario import obtener_por_email, registrar_usuario
from app.utils.response import json_error, json_ok

auth_bp = Blueprint("auth", __name__)
login_schema = LoginSchema()
register_schema = RegisterSchema()


def _token_de(usuario) -> str:
    return create_access_token(
        identity=str(usuario.id),
        additional_claims={"rol": usuario.rol, "email": usuario.email},
    )


def _perfil_contrato(usuario_id: int) -> dict | None:
    """Usuario en la forma del contrato demo-data (name/points/badgeIds…)."""
    uid = str(usuario_id)
    return next((u for u in museo.usuarios() if u["id"] == uid), None)


@auth_bp.post("/login")
def login():
    try:
        data = login_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return json_error(err.messages, 400)

    usuario = obtener_por_email(data["email"])
    if not usuario or not verify_password(data["password"], usuario.password_hash):
        return json_error("Credenciales inválidas", 401)

    return json_ok({"access_token": _token_de(usuario), "usuario": usuario.to_dict()})


@auth_bp.post("/register")
def register():
    try:
        data = register_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return json_error(err.messages, 400)

    if obtener_por_email(data["email"]):
        return json_error("El email ya está registrado", 409)

    usuario = registrar_usuario(data)
    return json_ok({"access_token": _token_de(usuario), "usuario": usuario.to_dict()}, 201)


@auth_bp.get("/me")
@jwt_required()
def me():
    from app.models.usuario import Usuario

    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    return json_ok(_perfil_contrato(usuario.id) or usuario.to_dict())
