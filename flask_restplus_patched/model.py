from apispec.ext.marshmallow.swagger import fields2jsonschema, field2property
import flask_marshmallow
from werkzeug import cached_property

from flask_restplus.model import Model as OriginalModel


class SchemaMixin(object):

    def __deepcopy__(self, memo):
        # XXX: Flask-RESTplus makes unnecessary data copying, while
        # marshmallow.Schema doesn't support deepcopyng.
        return self


class Schema(SchemaMixin, flask_marshmallow.Schema):
    pass


if flask_marshmallow.has_sqla:
    class ModelSchema(SchemaMixin, flask_marshmallow.sqla.ModelSchema):
        pass


class DefaultHTTPErrorSchema(Schema):
    status = flask_marshmallow.base_fields.Integer()
    message = flask_marshmallow.base_fields.String()

    def __init__(self, http_code, **kwargs):
        super(DefaultHTTPErrorSchema, self).__init__(**kwargs)
        self.fields['status'].default = http_code


class Model(OriginalModel):

    def __init__(self, name, model, **kwargs):
        # XXX: Wrapping with __schema__ is not a very elegant solution.
        super(Model, self).__init__(name, {'__schema__': model}, **kwargs)

    @cached_property
    def __schema__(self):
        schema = self['__schema__']
        if isinstance(schema, flask_marshmallow.Schema):
            return fields2jsonschema(schema.fields)
        elif isinstance(schema, flask_marshmallow.base_fields.FieldABC):
            return field2property(schema)
        raise NotImplementedError()
