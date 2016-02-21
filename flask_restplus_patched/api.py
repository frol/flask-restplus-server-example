from functools import wraps

from flask import jsonify
import flask_marshmallow
from flask_restplus import Api as OriginalApi
from flask_restplus.utils import merge
from webargs.flaskparser import use_args as use_webargs
from werkzeug import cached_property, exceptions as http_exceptions

from .model import Model, DefaultHTTPErrorSchema
from .swagger import Swagger


class Api(OriginalApi):

    @cached_property
    def __schema__(self):
        return Swagger(self).as_dict()

    def init_app(self, app):
        super(Api, self).init_app(app)
        app.errorhandler(http_exceptions.UnprocessableEntity.code)(handle_validation_error)

    def _handle_api_doc(self, cls, doc):
        if doc is False:
            cls.__apidoc__ = False
            return
        ##unshortcut_params_description(doc)
        ##for key in 'get', 'post', 'put', 'delete', 'options', 'head', 'patch':
        ##    if key in doc:
        ##        if doc[key] is False:
        ##            continue
        ##        unshortcut_params_description(doc[key])
        cls.__apidoc__ = merge(getattr(cls, '__apidoc__', {}), doc)

    def model(self, name=None, model=None, **kwargs):
        """
        Register a model.
        """
        if isinstance(model, flask_marshmallow.Schema):
            if not name:
                name = model.__class__.__name__
            api_model = Model(name, model)
            api_model.__apidoc__ = kwargs
            self.models[name] = api_model
            return api_model
        return super(Api, self).model(name, model, **kwargs)

    def parameters(self, parameters, locations=None):
        """
        Register endpoint parameters.
        """
        def decorator(func):
            if locations is None and parameters.many:
                _locations = ('json', )
            else:
                _locations = locations

            return self.doc(params=parameters)(
                self.response(code=http_exceptions.UnprocessableEntity.code)(
                    use_webargs(parameters, locations=_locations)(
                        func
                    )
                )
            )

        return decorator

    def response(self, model=None, code=200, description=None):
        if model is None:
            if code not in http_exceptions.default_exceptions:
                raise ValueError("`model` parameter is required for code %d" % code)
            model = self.model(
                name='HTTPError%dSchema' % code,
                model=DefaultHTTPErrorSchema(http_code=code)
            )
        if description is None:
            if code in http_exceptions.default_exceptions:
                description = http_exceptions.default_exceptions[code].description

        def decorator(func_or_class):
            if code in http_exceptions.default_exceptions:
                # If the code is handled by raising an exception, it will
                # produce a response later, so we don't need to apply a dump
                # wrapper.
                decorated_func_or_class = func_or_class
            else:
                def dump_wrapper(func):
                    def dump_decorator(*args, **kwargs):
                        return model.dump(func(*args, **kwargs)).data
                    return dump_decorator

                if isinstance(func_or_class, type):
                    # Make a copy of `method_decorators` as otherwise we will
                    # modify the behaviour of all flask-restful.Resource-based
                    # classes
                    func_or_class.method_decorators = (
                        [dump_wrapper] + func_or_class.method_decorators
                    )
                    decorated_func_or_class = func_or_class
                else:
                    decorated_func_or_class = wraps(func_or_class)(dump_wrapper(func_or_class))

            if isinstance(model, Model):
                api_model = model
            else:
                api_model = self.model(model=model)

            return self.doc(
                responses={
                    code: (
                        description,
                        [api_model] if getattr(model, 'many', False) else api_model
                    ),
                }
            )(decorated_func_or_class)

        return decorator


# Return validation errors as JSON
def handle_validation_error(err):
    exc = err.data['exc']
    return jsonify({
        'status': http_exceptions.UnprocessableEntity.code,
        'message': exc.messages
    }), http_exceptions.UnprocessableEntity.code
