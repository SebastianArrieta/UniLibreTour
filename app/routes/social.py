from flask import Blueprint, request

from app.extensions import db
from app.middleware.auth import role_required
from app.models.insignia import Insignia, UsuarioInsignia
from app.models.interaccion import Comentario, Reaccion
from app.models.notificacion import Notificacion
from app.utils.response import json_error, json_ok

notificaciones_bp = Blueprint("notificaciones", __name__)
insignias_bp = Blueprint("insignias", __name__)
social_bp = Blueprint("social", __name__)


# ── Notificaciones ────────────────────────────────────────────────────────────

@notificaciones_bp.get("")
@role_required("visitante", "guia", "admin")
def listar_notificaciones():
    from flask_jwt_extended import get_jwt_identity
    usuario_id = int(get_jwt_identity())
    notifs = db.session.execute(
        db.select(Notificacion).where(Notificacion.usuario_id == usuario_id)
    ).scalars().all()
    return json_ok([n.to_dict() for n in notifs])


@notificaciones_bp.put("/<int:notif_id>/leer")
@role_required("visitante", "guia", "admin")
def marcar_leida(notif_id: int):
    from flask_jwt_extended import get_jwt_identity
    notif = db.session.get(Notificacion, notif_id)
    if not notif or notif.usuario_id != int(get_jwt_identity()):
        return json_error("Notificación no encontrada", 404)
    notif.leido = True
    db.session.commit()
    return json_ok(notif.to_dict())


@notificaciones_bp.delete("/<int:notif_id>")
@role_required("visitante", "guia", "admin")
def eliminar_notificacion(notif_id: int):
    from flask_jwt_extended import get_jwt_identity
    notif = db.session.get(Notificacion, notif_id)
    if not notif or notif.usuario_id != int(get_jwt_identity()):
        return json_error("Notificación no encontrada", 404)
    db.session.delete(notif)
    db.session.commit()
    return json_ok({"mensaje": "Notificación eliminada"})


# ── Insignias ─────────────────────────────────────────────────────────────────

@insignias_bp.get("")
def listar_insignias():
    insignias = db.session.execute(db.select(Insignia)).scalars().all()
    return json_ok([i.to_dict() for i in insignias])


@insignias_bp.get("/<int:insignia_id>")
def obtener_insignia(insignia_id: int):
    insignia = db.session.get(Insignia, insignia_id)
    if not insignia:
        return json_error("Insignia no encontrada", 404)
    return json_ok(insignia.to_dict())


@insignias_bp.post("")
@role_required("admin")
def crear_insignia():
    data = request.get_json(silent=True) or {}
    if not data.get("nombre"):
        return json_error("El campo 'nombre' es obligatorio", 400)
    insignia = Insignia(
        nombre=data["nombre"],
        descripcion=data.get("descripcion"),
        icono=data.get("icono"),
    )
    db.session.add(insignia)
    db.session.commit()
    return json_ok(insignia.to_dict(), 201)


@insignias_bp.post("/<int:insignia_id>/otorgar/<int:usuario_id>")
@role_required("admin")
def otorgar_insignia(insignia_id: int, usuario_id: int):
    if db.session.get(UsuarioInsignia, (usuario_id, insignia_id)):
        return json_error("El usuario ya tiene esta insignia", 400)
    ui = UsuarioInsignia(usuario_id=usuario_id, insignia_id=insignia_id)
    db.session.add(ui)
    db.session.commit()
    return json_ok(ui.to_dict(), 201)


# ── Comentarios y Reacciones (polimórficos) ───────────────────────────────────

@social_bp.get("/comentarios")
def listar_comentarios():
    entidad_tipo = request.args.get("entidad_tipo")
    entidad_id = request.args.get("entidad_id", type=int)
    query = db.select(Comentario)
    if entidad_tipo:
        query = query.where(Comentario.entidad_tipo == entidad_tipo)
    if entidad_id:
        query = query.where(Comentario.entidad_id == entidad_id)
    comentarios = db.session.execute(query).scalars().all()
    return json_ok([c.to_dict() for c in comentarios])


@social_bp.post("/comentarios")
@role_required("visitante", "guia", "admin")
def crear_comentario():
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    if not all(k in data for k in ("entidad_tipo", "entidad_id", "texto")):
        return json_error("Se requiere 'entidad_tipo', 'entidad_id' y 'texto'", 400)
    comentario = Comentario(
        usuario_id=int(get_jwt_identity()),
        entidad_tipo=data["entidad_tipo"],
        entidad_id=data["entidad_id"],
        texto=data["texto"],
    )
    db.session.add(comentario)
    db.session.commit()
    return json_ok(comentario.to_dict(), 201)


@social_bp.delete("/comentarios/<int:comentario_id>")
@role_required("visitante", "guia", "admin")
def eliminar_comentario(comentario_id: int):
    from flask_jwt_extended import get_jwt_identity
    comentario = db.session.get(Comentario, comentario_id)
    if not comentario:
        return json_error("Comentario no encontrado", 404)
    if comentario.usuario_id != int(get_jwt_identity()):
        return json_error("No puedes eliminar este comentario", 403)
    db.session.delete(comentario)
    db.session.commit()
    return json_ok({"mensaje": "Comentario eliminado"})


@social_bp.post("/reacciones")
@role_required("visitante", "guia", "admin")
def reaccionar():
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    if not all(k in data for k in ("entidad_tipo", "entidad_id", "tipo")):
        return json_error("Se requiere 'entidad_tipo', 'entidad_id' y 'tipo'", 400)
    usuario_id = int(get_jwt_identity())
    pk = (usuario_id, data["entidad_tipo"], data["entidad_id"])
    reaccion = db.session.get(Reaccion, pk)
    if reaccion:
        reaccion.tipo = data["tipo"]
    else:
        reaccion = Reaccion(
            usuario_id=usuario_id,
            entidad_tipo=data["entidad_tipo"],
            entidad_id=data["entidad_id"],
            tipo=data["tipo"],
        )
        db.session.add(reaccion)
    db.session.commit()
    return json_ok(reaccion.to_dict())


@social_bp.delete("/reacciones")
@role_required("visitante", "guia", "admin")
def quitar_reaccion():
    from flask_jwt_extended import get_jwt_identity
    data = request.get_json(silent=True) or {}
    usuario_id = int(get_jwt_identity())
    reaccion = db.session.get(Reaccion, (usuario_id, data.get("entidad_tipo"), data.get("entidad_id")))
    if not reaccion:
        return json_error("Reacción no encontrada", 404)
    db.session.delete(reaccion)
    db.session.commit()
    return json_ok({"mensaje": "Reacción eliminada"})
