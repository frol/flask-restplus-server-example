# encoding: utf-8
# pylint: disable=too-many-arguments
"""
Application execution related tasks for Invoke.
"""

import os

try:
    from invoke import ctask as task
except ImportError:  # Invoke 0.13 renamed ctask to task
    from invoke import task


@task(default=True)
def run(
        context,
        host='127.0.0.1',
        port=5000,
        flask_config=None,
        install_dependencies=True,
        upgrade_db=True
    ):
    """
    Run Example RESTful API Server.
    """
    if flask_config is not None:
        os.environ['FLASK_CONFIG'] = flask_config

    if install_dependencies:
        context.invoke_execute(context, 'app.dependencies.install')

    from app import create_app
    app = create_app()

    if upgrade_db:
        context.invoke_execute(context, 'app.db.upgrade', app=app)
        if app.debug:
            context.invoke_execute(
                context,
                'app.db.init_development_data',
                app=app,
                upgrade_db=False,
                skip_on_failure=True
            )

    app.run(host=host, port=port)
