# encoding: utf-8
# pylint: disable=invalid-name
"""
Example RESTful API Server.
"""
import logging
import os

from flask import Flask


def create_app(debug=None, **kwargs):
    app = Flask(__name__, **kwargs)

    config = {
        'development': 'config.DevelopmentConfig',
        'testing': 'config.TestingConfig',
        'production': 'config.ProductionConfig',
        'local': 'local_config.LocalConfig',
    }
    config_name = os.getenv('FLASK_CONFIGURATION', 'production')
    app.config.from_object(config[config_name])
    if debug is not None:
        app.debug = debug

    if app.debug:
        logging.getLogger('flask_oauthlib').setLevel(logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)

        # We don't need default Flask's loggers when using invoke tasks as the
        # latter set up colorful loggers.
        for handler in app.logger.handlers:
            app.logger.removeHandler(handler)

    from . import extensions
    extensions.init_app(app)
    
    from . import modules
    modules.init_app(app)

    return app
