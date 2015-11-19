import logging

from flask.ext.login import current_user
from flask_restplus_patched import abort
from permission import Rule, Permission

from app import api
from app.auth.providers import AUTHENTICATION_REQUIRED_MESSAGE


PERMISSION_DENIED_MESSAGE = "You don't have the permission to access the requested resource."


log = logging.getLogger(__name__)


class Deny403Mixin(object):
    """
    A helper permissions mixin raising HTTP 403 Error on deny.

    NOTE: Apply this mixin before Rule class so it can override NotImplemented
    deny method.
    """

    def deny(self):
        return abort(code=403, message=PERMISSION_DENIED_MESSAGE)


class BaseAPIRule(Rule):
    """
    Base API permissions rule.
    """

    def __init__(self, api=None, **kwargs):
        self.init_api(api)
        super(BaseAPIRule, self).__init__(**kwargs)

    def init_api(self, api):
        self._api = api
        if hasattr(self, 'rules_list'):
            for rules in self.rules_list:
                for rule_check, rule_deny in rules:
                    if rule_check.__self__ != self:
                        rule_check.__self__.init_api(api=self._api)

    def base(self):
        # XXX: it handles only the first appropriate Rule base class
        for base_class in self.__class__.__bases__:
            if issubclass(base_class, BaseAPIRule):
                if base_class == BaseAPIRule:
                    continue
                return base_class(api=self._api)
            if issubclass(base_class, Rule):
                if base_class == Rule:
                    continue
                return base_class()


class WriteAccessRule(Deny403Mixin, BaseAPIRule):
    """
    Ensure that the current_user has has write access.
    """

    def check(self):
        return not current_user.is_readonly


class ActivatedUserRoleRule(BaseAPIRule):
    """
    Ensure that the current_user is activated.
    """

    def check(self):
        # NOTE: is_active implies is_authenticated
        return current_user.is_active

    def deny(self):
        return abort(code=401, message=AUTHENTICATION_REQUIRED_MESSAGE)


class AdminRoleRule(Deny403Mixin, ActivatedUserRoleRule):
    """
    Ensure that the current_user has an Admin role.
    """

    def __init__(self, password_required=False, password=None, *args, **kwargs):
        super(AdminRoleRule, self).__init__(*args, **kwargs)
        self._password_required = password_required
        self._password = password
 
    def check(self):
        if not current_user.is_admin:
            return False
        if self._password_required:
            if not self._password:
                return False
            return current_user.verify_password(self._password)
        return True


class OwnerRoleRule(Deny403Mixin, ActivatedUserRoleRule):
    """
    Ensure that the current_user has an Owner access to the given object.
    """
 
    def __init__(self, obj, **kwargs):
        super(OwnerRoleRule, self).__init__(**kwargs)
        self._obj = obj

    def check(self):
        if not hasattr(self._obj, 'check_owner'):
            return False
        return self._obj.check_owner(current_user)


class SupervisorRoleRule(Deny403Mixin, ActivatedUserRoleRule):
    """
    Ensure that the current_user has a Supervisor access to the given object.
    """

    def __init__(self, obj, password_required=False, password=None, *args, **kwargs):
        super(SupervisorRoleRule, self).__init__(**kwargs)
        self._obj = obj
        self._password_required = password_required
        self._password = password

    def check(self):
        if not hasattr(self._obj, 'check_supervisor'):
            return False
        if not self._obj.check_supervisor(current_user):
            return False
        if self._password_required:
            if not self._password:
                return False
            return current_user.verify_password(self._password)
        return True


class BaseAPIPermission(Permission):

    def __init__(self, api=None, **kwargs):
        """
        WARNING: When overload __init__ keep ``api`` argument the first
        argument no mater what.
        """
        super(BaseAPIPermission, self).__init__(**kwargs)
        self.init_api(api)

    def init_api(self, api):
        self._api = api

    def check(self):
        self.rule.init_api(self._api)
        return super(BaseAPIPermission, self).check()


class WriteAccessPermission(BaseAPIPermission):
    """
    Require a non-readonly user to perform an action.
    """

    def rule(self):
        return WriteAccessRule()


class RolePermission(BaseAPIPermission):
    """
    Helper class injecting Flask-RESTplus (swagger) documentation.
    """
    
    def __call__(self, *args, **kwargs):
        protected_func = super(RolePermission, self).__call__(*args, **kwargs)
        protected_func.__role_permission_applied__ = True
        if self._api:
            protected_func = self._api.doc(
                description="**PERMISSIONS: %s**\n\n" % self.__doc__
            )(protected_func)
        elif self._api is None:
            log.warning(
                "Role Permission %r is applied to %r but documentation won't "
                "be available in Swagger spec because you haven't passed "
                "`api` instance. Pass `False` as api instance to suppress "
                "this warning.", self, protected_func
            )
        return protected_func


class ActivatedUserRolePermission(RolePermission):
    """
    At least Activated user is required.
    """

    def rule(self):
        return ActivatedUserRoleRule()


class AdminRolePermission(RolePermission):
    """
    Admin role is required.
    """
    
    def __init__(self, api=None, password_required=False, password=None, **kwargs):
        self._password_required = password_required
        self._password = password
        super(AdminRolePermission, self).__init__(api=api, **kwargs)

    def rule(self):
        return AdminRoleRule(
            password_required=self._password_required,
            password=self._password
        )


class SupervisorRolePermission(AdminRolePermission):
    """
    Supervisor/Admin may execute this action.
    """
    
    def __init__(self, api=None, obj=None, password_required=False, password=None, **kwargs):
        self._obj = obj
        super(SupervisorRolePermission, self).__init__(api=api, **kwargs)

    def rule(self):
        return SupervisorRoleRule(
            obj=self._obj,
            password_required=self._password_required,
            password=self._password
        ) | super(SupervisorRolePermission, self).rule()


class OwnerRolePermission(SupervisorRolePermission):
    """
    Owner/Supervisor/Admin may execute this action.
    """

    def rule(self):
        return OwnerRoleRule(self._obj) | super(OwnerRolePermission, self).rule()
