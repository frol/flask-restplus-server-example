# -*- coding: utf-8 -*-
"""
Extended Api Namespace implementation with an application-specific helpers
--------------------------------------------------------------------------
"""
from contextlib import contextmanager
from functools import wraps
import logging

import flask_marshmallow
import sqlalchemy

from flask_restplus_patched.namespace import Namespace as BaseNamespace
from flask_restplus._http import HTTPStatus

from . import http_exceptions
from .webargs_parser import CustomWebargsParser


log = logging.getLogger(__name__)


class Namespace(BaseNamespace):
    """
    Having app-specific handlers here.
    """

    WEBARGS_PARSER = CustomWebargsParser()

    def resolve_object_by_model(self, model, object_arg_name, identity_arg_names=None):
        """
        A helper decorator to resolve DB record instance by id.

        Arguments:
            model (type) - a Flask-SQLAlchemy model class with
                ``query.get_or_404`` method
            object_arg_name (str) - argument name for a resolved object
            identity_arg_names (tuple) - a list of argument names holding an
                object identity, by default it will be auto-generated as
                ``%(object_arg_name)s_id``.

        Example:
        >>> @namespace.resolve_object_by_model(User, 'user')
        ... def get_user_by_id(user):
        ...     return user
        >>> get_user_by_id(user_id=3)
        <User(id=3, ...)>

        >>> @namespace.resolve_object_by_model(MyModel, 'my_model', ('user_id', 'model_name'))
        ... def get_object_by_two_primary_keys(my_model):
        ...     return my_model
        >>> get_object_by_two_primary_keys(user_id=3, model_name="test")
        <MyModel(user_id=3, name="test", ...)>
        """
        if identity_arg_names is None:
            identity_arg_names = ('%s_id' % object_arg_name,)
        elif not isinstance(identity_arg_names, (list, tuple)):
            identity_arg_names = (identity_arg_names,)
        return self.resolve_object(
            object_arg_name,
            resolver=lambda kwargs: model.query.get_or_404(
                [
                    kwargs.pop(identity_arg_name)
                    for identity_arg_name in identity_arg_names
                ]
            ),
        )

    def model(self, name=None, model=None, **kwargs):
        # pylint: disable=arguments-differ
        """
        A decorator which registers a model (aka schema / definition).

        This extended implementation auto-generates a name for
        ``Flask-Marshmallow.Schema``-based instances by using a class name
        with stripped off `Schema` prefix.
        """
        if isinstance(model, flask_marshmallow.Schema) and not name:
            name = model.__class__.__name__
            if name.endswith('Schema'):
                name = name[: -len('Schema')]
        return super(Namespace, self).model(name=name, model=model, **kwargs)

    def paginate(self, parameters=None, locations=None):
        """
        Endpoint parameters registration decorator special for pagination.
        If ``parameters`` is not provided default PaginationParameters will be
        used.

        Also, any custom Parameters can be used, but it needs to have ``limit`` and ``offset``
        fields.
        """
        if not parameters:
            # Use default parameters if None specified
            from app.extensions.api.parameters import PaginationParameters

            parameters = PaginationParameters()

        if not all(
            mandatory in parameters.declared_fields for mandatory in ('limit', 'offset')
        ):
            raise AttributeError(
                '`limit` and `offset` fields must be in Parameter passed to `paginate()`'
            )

        def decorator(func):
            @wraps(func)
            def wrapper(self_, parameters_args, *args, **kwargs):
                queryset = func(self_, parameters_args, *args, **kwargs)
                total_count = queryset.count()
                return (
                    queryset.offset(parameters_args['offset']).limit(
                        parameters_args['limit']
                    ),
                    HTTPStatus.OK,
                    {'X-Total-Count': total_count},
                )

            return self.parameters(parameters, locations)(wrapper)

        return decorator

    @contextmanager
    def commit_or_abort(
        self, session, default_error_message='The operation failed to complete'
    ):
        """
        Context manager to simplify a workflow in resources

        Args:
            session: db.session instance
            default_error_message: Custom error message

        Exampple:
        >>> with api.commit_or_abort(db.session):
        ...     family = Family(**args)
        ...     db.session.add(family)
        ...     return family
        """
        try:
            with session.begin():
                yield
        except ValueError as exception:
            log.info('Database transaction was rolled back due to: %r', exception)
            http_exceptions.abort(code=HTTPStatus.CONFLICT, message=str(exception))
        except sqlalchemy.exc.IntegrityError as exception:
            log.info('Database transaction was rolled back due to: %r', exception)
            http_exceptions.abort(code=HTTPStatus.CONFLICT, message=default_error_message)
