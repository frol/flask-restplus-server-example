from functools import wraps
import logging

from apispec.ext.marshmallow.swagger import schema2jsonschema
from flask.ext import marshmallow
from marshmallow import SchemaOpts
from werkzeug import cached_property

from flask_restplus.model import ApiModel as OriginalApiModel


log = logging.getLogger(__name__)


class SchemaMixin(object):
   
    def __deepcopy__(self, memo):
        # XXX: Flask-RESTplus makes unnecessary data copying, while
        # marshmallow.Schema doesn't support deepcopyng.
        return self


class Schema(SchemaMixin, marshmallow.Schema):
    pass


if marshmallow.has_sqla:
    class ModelSchema(SchemaMixin, marshmallow.sqla.ModelSchema):
        pass


class DefaultHTTPErrorSchema(Schema):
    status = marshmallow.base_fields.Integer(default=111)
    message = marshmallow.base_fields.String()

    def __init__(self, http_code, **kwargs):
        # XXX: I'm still looking for a better way since there are several
        # places with copies of `_declared_fields`: `fields`, `declared_fields`
        self._declared_fields['status'].default = http_code
        super(DefaultHTTPErrorSchema, self).__init__(**kwargs)


class ApiModel(OriginalApiModel):

    def __init__(self, model):
        # XXX: It is not a very elegant solution.
        super(ApiModel, self).__init__({'__schema__': model})

    @cached_property
    def __schema__(self):
        import logging
        logging.warn("__schema__ field: %s", self['__schema__'].fields.get('status'))
        return schema2jsonschema(self['__schema__'])
