from marshmallow import Schema, fields, validate


class ContenidoCreateSchema(Schema):
    """Contrato del frente (nombres en inglés, como demo-data.json)."""

    title = fields.Str(required=True, validate=validate.Length(min=3, max=200))
    category = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    description = fields.Str(required=True, validate=validate.Length(min=10))
    date = fields.Str(load_default=None)
    image = fields.Str(load_default=None)
    author = fields.Str(load_default=None)
    tags = fields.List(fields.Str(), load_default=list)
