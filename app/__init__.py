# encoding: utf-8
"""
Example RESTful API Server.
"""
import logging
import os

from flask import Flask


CONFIG_NAME_MAPPER = {
    'development': 'config.DevelopmentConfig',
    'testing': 'config.TestingConfig',
    'production': 'config.ProductionConfig',
    'local': 'local_config.LocalConfig',
}

def create_app(flask_config='production', **kwargs):
    """
    Entry point to the Flask RESTful Server application.
    """
    app = Flask(__name__, **kwargs)

    config_name = os.getenv('FLASK_CONFIG', flask_config)
    app.config.from_object(CONFIG_NAME_MAPPER[config_name])

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
