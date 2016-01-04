# encoding: utf-8
# pylint: disable=too-few-public-methods,invalid-name,abstract-method,method-hidden
"""
RESTful API permissions
-----------------------
"""
import logging

from flask_login import current_user
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
        """
        Abort HTTP request by raising HTTP error exception with a specified
        HTTP code.
        """
        return abort(code=self.DENY_ABORT_HTTP_CODE, message=self.DENY_ABORT_MESSAGE)


class Rule(BaseRule):
    """
    Experimental base Rule class that helps to automatically handle inherited
    rules.
    """

    def base(self):
        # XXX: it handles only the first appropriate Rule base class
        # TODO: PR this case to permission project
        for base_class in self.__class__.__bases__:
            if issubclass(base_class, Rule):
                if base_class in {Rule, BaseRule}:
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


class PasswordRequiredRule(DenyAbortMixin, Rule):
    """
    Ensure that the current user has provided a correct password.
    """

    def __init__(self, password, **kwargs):
        super(PasswordRequiredRule, self).__init__(**kwargs)
        self._password = password

    def check(self):
        return current_user.password == self._password


class AdminRoleRule(ActivatedUserRoleRule):
    """
    Ensure that the current_user has an Admin role.
    """

    def check(self):
        return current_user.is_admin


class SupervisorRoleRule(ActivatedUserRoleRule):
    """
    Ensure that the current_user has a Supervisor access to the given object.
    """

    def __init__(self, obj, **kwargs):
        super(SupervisorRoleRule, self).__init__(**kwargs)
        self._obj = obj

    def check(self):
        if not hasattr(self._obj, 'check_supervisor'):
            return False
        return self._obj.check_supervisor(current_user) is True


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
        return self._obj.check_owner(current_user) is True


class AllowAllRule(Rule):
    """
    Helper rule that always grants access.
    """

    def check(self):
        return True


class PartialPermissionDeniedRule(Rule):
    """
    Helper rule that must fail on every check since it should never be checked.
    """

    def check(self):
        raise RuntimeError("Partial permissions are not intended to be checked")


class PasswordRequiredPermissionMixin(object):
    """
    Helper rule mixin that ensure that user password is correct if
    `password_required` is set to True.
    """

    def __init__(self, password_required=False, password=None, **kwargs):
        # pylint: disable=unused-argument
        # NOTE: kwargs is required since it is a mixin
        """
        Args:
            password_required (bool) - in some cases you may need to ask
                users for a password to allow certain actions, enforce this
                requirement by setting this :bool:`True`.
            password (str) - pass a user-specified password here.
        """
        self._password_required = password_required
        self._password = password
        super(PasswordRequiredPermissionMixin, self).__init__()

    def rule(self):
        _rule = super(PasswordRequiredPermissionMixin, self).rule()
        if self._password_required:
            _rule &= PasswordRequiredRule(self._password)
        return _rule


class WriteAccessPermission(Permission):
    """
    Require a non-readonly user to perform an action.
    """

    def rule(self):
        return WriteAccessRule()


class RolePermission(Permission):
    """
    This class aims to help distinguish all role-type permissions.
    """

    def __init__(self, partial=False, **kwargs):
        """
        Args:
            partial (bool) - it is mostly useful for documentation purposes.
        """
        self._partial = partial
        super(RolePermission, self).__init__(**kwargs)

    def rule(self):
        if self._partial:
            return PartialPermissionDeniedRule()
        return AllowAllRule()


class ActivatedUserRolePermission(RolePermission):
    """
    At least Activated user is required.
    """

    def rule(self):
        return ActivatedUserRoleRule()


class AdminRolePermission(PasswordRequiredPermissionMixin, RolePermission):
    """
    Admin role is required.
    """

    def rule(self):
        return AdminRoleRule() & super(AdminRolePermission, self).rule()


class SupervisorRolePermission(PasswordRequiredPermissionMixin, RolePermission):
    """
    Supervisor/Admin may execute this action.
    """

    def __init__(self, obj=None, **kwargs):
        """
        Args:
            obj (object) - any object can be passed here, which will be asked
                via ``check_supervisor(current_user)`` method whether a current
                user has enough permissions to perform an action on the given
                object.
        """
        self._obj = obj
        super(SupervisorRolePermission, self).__init__(**kwargs)

    def rule(self):
        return (
            (SupervisorRoleRule(obj=self._obj) | AdminRoleRule())
            & super(SupervisorRolePermission, self).rule()
        )


class OwnerRolePermission(PasswordRequiredPermissionMixin, RolePermission):
    """
    Owner/Supervisor/Admin may execute this action.
    """

    def __init__(self, obj=None, **kwargs):
        """
        Args:
            obj (object) - any object can be passed here, which will be asked
                via ``check_owner(current_user)`` method whether a current user
                has enough permissions to perform an action on the given
                object.
        """
        self._obj = obj
        super(OwnerRolePermission, self).__init__(**kwargs)

    def rule(self):
        return (
            (OwnerRoleRule(obj=self._obj) | SupervisorRoleRule(obj=self._obj) | AdminRoleRule())
            & super(OwnerRolePermission, self).rule()
        )
