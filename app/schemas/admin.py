from marshmallow import Schema, fields, validate

ROLES_VALIDOS = ["visitante", "estudiante", "docente", "egresado", "admin"]
ESTADOS_VALIDOS = ["activo", "pendiente", "inactivo"]


class HitoCreateSchema(Schema):
    year = fields.Int(required=True, validate=validate.Range(min=1900, max=2100))
    type = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    description = fields.Str(required=True, validate=validate.Length(min=3))
    media = fields.List(fields.Str(), load_default=list)


class PremioCreateSchema(Schema):
    year = fields.Int(required=True, validate=validate.Range(min=1900, max=2100))
    category = fields.Str(load_default="premio", validate=validate.Length(max=100))
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    institution = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(required=True, validate=validate.Length(min=3))
    image = fields.Str(load_default=None)


class ProyectoCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    author = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    date = fields.Str(load_default=None)
    category = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=True, validate=validate.Length(min=10))
    tags = fields.List(fields.Str(), load_default=list)
    image = fields.Str(load_default=None)
    featured = fields.Bool(load_default=False)


class HallCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=150))
    title = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    year = fields.Int(required=True, validate=validate.Range(min=1900, max=2100))
    category = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    achievement = fields.Str(required=True, validate=validate.Length(min=3))
    bio = fields.Str(load_default=None)
    image = fields.Str(load_default=None)
    badges = fields.List(fields.Str(), load_default=list)


class EventoCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    date = fields.Str(required=True, validate=validate.Length(min=4, max=20))
    time = fields.Str(required=True, validate=validate.Length(min=3, max=10))
    type = fields.Str(required=True, validate=validate.Length(min=1, max=50))
    location = fields.Str(required=True, validate=validate.Length(min=2, max=200))
    description = fields.Str(load_default=None)


class NoticiaCreateSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    category = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    date = fields.Str(required=True, validate=validate.Length(min=4, max=20))
    excerpt = fields.Str(required=True, validate=validate.Length(min=3))
    image = fields.Str(load_default=None)


class SemilleroCreateSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=3, max=150))
    category = fields.Str(required=True, validate=validate.OneOf(["semillero", "grupo"]))
    leadId = fields.Int(load_default=None, allow_none=True)
    description = fields.Str(required=True, validate=validate.Length(min=3))
    image = fields.Str(load_default=None, allow_none=True)


class ValidacionSchema(Schema):
    accion = fields.Str(
        required=True,
        validate=validate.OneOf(["aprobar", "devolver", "institucional"]),
    )
    nota = fields.Str(load_default=None)
    tipo = fields.Str(load_default=None)
    fecha_publicacion = fields.Str(load_default=None)
    mensaje = fields.Str(load_default=None)


class UsuarioAdminUpdateSchema(Schema):
    nombre = fields.Str(validate=validate.Length(min=1, max=100))
    email = fields.Email()
    rol = fields.Str(validate=validate.OneOf(ROLES_VALIDOS))
    estado = fields.Str(validate=validate.OneOf(ESTADOS_VALIDOS))


class NotificacionUpdateSchema(Schema):
    leido = fields.Bool(load_default=None)
