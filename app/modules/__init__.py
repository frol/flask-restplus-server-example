# encoding: utf-8
"""
Init all modules here
"""


def init_app(app, **kwargs):
    from importlib import import_module

    for module_name in app.config['ENABLED_MODULES']:
        import_module('.%s' % module_name, package=__name__).init_app(app, **kwargs)
