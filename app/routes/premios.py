from flask import Blueprint, request

from app.extensions import db
from app.middleware.auth import role_required
from app.models.premio import Premio, PremioParticipante
from app.utils.response import json_error, json_ok

premios_bp = Blueprint("premios", __name__)

_CAMPOS = ("nombre", "anio", "lugar", "descripcion", "estado", "observaciones")


@premios_bp.get("")
def listar():
    premios = db.session.execute(db.select(Premio)).scalars().all()
    return json_ok([p.to_dict() for p in premios])


@premios_bp.get("/<int:premio_id>")
def obtener(premio_id: int):
    premio = db.session.get(Premio, premio_id)
    if not premio:
        return json_error("Premio no encontrado", 404)
    return json_ok(premio.to_dict())


@premios_bp.post("")
@role_required("admin", "guia")
def crear():
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    if not data.get("nombre"):
        return json_error("El campo 'nombre' es obligatorio", 400)
    premio = Premio(**{k: v for k, v in data.items() if k in _CAMPOS})
    premio.creador_id = int(get_jwt_identity())
    db.session.add(premio)
    db.session.commit()
    return json_ok(premio.to_dict(), 201)


@premios_bp.put("/<int:premio_id>")
@role_required("admin", "guia")
def actualizar(premio_id: int):
    premio = db.session.get(Premio, premio_id)
    if not premio:
        return json_error("Premio no encontrado", 404)
    data = request.get_json(silent=True) or {}
    for campo in _CAMPOS:
        if campo in data:
            setattr(premio, campo, data[campo])
    db.session.commit()
    return json_ok(premio.to_dict())


@premios_bp.delete("/<int:premio_id>")
@role_required("admin")
def eliminar(premio_id: int):
    premio = db.session.get(Premio, premio_id)
    if not premio:
        return json_error("Premio no encontrado", 404)
    db.session.delete(premio)
    db.session.commit()
    return json_ok({"mensaje": "Premio eliminado"})


# ── Participantes ─────────────────────────────────────────────────────────────

@premios_bp.get("/<int:premio_id>/participantes")
def listar_participantes(premio_id: int):
    participantes = db.session.execute(
        db.select(PremioParticipante).where(PremioParticipante.premio_id == premio_id)
    ).scalars().all()
    return json_ok([p.to_dict() for p in participantes])


@premios_bp.post("/<int:premio_id>/participantes")
@role_required("admin", "guia")
def agregar_participante(premio_id: int):
    data = request.get_json(silent=True) or {}
    usuario_id = data.get("usuario_id")
    if not usuario_id:
        return json_error("Se requiere 'usuario_id'", 400)
    if db.session.get(PremioParticipante, (premio_id, usuario_id)):
        return json_error("El usuario ya es participante", 400)
    participante = PremioParticipante(premio_id=premio_id, usuario_id=usuario_id)
    db.session.add(participante)
    db.session.commit()
    return json_ok(participante.to_dict(), 201)


@premios_bp.delete("/<int:premio_id>/participantes/<int:usuario_id>")
@role_required("admin", "guia")
def quitar_participante(premio_id: int, usuario_id: int):
    participante = db.session.get(PremioParticipante, (premio_id, usuario_id))
    if not participante:
        return json_error("Participante no encontrado", 404)
    db.session.delete(participante)
    db.session.commit()
    return json_ok({"mensaje": "Participante eliminado"})
