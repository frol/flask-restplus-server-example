from functools import wraps
import logging

from apispec.ext.marshmallow.swagger import schema2jsonschema
from flask.ext import marshmallow
from werkzeug import cached_property

from flask_restplus.model import ApiModel as OriginalApiModel


log = logging.getLogger(__name__)


class APISchema(object):
   
    def __init__(self, api=None, code=200, description=None, **kwargs):
        super(APISchema, self).__init__(**kwargs)
        self._code = code
        self._description = description
        self.init_api(api)

    def init_api(self, api):
        self._api = api

    def __deepcopy__(self, memo):
        # XXX: Flask-RESTplus makes unnecessary data copying.
        return self

    def __call__(self, func):

        # XXX: This decorator should also support classes.
        # XXX: This decorator should also handle different response codes.
        if self._code == 200:
            @wraps(func)
            def decorator(*args, **kwargs):
                return self.dump(func(*args, **kwargs)).data
            serialized_func = decorator
        else:
            serialized_func = func

        if self._api:
            model = self._api.model(model=self)
            serialized_func = self._api.doc(
                responses={
                    self._code: (self._description, [model] if self.many else model),
                }
            )(serialized_func)
        elif self._api is None:
            log.warning(
                "API Schema %r is applied to %r but documentation won't be "
                "available in Swagger spec because you haven't passed `api` "
                "instance. Pass `False` as api instance to suppress this "
                "warning.", self, func
            )

        return serialized_func


class Schema(APISchema, marshmallow.Schema):
    pass


if marshmallow.has_sqla:
    class ModelSchema(APISchema, marshmallow.sqla.ModelSchema):
        pass
   

class DefaultHTTPErrorSchema(Schema):
    status = marshmallow.base_fields.Integer()
    message = marshmallow.base_fields.String()


class ApiModel(OriginalApiModel):

    def __init__(self, model):
        # XXX: It is not a very elegant solution.
        super(ApiModel, self).__init__({'__schema__': model})

    @cached_property
    def __schema__(self):
        return schema2jsonschema(self['__schema__'])
