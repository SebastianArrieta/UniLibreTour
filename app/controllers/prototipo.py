"""Blueprint del prototipo — port server-side del mockup React.

Sirve las 28 vistas + el dataset demo en /api/demo-data (mismo contrato que
DataContext del prototipo). Cada ruta pasa a Jinja el dataset completo bajo
claves planas (contentItems, news, collections, ...) mas un contexto base.
"""

import json
from functools import lru_cache
from pathlib import Path

from flask import Blueprint, abort, jsonify, render_template

prototipo_bp = Blueprint("prototipo", __name__)

DATA_PATH = Path(__file__).resolve().parent.parent / "static" / "data" / "demo-data.json"


@lru_cache(maxsize=1)
def demo_data() -> dict:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def _ctx(page: str, **extra) -> dict:
    d = demo_data()
    base = {
        "current_page": page,
        "datos": d,
        "collection_count": len(d.get("collections", [])),
        "contentItems": d.get("contentItems", []),
        "contentQueue": d.get("contentQueue", []),
        "news": d.get("news", []),
        "collections": d.get("collections", []),
        "timeline": d.get("timeline", []),
        "events": d.get("events", []),
        "hallMembers": d.get("hallMembers", []),
        "badges": d.get("badges", []),
        "users": d.get("users", []),
        "kpiData": d.get("kpiData", {}),
        "researchGroups": d.get("researchGroups", []),
        "achievements": d.get("achievements", []),
        "teacherOptions": d.get("teacherOptions", []),
        "demoAccounts": d.get("demoAccounts", []),
        "pointsPerLevel": d.get("pointsPerLevel", 500),
        "maxLevel": d.get("maxLevel", 20),
    }
    base.update(extra)
    return base


def _item(cid: str) -> dict:
    for item in demo_data().get("contentItems", []):
        if item.get("id") == cid:
            return item
    abort(404)


@prototipo_bp.get("/api/demo-data")
def demo_data_endpoint():
    return jsonify(demo_data())


@prototipo_bp.get("/")
def home():
    return render_template("prototipo/home.html", **_ctx("home"))


@prototipo_bp.get("/explorar")
def explorar():
    return render_template("prototipo/explorar.html", **_ctx("explorar"))


@prototipo_bp.get("/buscar")
def buscar():
    return render_template("prototipo/buscar.html", **_ctx("buscar"))


@prototipo_bp.get("/detalle/<cid>")
def detalle(cid):
    return render_template("prototipo/detalle.html", **_ctx("detalle", item=_item(cid)))


@prototipo_bp.get("/hall-fama")
def hall_fama():
    return render_template("prototipo/hall_fama.html", **_ctx("hall-fama"))


@prototipo_bp.get("/semilleros")
def semilleros():
    return render_template("prototipo/semilleros.html", **_ctx("semilleros"))


@prototipo_bp.get("/calendario")
def calendario():
    return render_template("prototipo/calendario.html", **_ctx("calendario"))


@prototipo_bp.get("/cronologia")
def cronologia():
    return render_template("prototipo/cronologia.html", **_ctx("cronologia"))


@prototipo_bp.get("/ranking")
def ranking():
    return render_template("prototipo/ranking.html", **_ctx("ranking"))


@prototipo_bp.get("/perfil")
def perfil():
    return render_template("prototipo/perfil.html", **_ctx("perfil"))


@prototipo_bp.get("/login")
def login():
    return render_template("prototipo/login.html", **_ctx("login"))


@prototipo_bp.get("/2fa")
def two_fa():
    return render_template("prototipo/2fa.html", **_ctx("2fa"))


@prototipo_bp.get("/registro")
def registro():
    return render_template("prototipo/registro.html", **_ctx("registro"))


@prototipo_bp.get("/estudiante")
def estudiante():
    return render_template("prototipo/estudiante.html", **_ctx("est-dashboard"))


@prototipo_bp.get("/estudiante/aportes")
def estudiante_aportes():
    return render_template("prototipo/estudiante_aportes.html", **_ctx("est-aportes"))


@prototipo_bp.get("/estudiante/favoritos")
def estudiante_favoritos():
    return render_template("prototipo/estudiante_favoritos.html", **_ctx("est-favoritos"))


@prototipo_bp.get("/estudiante/contribuir")
def estudiante_contribuir():
    return render_template("prototipo/estudiante_contribuir.html", **_ctx("est-contribuir"))


@prototipo_bp.get("/egresado")
def egresado():
    return render_template("prototipo/egresado.html", **_ctx("egresado"))


@prototipo_bp.get("/docente")
def docente():
    return render_template("prototipo/docente.html", **_ctx("doc-dashboard"))


@prototipo_bp.get("/docente/registrar-evidencia")
def docente_evidencia():
    return render_template("prototipo/docente_evidencia.html", **_ctx("doc-wizard"))


@prototipo_bp.get("/docente/notificaciones")
def docente_notificaciones():
    return render_template("prototipo/docente_notificaciones.html", **_ctx("doc-notificaciones"))


@prototipo_bp.get("/admin")
def admin():
    return render_template("prototipo/admin.html", **_ctx("admin-dashboard"))


@prototipo_bp.get("/admin/anadir")
def admin_anadir():
    return render_template("prototipo/admin_anadir.html", **_ctx("admin-anadir"))


@prototipo_bp.get("/admin/usuarios")
def admin_usuarios():
    return render_template("prototipo/admin_usuarios.html", **_ctx("admin-usuarios"))


@prototipo_bp.get("/admin/cola")
def admin_cola():
    return render_template("prototipo/admin_cola.html", **_ctx("admin-cola"))


@prototipo_bp.get("/admin/validacion/<iid>")
def admin_validacion(iid):
    item = next((i for i in demo_data().get("contentQueue", []) if i.get("id") == iid), None)
    if item is None:
        abort(404)
    return render_template("prototipo/admin_validacion.html", **_ctx("admin-validacion", item=item))


@prototipo_bp.get("/admin/confirmacion/<iid>")
def admin_confirmacion(iid):
    item = next((i for i in demo_data().get("contentItems", []) if i.get("id") == iid), None)
    if item is None:
        abort(404)
    return render_template("prototipo/admin_confirmacion.html", **_ctx("admin-confirmacion", item=item))


@prototipo_bp.get("/admin/registros")
def admin_registros():
    return render_template("prototipo/admin_registros.html", **_ctx("admin-registros"))


@prototipo_bp.get("/admin/hall-registro")
def admin_hall_registro():
    return render_template("prototipo/admin_hall_registro.html", **_ctx("admin-hall-registro"))