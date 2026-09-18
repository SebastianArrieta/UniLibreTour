from flask import Blueprint, render_template

from app.services.usuario import listar_usuarios

views_bp = Blueprint("views", __name__)


@views_bp.get("/usuarios")
def usuarios():
    try:
        lista_usuarios = listar_usuarios()
    except Exception:
        lista_usuarios = []
    return render_template("usuarios.html", usuarios=lista_usuarios)
