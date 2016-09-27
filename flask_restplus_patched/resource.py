# -*- coding: utf-8 -*-
# pylint: disable=protected-access
import flask
from flask_restplus import Resource as OriginalResource
from werkzeug.exceptions import HTTPException


class Resource(OriginalResource):
    """
    Extended Flast-RESTPlus Resource to add options method
    """

    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)

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
        Implementation  of universal OPTIONS method for resources

        This method checks every permissions provided as decorators
        for other methods to provide information about what methods
        current_user can use
        """
        funcs = [getattr(self, m.lower()) for m in self.methods]
        methods = self.methods[:]
        for method in funcs:
            if hasattr(method, '_access_restriction_decorators'):
                if not hasattr(method, '_cached_ok_func'):
                    ok_func = lambda *args, **kwargs: True
                    for decorator in method._access_restriction_decorators:
                        ok_func = decorator(ok_func)
                    method.__dict__['_cached_ok_func'] = ok_func
                else:
                    ok_func = method._cached_ok_func
                try:
                    ok_func(*args, **kwargs)
                except HTTPException:
                    del methods[methods.index(method.__name__.upper())]
                else:
                    pass  # !!! all checks are passed, so we should be fine here!
        return flask.Response(status=204, headers={'Allow': ", ".join(methods)})
