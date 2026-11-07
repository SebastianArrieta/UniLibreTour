from datetime import timedelta

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    decode_token,
    get_jwt_identity,
    jwt_required,
    set_access_cookies,
    unset_access_cookies,
)
from marshmallow import ValidationError

from app.extensions import db
from app.models.usuario import Usuario
from app.schemas.auth import LoginSchema
from app.services import museo
from app.services import otp as otp_svc
from app.services.auth import verify_password
from app.services.usuario import obtener_por_email
from app.utils.response import json_error, json_ok

auth_bp = Blueprint("auth", __name__)
login_schema = LoginSchema()


def _token_de(usuario) -> str:
    return create_access_token(
        identity=str(usuario.id),
        additional_claims={"rol": usuario.rol, "email": usuario.email},
    )


def _respuesta_sesion(usuario):
    """Sesión completa: token en el cuerpo (API) y en cookie httpOnly (vistas)."""
    token = _token_de(usuario)
    respuesta, status = json_ok({"access_token": token, "usuario": usuario.to_dict()})
    set_access_cookies(respuesta, token)  # cookie httpOnly para navegación
    return respuesta, status


def _perfil_contrato(usuario_id: int) -> dict | None:
    """Usuario en la forma del contrato demo-data (name/points/badgeIds…)."""
    uid = str(usuario_id)
    return next((u for u in museo.usuarios() if u["id"] == uid), None)


# -----------------------------------------------------------------------------
# Segundo factor (2FA)
# -----------------------------------------------------------------------------
def _secreto() -> str:
    return current_app.config["JWT_SECRET_KEY"]


def _token_desafio(usuario, codigo: str, nonce: str, intentos: int) -> str:
    return create_access_token(
        identity=str(usuario.id),
        additional_claims={
            "rol": usuario.rol,
            "email": usuario.email,
            "scope": "2fa",
            "nonce": nonce,
            "otp": otp_svc.huella(_secreto(), nonce, codigo),
            "att": intentos,
        },
        expires_delta=timedelta(minutes=otp_svc.OTP_TTL_MINUTOS),
    )


def _token_desafio_desde_claims(usuario, claims: dict, intentos: int) -> str:
    """Reemite el desafío conservando nonce y huella (solo suma intentos)."""
    return create_access_token(
        identity=str(usuario.id),
        additional_claims={
            "rol": claims.get("rol", usuario.rol),
            "email": claims.get("email", usuario.email),
            "scope": "2fa",
            "nonce": claims.get("nonce", ""),
            "otp": claims.get("otp", ""),
            "att": intentos,
        },
        expires_delta=timedelta(minutes=otp_svc.OTP_TTL_MINUTOS),
    )


def _respuesta_desafio(usuario, codigo: str, nonce: str, intentos: int = 0):
    payload = {
        "requires_2fa": True,
        "pending_token": _token_desafio(usuario, codigo, nonce, intentos),
        "usuario": usuario.to_dict(),
    }
    if current_app.config.get("OTP_DEV_ECHO") and current_app.config.get("DEBUG"):
        # Sin servidor de correo: en desarrollo el código se muestra para poder
        # completar el flujo. En producción configurar OTP_DEV_ECHO=0.
        current_app.logger.info("[2FA] Código para %s: %s", usuario.email, codigo)
        payload["dev_code"] = codigo
    return json_ok(payload)


def _claims_desafio():
    """Lee y valida el token de desafío enviado en Authorization: Bearer."""
    encabezado = request.headers.get("Authorization", "")
    if not encabezado.startswith("Bearer "):
        return None, json_error("Token de verificación requerido", 401)

    try:
        claims = decode_token(encabezado[7:].strip())
    except Exception:
        return None, json_error("Token de verificación inválido o expirado", 401)

    if claims.get("scope") != "2fa":
        return None, json_error("Token de verificación inválido", 401)

    usuario = db.session.get(Usuario, int(claims.get("sub", 0)))
    if not usuario:
        return None, json_error("Usuario no encontrado", 401)

    return (claims, usuario), None


@auth_bp.post("/login")
def login():
    try:
        data = login_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return json_error(err.messages, 400)

    usuario = obtener_por_email(data["email"])
    if not usuario or not verify_password(data["password"], usuario.password_hash):
        return json_error("Credenciales inválidas", 401)

    if usuario.estado != "activo":
        return json_error("Tu cuenta está pendiente de aprobación por un administrador", 403)

    if usuario.two_factor_enabled:
        codigo = otp_svc.generar_codigo()
        return _respuesta_desafio(usuario, codigo, otp_svc.nuevo_nonce())

    return _respuesta_sesion(usuario)


@auth_bp.post("/2fa/verify")
def verificar_2fa():
    datos = request.get_json(silent=True) or {}
    codigo = str(datos.get("codigo", "")).strip()

    par, error = _claims_desafio()
    if error:
        return error
    claims, usuario = par

    intentos = int(claims.get("att", 0))
    if intentos >= otp_svc.OTP_MAX_INTENTOS:
        return json_error("Demasiados intentos fallidos. Inicia sesión de nuevo.", 429)

    if not otp_svc.coincide(
        _secreto(),
        claims.get("nonce", ""),
        codigo,
        claims.get("otp", ""),
    ):
        restantes = otp_svc.OTP_MAX_INTENTOS - (intentos + 1)
        return jsonify({
            "ok": False,
            "error": "Código de verificación incorrecto",
            "pending_token": _token_desafio_desde_claims(usuario, claims, intentos + 1),
            "intentos_restantes": restantes,
        }), 401

    return _respuesta_sesion(usuario)


@auth_bp.post("/2fa/resend")
def reenviar_2fa():
    par, error = _claims_desafio()
    if error:
        return error
    _, usuario = par
    codigo = otp_svc.generar_codigo()
    return _respuesta_desafio(usuario, codigo, otp_svc.nuevo_nonce())


@auth_bp.post("/logout")
def logout():
    respuesta, status = json_ok({"mensaje": "Sesión cerrada"})
    unset_access_cookies(respuesta)
    return respuesta, status


@auth_bp.get("/me")
@jwt_required()
def me():
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    return json_ok(_perfil_contrato(usuario.id) or usuario.to_dict())
