from marshmallow import Schema, fields, validate


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=1, max=128), load_only=True)


class RegisterSchema(Schema):
    nombre = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128), load_only=True)
    rol = fields.Str(
        load_default="estudiante",
        validate=validate.OneOf(["estudiante", "docente", "egresado"]),
    )
