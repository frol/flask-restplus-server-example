from functools import wraps

import flask
import flask_marshmallow
from flask_restplus import Namespace as OriginalNamespace
from flask_restplus.utils import merge
from flask_restplus._http import HTTPStatus
from webargs.flaskparser import parser as webargs_parser
from werkzeug import cached_property, exceptions as http_exceptions

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
                # Handle Resource classes decoration
                # pylint: disable=protected-access
                func_or_class._apply_decorator_to_methods(decorator)
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
        if isinstance(model, (flask_marshmallow.Schema, flask_marshmallow.base_fields.FieldABC)):
            if not name:
                name = model.__class__.__name__
            api_model = Model(name, model, mask=mask)
            api_model.__apidoc__ = kwargs
            return self.add_model(name, api_model)
        return super(Namespace, self).model(name=name, model=model, **kwargs)

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
                self.response(code=HTTPStatus.UNPROCESSABLE_ENTITY)(
                    self.WEBARGS_PARSER.use_args(parameters, locations=_locations)(
                        func
                    )
                )
            )

        return decorator

    def response(self, model=None, code=HTTPStatus.OK, description=None, **kwargs):
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
        ... @namespace.response(code=HTTPStatus.FORBIDDEN)
        ... def get_teams():
        ...     if not user.is_admin:
        ...         abort(HTTPStatus.FORBIDDEN)
        ...     return Team.query.all()
        """
        code = HTTPStatus(code)
        if code is HTTPStatus.NO_CONTENT:
            assert model is None
        if model is None and code not in {HTTPStatus.ACCEPTED, HTTPStatus.NO_CONTENT}:
            if code.value not in http_exceptions.default_exceptions:
                raise ValueError("`model` parameter is required for code %d" % code)
            model = self.model(
                name='HTTPError%d' % code,
                model=DefaultHTTPErrorSchema(http_code=code)
            )
        if description is None:
            description = code.description

        def response_serializer_decorator(func):
            """
            This decorator handles responses to serialize the returned value
            with a given model.
            """
            def dump_wrapper(*args, **kwargs):
                # pylint: disable=missing-docstring
                response = func(*args, **kwargs)

                if response is None:
                    if model is not None:
                        raise ValueError("Response cannot not be None with HTTP status %d" % code)
                    return flask.Response(status=code)
                elif isinstance(response, flask.Response) or model is None:
                    return response
                elif isinstance(response, tuple):
                    response, _code = response
                else:
                    _code = code

                if HTTPStatus(_code) is code:
                    response = model.dump(response).data
                return response, _code

            return dump_wrapper

        def decorator(func_or_class):
            if code.value in http_exceptions.default_exceptions:
                # If the code is handled by raising an exception, it will
                # produce a response later, so we don't need to apply a useless
                # wrapper.
                decorated_func_or_class = func_or_class
            elif isinstance(func_or_class, type):
                # Handle Resource classes decoration
                # pylint: disable=protected-access
                func_or_class._apply_decorator_to_methods(response_serializer_decorator)
                decorated_func_or_class = func_or_class
            else:
                decorated_func_or_class = wraps(func_or_class)(
                    response_serializer_decorator(func_or_class)
                )

            if model is None:
                api_model = None
            else:
                if isinstance(model, Model):
                    api_model = model
                else:
                    api_model = self.model(model=model)
                if getattr(model, 'many', False):
                    api_model = [api_model]

            doc_decorator = self.doc(
                    responses={
                            code.value: (description, api_model)
                        }
                )
            return doc_decorator(decorated_func_or_class)

        return decorator

    def preflight_options_handler(self, func):

        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if 'Access-Control-Request-Method' in flask.request.headers:
                response = flask.Response(status=HTTPStatus.OK)
                response.headers['Access-Control-Allow-Methods'] = ", ".join(self.methods)
                return response
            return func(self, *args, **kwargs)

        return wrapper

    def route(self, *args, **kwargs):
        base_wrapper = super(Namespace, self).route(*args, **kwargs)

        def wrapper(cls):
            if 'OPTIONS' in cls.methods:
                cls.options = self.preflight_options_handler(
                    self.response(code=HTTPStatus.NO_CONTENT)(cls.options)
                )
            return base_wrapper(cls)

        return wrapper
