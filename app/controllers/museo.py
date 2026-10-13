"""API del Museo — lectura pública + escritura de aportes (fase 2).

Lectura: contrato idéntico a demo-data.json (tablas reales vía /api/museo/*).
Escritura: POST /contenidos requiere JWT de usuario autenticado y crea la
pieza en estado 'pendiente' (cola de validación del flujo general).
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from marshmallow import ValidationError

from app.extensions import db
from app.models.usuario import Usuario
from app.schemas.contenido import ContenidoCreateSchema
from app.services import contenido as contenido_svc
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
    "cola": museo.cola_contenidos,
    "hall": museo.hall_fama,
    "insignias": museo.insignias,
    "usuarios": museo.usuarios,
    "grupos": museo.grupos_investigacion,
    "logros": museo.logros,
    "docentes": museo.opciones_docentes,
    "kpi": museo.kpis,
}


@museo_bp.get("/data")
def data():
    """Dataset completo (mismo contrato crudo que /api/demo-data)."""
    return jsonify(museo.dataset())


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
