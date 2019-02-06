# -*- coding: utf-8 -*-
# pylint: disable=protected-access
import flask
from flask_restplus import Resource as OriginalResource
from flask_restplus._http import HTTPStatus
from werkzeug.exceptions import HTTPException


class Resource(OriginalResource):
    """
    Extended Flast-RESTPlus Resource to add options method
    """

    @classmethod
    def _apply_decorator_to_methods(cls, decorator):
        """
        This helper can apply a given decorator to all methods on the current
        Resource.

        NOTE: In contrast to ``Resource.method_decorators``, which has a
        similar use-case, this method applies decorators directly and override
        methods in-place, while the decorators listed in
        ``Resource.method_decorators`` are applied on every request which is
        quite a waste of resources.
        """
        for method in cls.methods:
            method_name = method.lower()
            decorated_method_func = decorator(getattr(cls, method_name))
            setattr(cls, method_name, decorated_method_func)

    def options(self, *args, **kwargs):
        """
        Check which methods are allowed.

        Use this method if you need to know what operations are allowed to be
        performed on this endpoint, e.g. to decide wether to display a button
        in your UI.

        The list of allowed methods is provided in `Allow` response header.
        """
        # This is a generic implementation of OPTIONS method for resources.
        # This method checks every permissions provided as decorators for other
        # methods to provide information about what methods `current_user` can
        # use.
        method_funcs = [getattr(self, m.lower()) for m in self.methods]
        allowed_methods = []
        request_oauth_backup = getattr(flask.request, 'oauth', None)
        for method_func in method_funcs:
            if getattr(method_func, '_access_restriction_decorators', None):
                if not hasattr(method_func, '_cached_fake_method_func'):
                    fake_method_func = lambda *args, **kwargs: True
                    # `__name__` is used in `login_required` decorator, so it
                    # is required to fake this also
                    fake_method_func.__name__ = 'options'

                    # Decorate the fake method with the registered access
                    # restriction decorators
                    for decorator in method_func._access_restriction_decorators:
                        fake_method_func = decorator(fake_method_func)

                    # Cache the `fake_method_func` to avoid redoing this over
                    # and over again
                    method_func.__dict__['_cached_fake_method_func'] = fake_method_func
                else:
                    fake_method_func = method_func._cached_fake_method_func

                flask.request.oauth = None
                try:
                    fake_method_func(self, *args, **kwargs)
                except HTTPException:
                    # This method is not allowed, so skip it
                    continue

            allowed_methods.append(method_func.__name__.upper())
        flask.request.oauth = request_oauth_backup

        return flask.Response(
            status=HTTPStatus.NO_CONTENT,
            headers={'Allow': ", ".join(allowed_methods)}
        )
