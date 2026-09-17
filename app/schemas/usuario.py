from marshmallow import Schema, fields, validate


class UsuarioSchema(Schema):
    id = fields.Int(dump_only=True)
    nombre = fields.Str()
    email = fields.Email()
    rol = fields.Str()
    created_at = fields.DateTime()


class UsuarioCreateSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6, max=128), load_only=True)
    rol = fields.Str(
        load_default="visitante",
        validate=validate.OneOf(["visitante", "guia", "admin"]),
    )


class UsuarioUpdateSchema(Schema):
    nombre = fields.Str(validate=validate.Length(min=1, max=100))
    email = fields.Email()
    rol = fields.Str(validate=validate.OneOf(["visitante", "guia", "admin"]))
