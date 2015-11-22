import logging

from flask.ext.login import current_user
from permission import Rule as BaseRule, Permission

from app.extensions.api import abort, http_exceptions


log = logging.getLogger(__name__)


class DenyAbortMixin(object):
    """
    A helper permissions mixin raising an HTTP Error (specified in
    ``DENY_ABORT_CODE``) on deny.

    NOTE: Apply this mixin before Rule class so it can override NotImplemented
    deny method.
    """

    DENY_ABORT_HTTP_CODE = http_exceptions.Forbidden.code
    DENY_ABORT_MESSAGE = None

    def deny(self):
        return abort(code=self.DENY_ABORT_HTTP_CODE, message=self.DENY_ABORT_MESSAGE)


class Rule(BaseRule):

    def base(self):
        # XXX: it handles only the first appropriate Rule base class
        # TODO: PR this case to permission project
        for base_class in self.__class__.__bases__:
            if issubclass(base_class, Rule):
                if base_class == Rule or base_class == BaseRule:
                    continue
                return base_class()


class WriteAccessRule(DenyAbortMixin, Rule):
    """
    Ensure that the current_user has has write access.
    """

    def check(self):
        return not current_user.is_readonly


class ActivatedUserRoleRule(DenyAbortMixin, Rule):
    """
    Ensure that the current_user is activated.
    """

    def check(self):
        # Do not override DENY_ABORT_HTTP_CODE because inherited classes will
        # better use HTTP 403/Forbidden code on denial.
        self.DENY_ABORT_HTTP_CODE = http_exceptions.Unauthorized.code
        # NOTE: `is_active` implies `is_authenticated`.
        return current_user.is_active


class AdminRoleRule(ActivatedUserRoleRule):
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


class OwnerRoleRule(ActivatedUserRoleRule):
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


class SupervisorRoleRule(ActivatedUserRoleRule):
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



class WriteAccessPermission(Permission):
    """
    Require a non-readonly user to perform an action.
    """

    def rule(self):
        return WriteAccessRule()


class RolePermission(Permission):
    """
    This class is aiming to help distinguish all role-type permissions.
    """


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
    
    def __init__(self, password_required=False, password=None, **kwargs):
        self._password_required = password_required
        self._password = password
        super(AdminRolePermission, self).__init__(**kwargs)

    def rule(self):
        return AdminRoleRule(
            password_required=self._password_required,
            password=self._password
        )


class SupervisorRolePermission(AdminRolePermission):
    """
    Supervisor/Admin may execute this action.
    """
    
    def __init__(self, obj=None, password_required=False, password=None, **kwargs):
        self._obj = obj
        super(SupervisorRolePermission, self).__init__(**kwargs)

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
