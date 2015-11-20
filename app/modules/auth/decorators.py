from app.extensions.api import DefaultHTTPErrorSchema
from app.modules.users import permissions

from . import providers


def login_required(api, scopes):
    def decorator(func):
        if getattr(func, '__role_permission_applied__', False):
            protected_func = func
        else:
            protected_func = permissions.ActivatedUserRolePermission(api=api)(func)
        oauth_protected_func = providers.oauth2.require_oauth(*scopes)(protected_func)
        return api.doc(
            security=[
                {'oauth2': scopes}
            ]
        )(
            DefaultHTTPErrorSchema(
                api=api,
                code=401,
                description="Authentication with %s scope(s) is required" % (', '.join(scopes)),
            )(oauth_protected_func)
        )
    return decorator
