"""API del Museo — lectura pública + escritura de aportes (fase 2).

Lectura: dataset del museo desde las tablas reales (/api/museo/*).
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
from app.services import limite
from app.services import museo
from app.utils.response import json_error, json_ok

museo_bp = Blueprint("museo", __name__)
contenido_create_schema = ContenidoCreateSchema()

# Límites de escritura por usuario (ventana deslizante persistente).
MAX_APORTES = 10
VENTANA_APORTES = 3600        # 1 hora
MAX_COMENTARIOS = 20
VENTANA_COMENTARIOS = 600     # 10 minutos

_SECCIONES = {
    "colecciones": museo.colecciones,
    "noticias": museo.noticias,
    "linea-tiempo": museo.linea_tiempo,
    "eventos": museo.eventos,
    "contenidos": museo.contenidos_publicados,
    "hall": museo.hall_fama,
    "insignias": museo.insignias,
    "usuarios": museo.usuarios_publicos,
    "grupos": museo.grupos_investigacion,
    "logros": museo.logros,
    "docentes": museo.opciones_docentes_publicas,
    "kpi": museo.kpis,
}


@museo_bp.get("/data")
def data():
    """Dataset público completo del museo
    ---
    tags: [Museo]
    summary: Snapshot público (sin cola interna ni emails)
    responses:
      200:
        description: Dataset JSON del museo
        schema:
          type: object
    """
    return jsonify(museo.dataset_publico())


@museo_bp.get("/<seccion>")
def seccion(seccion: str):
    """Sección del museo por nombre
    ---
    tags: [Museo]
    summary: Una sección del dataset (colecciones, noticias, eventos, …)
    parameters:
      - in: path
        name: seccion
        required: true
        type: string
        enum: [colecciones, noticias, linea-tiempo, eventos, contenidos, hall, insignias, usuarios, grupos, logros, docentes, kpi]
    responses:
      200:
        description: Contenido de la sección
        schema:
          type: object
      404:
        description: Sección desconocida
        schema:
          $ref: '#/definitions/Error'
    """
    fn = _SECCIONES.get(seccion)
    if fn is None:
        return json_error(f"Sección desconocida: {seccion}", 404)
    return jsonify(fn())


@museo_bp.post("/contenidos")
@jwt_required()
def crear_contenido():
    """Registrar un aporte de contenido
    ---
    tags: [Museo]
    summary: Crea la pieza en estado pendiente (cola de validación docente)
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/ContenidoCreate'
    responses:
      201:
        description: Aporte creado en estado pendiente
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
      400:
        description: Validación fallida
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      403:
        description: El rol no puede aportar contenido
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Usuario no encontrado
        schema:
          $ref: '#/definitions/Error'
      429:
        description: Límite de aportes por hora alcanzado
        schema:
          $ref: '#/definitions/Error'
    """
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    if not contenido_svc.puede_aportar(usuario):
        return json_error("Tu rol no puede aportar contenido", 403)

    clave_limite = f"aporte:{usuario.id}"
    if limite.bloqueado(clave_limite, MAX_APORTES, VENTANA_APORTES):
        return json_error("Has enviado demasiados aportes. Espera un momento.", 429)

    try:
        data = contenido_create_schema.load(request.get_json(silent=True) or {})
    except ValidationError as err:
        return json_error(err.messages, 400)

    pieza = contenido_svc.crear_contenido(data, usuario)
    limite.registrar(clave_limite)
    forma = next((c for c in museo.contenidos() if c["id"] == str(pieza.id)), pieza.to_dict())
    return json_ok(forma, 201)


@museo_bp.put("/contenidos/<int:contenido_id>/docente-revision")
@role_required("docente", "admin")
def revisar_docente(contenido_id: int):
    """Revisión docente de un aporte
    ---
    tags: [Museo]
    summary: Aprueba o devuelve un aporte en revisión
    security:
      - Bearer: []
    parameters:
      - in: path
        name: contenido_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [aprobar]
          properties:
            aprobar:
              type: boolean
              description: true aprueba, false devuelve con observaciones
            nota:
              type: string
              description: Observaciones al devolver
    responses:
      200:
        description: Decisión registrada (id, estado, observaciones)
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      403:
        description: No puede revisar este aporte
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Contenido no encontrado
        schema:
          $ref: '#/definitions/Error'
    """
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
    """Listar comentarios de una pieza
    ---
    tags: [Museo]
    summary: Comentarios públicos de un contenido
    parameters:
      - in: path
        name: contenido_id
        required: true
        type: integer
    responses:
      200:
        description: Lista de comentarios
        schema:
          type: array
          items:
            type: object
    """
    return jsonify(interaccion_svc.comentarios_de(contenido_id))


@museo_bp.post("/contenidos/<int:contenido_id>/comentarios")
@jwt_required()
def crear_comentario(contenido_id: int):
    """Publicar comentario en una pieza
    ---
    tags: [Museo]
    summary: Crea un comentario autenticado (con límite por ventana)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: contenido_id
        required: true
        type: integer
      - in: body
        name: body
        required: true
        schema:
          type: object
          required: [texto]
          properties:
            texto:
              type: string
    responses:
      201:
        description: Comentario creado
        schema:
          type: object
      400:
        description: Texto inválido
        schema:
          $ref: '#/definitions/Error'
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Contenido o usuario no encontrado
        schema:
          $ref: '#/definitions/Error'
      429:
        description: Demasiados comentarios seguidos
        schema:
          $ref: '#/definitions/Error'
    """
    usuario = db.session.get(Usuario, int(get_jwt_identity()))
    if not usuario:
        return json_error("Usuario no encontrado", 404)
    if db.session.get(Contenido, contenido_id) is None:
        return json_error("Contenido no encontrado", 404)

    clave_limite = f"comentario:{usuario.id}"
    if limite.bloqueado(clave_limite, MAX_COMENTARIOS, VENTANA_COMENTARIOS):
        return json_error("Has comentado demasiado seguido. Espera un momento.", 429)

    data = request.get_json(silent=True) or {}
    try:
        forma = interaccion_svc.crear_comentario(usuario, contenido_id, data.get("texto"))
    except ValueError as err:
        return json_error(str(err), 400)
    limite.registrar(clave_limite)
    return json_ok(forma, 201)


@museo_bp.delete("/comentarios/<int:comentario_id>")
@jwt_required()
def eliminar_comentario(comentario_id: int):
    """Eliminar comentario propio (o cualquiera si eres admin)
    ---
    tags: [Museo]
    summary: Borra un comentario; 403 si no eres autor ni admin
    security:
      - Bearer: []
    parameters:
      - in: path
        name: comentario_id
        required: true
        type: integer
    responses:
      200:
        description: Comentario eliminado
        schema:
          type: object
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      403:
        description: No es el autor ni admin
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Usuario no encontrado
        schema:
          $ref: '#/definitions/Error'
    """
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
    """Ids de favoritos del usuario
    ---
    tags: [Favoritos]
    summary: Lista de ids marcados por el usuario autenticado
    security:
      - Bearer: []
    responses:
      200:
        description: Ids favoritos
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
              properties:
                ids:
                  type: array
                  items:
                    type: string
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
    """
    ids = favoritos_svc.ids_de(int(get_jwt_identity()))
    return json_ok({"ids": [str(i) for i in ids]})


@museo_bp.post("/favoritos/<int:contenido_id>")
@jwt_required()
def alternar_favorito(contenido_id: int):
    """Alternar favorito de una pieza
    ---
    tags: [Favoritos]
    summary: Si no está lo agrega; si está lo quita (toggle)
    security:
      - Bearer: []
    parameters:
      - in: path
        name: contenido_id
        required: true
        type: integer
    responses:
      200:
        description: Estado nuevo del favorito y lista completa de ids
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
              properties:
                favorito:
                  type: boolean
                ids:
                  type: array
                  items:
                    type: string
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
      404:
        description: Contenido no encontrado
        schema:
          $ref: '#/definitions/Error'
    """
    if not favoritos_svc.existe_contenido(contenido_id):
        return json_error("Contenido no encontrado", 404)
    activo, ids = favoritos_svc.alternar(int(get_jwt_identity()), contenido_id)
    return json_ok({"favorito": activo, "ids": [str(i) for i in ids]})


@museo_bp.delete("/favoritos/<int:contenido_id>")
@jwt_required()
def eliminar_favorito(contenido_id: int):
    """Quitar un favorito
    ---
    tags: [Favoritos]
    summary: Elimina un id de la lista de favoritos
    security:
      - Bearer: []
    parameters:
      - in: path
        name: contenido_id
        required: true
        type: integer
    responses:
      200:
        description: Lista de ids restantes
        schema:
          type: object
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
    """
    ids = favoritos_svc.quitar(int(get_jwt_identity()), contenido_id)
    return json_ok({"ids": [str(i) for i in ids]})


@museo_bp.delete("/favoritos")
@jwt_required()
def limpiar_favoritos():
    """Vaciar la lista de favoritos
    ---
    tags: [Favoritos]
    summary: Elimina todos los favoritos del usuario
    security:
      - Bearer: []
    responses:
      200:
        description: Lista vacía
        schema:
          type: object
          properties:
            ok:
              type: boolean
            data:
              type: object
              properties:
                ids:
                  type: array
                  items:
                    type: string
      401:
        description: Sin token
        schema:
          $ref: '#/definitions/Error'
    """
    favoritos_svc.limpiar(int(get_jwt_identity()))
    return json_ok({"ids": []})
