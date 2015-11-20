from flask_restplus_patched import DefaultHTTPErrorSchema
from werkzeug import exceptions as http_exceptions

from app.extensions import oauth2
from app.modules.users import permissions


def login_required(api, scopes):
    def decorator(func):
        if getattr(func, '__role_permission_applied__', False):
            protected_func = func
        else:
            protected_func = permissions.ActivatedUserRolePermission(api=api)(func)
        oauth_protected_func = oauth2.require_oauth(*scopes)(protected_func)
        return api.doc(
            security=[
                {'oauth2': scopes}
            ]
        )(
            DefaultHTTPErrorSchema(
                api=api,
                code=http_exceptions.Unauthorized.code,
                description="Authentication with %s scope(s) is required" % (', '.join(scopes)),
            )(oauth_protected_func)
        )
    return decorator
