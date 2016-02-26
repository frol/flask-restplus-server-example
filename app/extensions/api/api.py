# encoding: utf-8
"""
Extended Api implementation with an application-specific helpers
----------------------------------------------------------------
"""
from flask_restplus_patched import Api as BaseApi

from .namespace import Namespace


class Api(BaseApi):
    """
    Having app-specific handlers here.
    """

    def namespace(self, *args, **kwargs):
        # The only purpose of this method is to pass custom Namespace class
        _namespace = Namespace(*args, **kwargs)
        self.namespaces.append(_namespace)
        return _namespace

    def add_oauth_scope(self, scope_name, scope_description):
        for authorization_settings in self.authorizations.values():
            if authorization_settings['type'].startswith('oauth'):
                assert scope_name not in authorization_settings['scopes'], \
                    "OAuth scope %s already exists" % scope_name
                authorization_settings['scopes'][scope_name] = scope_description
