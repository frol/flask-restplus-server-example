from functools import wraps

import flask
import flask_marshmallow
from flask_restplus import Namespace as OriginalNamespace
from flask_restplus.utils import merge
from webargs.flaskparser import parser as webargs_parser
from werkzeug import cached_property, exceptions as http_exceptions

from ._http import HTTPStatus
from .model import Model, DefaultHTTPErrorSchema


class Namespace(OriginalNamespace):

    WEBARGS_PARSER = webargs_parser

    def _handle_api_doc(self, cls, doc):
        if doc is False:
            cls.__apidoc__ = False
            return
        ##unshortcut_params_description(doc)
        ##handle_deprecations(doc)
        ##for key in 'get', 'post', 'put', 'delete', 'options', 'head', 'patch':
        ##    if key in doc:
        ##        if doc[key] is False:
        ##            continue
        ##        unshortcut_params_description(doc[key])
        ##        handle_deprecations(doc[key])
        ##        if 'expect' in doc[key] and not isinstance(doc[key]['expect'], (list, tuple)):
        ##            doc[key]['expect'] = [doc[key]['expect']]
        cls.__apidoc__ = merge(getattr(cls, '__apidoc__', {}), doc)

    def resolve_object(self, object_arg_name, resolver):
        """
        A helper decorator to resolve object instance from arguments (e.g. identity).

        Example:
        >>> @namespace.route('/<int:user_id>')
        ... class MyResource(Resource):
        ...    @namespace.resolve_object(
        ...        object_arg_name='user',
        ...        resolver=lambda kwargs: User.query.get_or_404(kwargs.pop('user_id'))
        ...    )
        ...    def get(self, user):
        ...        # user is a User instance here
        """
        def decorator(func_or_class):
            if isinstance(func_or_class, type):
                func_or_class.method_decorators = (
                    [decorator] + func_or_class.method_decorators
                )
                return func_or_class

            @wraps(func_or_class)
            def wrapper(*args, **kwargs):
                kwargs[object_arg_name] = resolver(kwargs)
                return func_or_class(*args, **kwargs)
            return wrapper
        return decorator

    def model(self, name=None, model=None, mask=None, **kwargs):
        """
        Model registration decorator.
        """
        if isinstance(model, flask_marshmallow.Schema):
            if not name:
                name = model.__class__.__name__
            api_model = Model(name, model, mask=mask)
            api_model.__apidoc__ = kwargs
            return self.add_model(name, api_model)
        return super(Namespace, self).model(name, model, **kwargs)

    def parameters(self, parameters, locations=None):
        """
        Endpoint parameters registration decorator.
        """
        def decorator(func):
            if locations is None and parameters.many:
                _locations = ('json', )
            else:
                _locations = locations
            if _locations is not None:
                parameters.context['in'] = _locations

            return self.doc(params=parameters)(
                self.response(code=http_exceptions.UnprocessableEntity.code)(
                    self.WEBARGS_PARSER.use_args(parameters, locations=_locations)(
                        func
                    )
                )
            )

        return decorator

    def response(self, model=None, code=200, description=None, **kwargs):
        """
        Endpoint response OpenAPI documentation decorator.

        It automatically documents HTTPError%(code)d responses with relevant
        schemas.

        Arguments:
            model (flask_marshmallow.Schema) - it can be a class or an instance
                of the class, which will be used for OpenAPI documentation
                purposes. It can be omitted if ``code`` argument is set to an
                error HTTP status code.
            code (int) - HTTP status code which is documented.
            description (str)

        Example:
        >>> @namespace.response(BaseTeamSchema(many=True))
        ... @namespace.response(code=403)
        ... def get_teams():
        ...     if not user.is_admin:
        ...         abort(403)
        ...     return Team.query.all()
        """
        if model is None and code != HTTPStatus.NO_CONTENT:
            if code not in http_exceptions.default_exceptions:
                raise ValueError("`model` parameter is required for code %d" % code)
            model = self.model(
                name='HTTPError%d' % code,
                model=DefaultHTTPErrorSchema(http_code=code)
            )
        if description is None:
            if code in http_exceptions.default_exceptions:
                description = http_exceptions.default_exceptions[code].description
            elif code == HTTPStatus.NO_CONTENT:
                description = 'Request fulfilled, nothing follows'

        def dump_response_with_model_decorator(func):
            def dump_wrapper(*args, **kwargs):
                response = func(*args, **kwargs)
                if isinstance(response, flask.Response):
                    return response
                elif response is None:
                    if code == HTTPStatus.NO_CONTENT:
                        return flask.Response(status=HTTPStatus.NO_CONTENT, content_type='application/json')
                    raise ValueError("Reponse must not be empty with code 200")
                return model.dump(response).data
            return dump_wrapper

        def decorator(func_or_class):
            if code in http_exceptions.default_exceptions:
                # If the code is handled by raising an exception, it will
                # produce a response later, so we don't need to apply a dump
                # wrapper.
                decorated_func_or_class = func_or_class
            elif isinstance(func_or_class, type):
                # Make a copy of `method_decorators` as otherwise we will
                # modify the behaviour of all flask-restful.Resource-based
                # classes
                func_or_class.method_decorators = (
                    [dump_response_with_model_decorator] + func_or_class.method_decorators
                )
                decorated_func_or_class = func_or_class
            else:
                decorated_func_or_class = wraps(func_or_class)(
                    dump_response_with_model_decorator(func_or_class)
                )

            if code == HTTPStatus.NO_CONTENT:
                api_model = None
            else:
                if isinstance(model, Model):
                    api_model = model
                else:
                    api_model = self.model(model=model)
                if getattr(model, 'many', False):
                    api_model = [api_model]

            return self.doc(responses={code: (description, api_model)})(decorated_func_or_class)

        return decorator

    def route(self, *args, **kwargs):
        base_wrapper = super(Namespace, self).route(*args, **kwargs)
        def wrapper(cls):
            if 'OPTIONS' in cls.methods:
                cls.options = self.response(code=204)(cls.options)
            return base_wrapper(cls)
        return wrapper
