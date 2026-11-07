"""API del Museo — lectura pública + escritura de aportes (fase 2).

Lectura: contrato idéntico a demo-data.json (tablas reales vía /api/museo/*).
Escritura: POST /contenidos requiere JWT de usuario autenticado y crea la
pieza en estado 'pendiente' (cola de validación del flujo general).
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.middleware.auth import role_required
from app.models.contenido import Contenido
from app.models.usuario import Usuario
from app.schemas.contenido import ContenidoCreateSchema
from app.services import contenido as contenido_svc
from app.services import favoritos as favoritos_svc
from app.services import interaccion as interaccion_svc
from app.services import museo
from app.utils.response import json_error, json_ok

museo_bp = Blueprint("museo", __name__)
contenido_create_schema = ContenidoCreateSchema()

_SECCIONES = {
    "colecciones": museo.colecciones,
    "noticias": museo.noticias,
    "linea-tiempo": museo.linea_tiempo,
    "eventos": museo.eventos,
    "contenidos": museo.contenidos,
    "hall": museo.hall_fama,
    "insignias": museo.insignias,
    "usuarios": museo.usuarios_publicos,
    "grupos": museo.grupos_investigacion,
    "logros": museo.logros,
    "docentes": museo.opciones_docentes,
    "kpi": museo.kpis,
}


@museo_bp.get("/data")
def data():
    """Dataset público (sin cola interna ni emails de usuarios)."""
    return jsonify(museo.dataset_publico())


@museo_bp.get("/<seccion>")
def seccion(seccion: str):
    fn = _SECCIONES.get(seccion)
    if fn is None:
        return json_error(f"Sección desconocida: {seccion}", 404)
    return jsonify(fn())


@museo_bp.post("/contenidos")
@jwt_required()
def crear_contenido():
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    if not contenido_svc.puede_aportar(usuario):
        return json_error("Tu rol no puede aportar contenido", 403)

    try:
        data = contenido_create_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return json_error(err.messages, 400)

    pieza = contenido_svc.crear_contenido(data, usuario)
    forma = next((c for c in museo.contenidos() if c["id"] == str(pieza.id)), pieza.to_dict())
    return json_ok(forma, 201)


@museo_bp.put("/contenidos/<int:contenido_id>/docente-revision")
@role_required("docente", "admin")
def revisar_docente(contenido_id: int):
    """El docente asignado aprueba o devuelve un aporte en revisión."""
    revisor = db.session.get(Usuario, int(get_jwt_identity()))
    contenido = db.session.get(Contenido, contenido_id)
    if not revisor or not contenido:
        return json_error("Contenido no encontrado", 404)

    data = request.get_json(silent=True) or {}
    aprobar = bool(data.get("aprobar"))
    nota = data.get("nota")

    resultado = contenido_svc.decision_docente(contenido, revisor, aprobar, nota)
    if resultado is None:
        return json_error("No puedes revisar este aporte", 403)

    return json_ok({
        "id": resultado.id,
        "estado": resultado.estado,
        "observaciones": resultado.observaciones,
    })


# -----------------------------------------------------------------------------
# Comentarios (reales, ligados a la pieza y al usuario)
# -----------------------------------------------------------------------------
@museo_bp.get("/contenidos/<int:contenido_id>/comentarios")
def listar_comentarios(contenido_id: int):
    return jsonify(interaccion_svc.comentarios_de(contenido_id))


@museo_bp.post("/contenidos/<int:contenido_id>/comentarios")
@jwt_required()
def crear_comentario(contenido_id: int):
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    if db.session.get(Contenido, contenido_id) is None:
        return json_error("Contenido no encontrado", 404)

    data = request.get_json(silent=True) or {}
    try:
        forma = interaccion_svc.crear_comentario(usuario, contenido_id, data.get("texto"))
    except ValueError as err:
        return json_error(str(err), 400)
    return json_ok(forma, 201)


@museo_bp.delete("/comentarios/<int:comentario_id>")
@jwt_required()
def eliminar_comentario(comentario_id: int):
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    if not interaccion_svc.eliminar_comentario(usuario, comentario_id):
        return json_error("No puedes eliminar este comentario", 403)
    return json_ok({"mensaje": "Comentario eliminado"})


# -----------------------------------------------------------------------------
# Favoritos persistentes por usuario
# -----------------------------------------------------------------------------
@museo_bp.get("/favoritos")
@jwt_required()
def listar_favoritos():
    ids = favoritos_svc.ids_de(int(get_jwt_identity()))
    return json_ok({"ids": [str(i) for i in ids]})


@museo_bp.post("/favoritos/<int:contenido_id>")
@jwt_required()
def alternar_favorito(contenido_id: int):
    if not favoritos_svc.existe_contenido(contenido_id):
        return json_error("Contenido no encontrado", 404)
    activo, ids = favoritos_svc.alternar(int(get_jwt_identity()), contenido_id)
    return json_ok({"favorito": activo, "ids": [str(i) for i in ids]})


@museo_bp.delete("/favoritos/<int:contenido_id>")
@jwt_required()
def eliminar_favorito(contenido_id: int):
    ids = favoritos_svc.quitar(int(get_jwt_identity()), contenido_id)
    return json_ok({"ids": [str(i) for i in ids]})


@museo_bp.delete("/favoritos")
@jwt_required()
def limpiar_favoritos():
    favoritos_svc.limpiar(int(get_jwt_identity()))
    return json_ok({"ids": []})
