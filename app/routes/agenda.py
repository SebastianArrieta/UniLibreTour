from flask import Blueprint, request

from app.extensions import db
from app.middleware.auth import role_required
from app.models.cronologia import CronologiaHito, Evento
from app.utils.response import json_error, json_ok

eventos_bp = Blueprint("eventos", __name__)
cronologia_bp = Blueprint("cronologia", __name__)

# ── Eventos ───────────────────────────────────────────────────────────────────

_CAMPOS_EVENTO = ("titulo", "fecha", "hora", "ubicacion", "tipo",
                  "descripcion", "estado", "observaciones")


@eventos_bp.get("")
def listar_eventos():
    eventos = db.session.execute(db.select(Evento)).scalars().all()
    return json_ok([e.to_dict() for e in eventos])


@eventos_bp.get("/<int:evento_id>")
def obtener_evento(evento_id: int):
    evento = db.session.get(Evento, evento_id)
    if not evento:
        return json_error("Evento no encontrado", 404)
    return json_ok(evento.to_dict())


@eventos_bp.post("")
@role_required("admin", "guia")
def crear_evento():
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    if not data.get("titulo"):
        return json_error("El campo 'titulo' es obligatorio", 400)
    evento = Evento(**{k: v for k, v in data.items() if k in _CAMPOS_EVENTO})
    evento.creador_id = int(get_jwt_identity())
    db.session.add(evento)
    db.session.commit()
    return json_ok(evento.to_dict(), 201)


@eventos_bp.put("/<int:evento_id>")
@role_required("admin", "guia")
def actualizar_evento(evento_id: int):
    evento = db.session.get(Evento, evento_id)
    if not evento:
        return json_error("Evento no encontrado", 404)
    data = request.get_json(silent=True) or {}
    for campo in _CAMPOS_EVENTO:
        if campo in data:
            setattr(evento, campo, data[campo])
    db.session.commit()
    return json_ok(evento.to_dict())


@eventos_bp.delete("/<int:evento_id>")
@role_required("admin")
def eliminar_evento(evento_id: int):
    evento = db.session.get(Evento, evento_id)
    if not evento:
        return json_error("Evento no encontrado", 404)
    db.session.delete(evento)
    db.session.commit()
    return json_ok({"mensaje": "Evento eliminado"})


# ── Cronología de Hitos ───────────────────────────────────────────────────────

_CAMPOS_HITO = ("anio", "titulo", "descripcion", "tipo", "estado", "observaciones")


@cronologia_bp.get("")
def listar_hitos():
    hitos = db.session.execute(db.select(CronologiaHito)).scalars().all()
    return json_ok([h.to_dict() for h in hitos])


@cronologia_bp.get("/<int:hito_id>")
def obtener_hito(hito_id: int):
    hito = db.session.get(CronologiaHito, hito_id)
    if not hito:
        return json_error("Hito no encontrado", 404)
    return json_ok(hito.to_dict())


@cronologia_bp.post("")
@role_required("admin", "guia")
def crear_hito():
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    if not data.get("titulo"):
        return json_error("El campo 'titulo' es obligatorio", 400)
    hito = CronologiaHito(**{k: v for k, v in data.items() if k in _CAMPOS_HITO})
    hito.creador_id = int(get_jwt_identity())
    db.session.add(hito)
    db.session.commit()
    return json_ok(hito.to_dict(), 201)


@cronologia_bp.put("/<int:hito_id>")
@role_required("admin", "guia")
def actualizar_hito(hito_id: int):
    hito = db.session.get(CronologiaHito, hito_id)
    if not hito:
        return json_error("Hito no encontrado", 404)
    data = request.get_json(silent=True) or {}
    for campo in _CAMPOS_HITO:
        if campo in data:
            setattr(hito, campo, data[campo])
    db.session.commit()
    return json_ok(hito.to_dict())


@cronologia_bp.delete("/<int:hito_id>")
@role_required("admin")
def eliminar_hito(hito_id: int):
    hito = db.session.get(CronologiaHito, hito_id)
    if not hito:
        return json_error("Hito no encontrado", 404)
    db.session.delete(hito)
    db.session.commit()
    return json_ok({"mensaje": "Hito eliminado"})
