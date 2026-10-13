"""Sembrador del dataset demo → tablas reales.

Carga app/static/data/demo-data.json en la BD (colecciones, usuarios,
semilleros, contenidos, cola de validación, línea del tiempo, eventos,
hall de la fama, noticias y premios). Idempotente: si ya hay colecciones,
omite la siembra. Las cuentas demo quedan con password = "123456".
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from app.extensions import db
from app.models.contenido import Coleccion, Contenido, Etiqueta
from app.models.cronologia import CronologiaHito, Evento
from app.models.insignia import Insignia, UsuarioInsignia
from app.models.premio import Premio
from app.models.publicacion import HallFama, Noticia
from app.models.semillero import Semillero
from app.models.usuario import Usuario
from app.services.auth import hash_password

DATA_PATH = Path(__file__).resolve().parent.parent / "static" / "data" / "demo-data.json"
PASSWORD_DEMO = "123456"


def _cargar_json() -> dict:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _nombre_apellidos(nombre: str) -> set[str]:
    """Tokens significativos de un nombre (para emparejar líderes/docentes)."""
    return {t for t in nombre.replace("–", " ").split() if len(t) > 3 and t[0].isupper()}


def _buscar_usuario_por_nombre(nombre: str, por_id: dict[str, int], datos: dict) -> int | None:
    if not nombre:
        return None
    for u in datos.get("users", []):
        if u["name"] == nombre:
            return por_id.get(u["id"])
    # coincidencia difusa por apellidos/tokens (p.ej. "Dra. Paola Andrea Jiménez" ↔ "Dra. Paola Jiménez")
    tokens = _nombre_apellidos(nombre)
    mejor, mejor_puntaje = None, 0
    for u in datos.get("users", []):
        interseccion = len(tokens & _nombre_apellidos(u["name"]))
        if interseccion > mejor_puntaje:
            mejor, mejor_puntaje = por_id.get(u["id"]), interseccion
    return mejor if mejor_puntaje >= 2 else None


def _obtener_o_crear_etiqueta(nombre: str) -> Etiqueta:
    et = Etiqueta.query.filter_by(nombre=nombre).first()
    if et is None:
        et = Etiqueta(nombre=nombre)
        db.session.add(et)
        db.session.flush()
    return et


def _sembrar_insignias(datos: dict) -> dict[str, int]:
    ids = {}
    for b in datos.get("badges", []):
        ins = Insignia(slug=b["id"], nombre=b["name"], icono=b.get("icon"), descripcion=None)
        db.session.add(ins)
        db.session.flush()
        ids[b["id"]] = ins.id
    return ids


def _sembrar_colecciones(datos: dict) -> dict[str, int]:
    ids = {}
    for c in datos.get("collections", []):
        col = Coleccion(
            slug=c["id"], titulo=c["title"], descripcion=c.get("description"),
            icono=c.get("icon"), imagen=c.get("image"),
        )
        db.session.add(col)
        db.session.flush()
        ids[c["id"]] = col.id
    return ids


def _sembrar_semilleros(datos: dict) -> dict[str, int]:
    ids = {}
    for g in datos.get("researchGroups", []):
        sem = Semillero(
            nombre=g["name"], categoria=g.get("category"),
            descripcion=g.get("description"), imagen=g.get("image"),
        )
        db.session.add(sem)
        db.session.flush()
        ids[g["id"]] = sem.id
    return ids


def _sembrar_usuarios(datos: dict, insignias: dict[str, int], semilleros: dict[str, int]) -> dict[str, int]:
    ids = {}
    for u in datos.get("users", []):
        usuario = Usuario(
            nombre=u["name"],
            email=u["email"],
            password_hash=hash_password(PASSWORD_DEMO),
            rol=u.get("role", "visitante"),
            estado=u.get("status", "activo"),
            puntos=u.get("points", 0),
            semillero_id=semilleros.get(u.get("researchGroupId")),
            anio_grado=u.get("graduationYear"),
            cargo_actual=u.get("currentPosition"),
            created_at=(
                datetime.strptime(u["joinDate"], "%Y-%m-%d") if u.get("joinDate") else None
            ),
        )
        db.session.add(usuario)
        db.session.flush()
        ids[u["id"]] = usuario.id
        for bid in u.get("badgeIds", []):
            if bid in insignias:
                db.session.add(UsuarioInsignia(usuario_id=usuario.id, insignia_id=insignias[bid]))
    return ids


def _sembrar_noticias(datos: dict) -> None:
    for n in datos.get("news", []):
        db.session.add(Noticia(
            titulo=n["title"], resumen=n.get("excerpt"), fecha=n.get("date"),
            categoria=n.get("category"), imagen=n.get("image"), estado="publicado",
        ))


def _sembrar_contenidos(datos: dict, colecciones: dict[str, int], usuarios_id: dict[str, int]) -> dict[str, int]:
    """contentItems + contentQueue → Contenidos. Los de cola duplicados de
    contentItems (misma título) no se vuelven a crear: el ya existente porta
    el estado pendiente/devuelto y alimenta ambas vistas del contrato."""
    por_nombre = {
        u["name"]: usuarios_id.get(u["id"]) for u in datos.get("users", [])
    }
    mapa_id: dict[str, int] = {}
    titulos_vistos: set[str] = set()

    def crear(item: dict) -> None:
        cont = Contenido(
            titulo=item["title"],
            categoria=item.get("category"),
            descripcion=item.get("description"),
            fecha=item.get("date"),
            imagen=item.get("image"),
            autor=item.get("author"),
            estado=item.get("status", "borrador"),
            observaciones=item.get("reviewNote"),
            coleccion_id=colecciones.get(item.get("category")),
            creador_id=por_nombre.get(item.get("submittedBy")) if item.get("submittedBy") else None,
        )
        db.session.add(cont)
        db.session.flush()
        cont.etiquetas = [_obtener_o_crear_etiqueta(t) for t in item.get("tags", [])]
        mapa_id[item["id"]] = cont.id
        titulos_vistos.add(cont.titulo)

    for item in datos.get("contentItems", []):
        crear(item)
    for item in datos.get("contentQueue", []):
        if item["title"] not in titulos_vistos:
            crear(item)
    db.session.flush()
    return mapa_id


def _sembrar_cronologia(datos: dict, contenidos_map: dict[str, int]) -> None:
    for h in datos.get("timeline", []):
        db.session.add(CronologiaHito(
            anio=h.get("year"), titulo=h["title"], descripcion=h.get("description"),
            tipo=h.get("type"), contenido_id=contenidos_map.get(h.get("itemId")),
            estado="publicado",
        ))


def _sembrar_eventos(datos: dict) -> None:
    for e in datos.get("events", []):
        db.session.add(Evento(
            titulo=e["title"], fecha=e.get("date"), hora=e.get("time"),
            ubicacion=e.get("location"), tipo=e.get("type"),
            descripcion=e.get("description"), estado="publicado",
        ))


def _sembrar_hall(datos: dict) -> None:
    for m in datos.get("hallMembers", []):
        db.session.add(HallFama(
            nombre=m["name"], titulo=m.get("title"), anio=m.get("year"),
            logro=m.get("achievement"), imagen=m.get("image"),
            categoria=m.get("category"), estado="publicado",
        ))


def _sembrar_premios(datos: dict) -> None:
    for a in datos.get("achievements", []):
        db.session.add(Premio(
            nombre=a["title"], anio=a.get("year"), lugar=a.get("institution"),
            descripcion=a.get("description"), categoria=a.get("category"),
            imagen=a.get("image"), estado="publicado",
        ))


def _asignar_lideres(datos: dict, semilleros: dict[str, int], usuarios_id: dict[str, int]) -> None:
    for g in datos.get("researchGroups", []):
        lider_id = _buscar_usuario_por_nombre(g.get("lead"), usuarios_id, datos)
        if lider_id:
            db.session.get(Semillero, semilleros[g["id"]]).lider_id = lider_id


def _sembrar_cuentas_demo(datos: dict) -> None:
    """demoAccounts pueden referir emails no presentes en users (p. ej.
    estudiante@/docente@). Se crean como usuarios reales con password demo
    para que /api/auth/login funcione desde la fase 1."""
    emails_existentes = {u.email for u in Usuario.query.all()}
    for acc in datos.get("demoAccounts", []):
        if acc["email"] in emails_existentes:
            continue
        db.session.add(Usuario(
            nombre=f"{acc.get('label', acc['role']).capitalize()} Demo",
            email=acc["email"],
            password_hash=hash_password(acc.get("password", PASSWORD_DEMO)),
            rol=acc["role"],
            estado="activo",
        ))


def seed_desde_demo() -> bool:
    """Siembra el dataset demo si la BD aún no tiene datos. Retorna True si sembró."""
    if Coleccion.query.count() > 0:
        return False

    datos = _cargar_json()

    insignias = _sembrar_insignias(datos)
    colecciones = _sembrar_colecciones(datos)
    semilleros = _sembrar_semilleros(datos)
    usuarios_id = _sembrar_usuarios(datos, insignias, semilleros)
    _sembrar_cuentas_demo(datos)
    _sembrar_noticias(datos)
    contenidos_map = _sembrar_contenidos(datos, colecciones, usuarios_id)
    _sembrar_cronologia(datos, contenidos_map)
    _sembrar_eventos(datos)
    _sembrar_hall(datos)
    _sembrar_premios(datos)
    _asignar_lideres(datos, semilleros, usuarios_id)

    db.session.commit()
    return True
