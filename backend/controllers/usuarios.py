from models.usuario import UsuarioModel
from utils.response import send_json, send_error


def listar(handler):
    usuarios = UsuarioModel.find_all()
    send_json(handler, 200, usuarios)


def obtener(handler):
    usuario_id = handler.path_params[0]
    usuario = UsuarioModel.find_by_id(usuario_id)
    if usuario:
        send_json(handler, 200, usuario)
    else:
        send_error(handler, 404, 'Usuario no encontrado')


def crear(handler):
    data = handler.body
    if not data or 'nombre' not in data or 'email' not in data:
        send_error(handler, 400, 'Nombre y email son requeridos')
        return

    try:
        usuario = UsuarioModel.create(data)
        send_json(handler, 201, usuario)
    except Exception as e:
        send_error(handler, 400, str(e))


def actualizar(handler):
    usuario_id = handler.path_params[0]
    data = handler.body

    usuario = UsuarioModel.update(usuario_id, data)
    if usuario:
        send_json(handler, 200, usuario)
    else:
        send_error(handler, 404, 'Usuario no encontrado')


def eliminar(handler):
    usuario_id = handler.path_params[0]
    eliminado = UsuarioModel.delete(usuario_id)
    if eliminado:
        send_json(handler, 200, {'mensaje': 'Usuario eliminado'})
    else:
        send_error(handler, 404, 'Usuario no encontrado')
