# encoding: utf-8
"""
Extended Api implementation with an application-specific helpers
----------------------------------------------------------------
"""
#from flask_restplus import Api as BaseApi
from flask_restplus_patched import Api as BaseApi

from . import http_exceptions


class Api(BaseApi):
    """
    Having app-specific handlers here.
    """

    def login_required(self, scopes):
        """
        A decorator which restricts access for authorized users only.
        """
        def decorator(func):
            """
            A helper wrapper.
            """
            # Avoid circilar dependency
            from app.extensions import oauth2
            from app.modules.users import permissions

            if getattr(func, '_role_permission_applied', False):
                protected_func = func
            else:
                protected_func = self.permission_required(
                    permissions.ActivatedUserRolePermission()
                )(func)
            oauth_protected_func = oauth2.require_oauth(*scopes)(protected_func)
            return self.doc(
                security=[
                    {'oauth2': scopes}
                ]
            )(
                self.response(
                    code=http_exceptions.Unauthorized.code,
                    description="Authentication with %s scope(s) is required" % (', '.join(scopes)),
                )(oauth_protected_func)
            )

        return decorator

    def permission_required(self, permission):
        """
        A decorator which restricts access for users with a specific permissions only.
        """
        def decorator(func):
            """
            A helper wrapper.
            """
            # Avoid circilar dependency
            from app.modules.users import permissions

            if getattr(permission, '_partial', False):
                # We don't apply partial permissions, we only use them for
                # documentation purposes.
                protected_func = func
            else:
                protected_func = permission(func)

            if isinstance(permission, permissions.RolePermission):
                protected_func._role_permission_applied = True # pylint: disable=protected-access

            permission_description = permission.__doc__.strip()
            return self.doc(
                description="**PERMISSIONS: %s**\n\n" % permission_description
            )(
                self.response(
                    code=http_exceptions.Forbidden.code,
                    description=permission_description,
                )(protected_func)
            )

        return decorator
