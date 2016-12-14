# encoding: utf-8
# pylint: disable=too-many-arguments
"""
Application execution related tasks for Invoke.
"""

try:
    from importlib import reload
except ImportError:
    pass  # Python 2 has built-in reload() function
import os
import platform
import warnings

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
        # After the installed dependencies the app.db.* tasks might need to be
        # reloaded to import all necessary dependencies.
        from . import db as db_tasks
        reload(db_tasks)

        context.invoke_execute(context, 'app.db.upgrade', app=app)
        if app.debug:
            context.invoke_execute(
                context,
                'app.db.init_development_data',
                app=app,
                upgrade_db=False,
                skip_on_failure=True
            )

    use_reloader = app.debug
    if platform.system() == 'Windows':
        warnings.warn(
                "Auto-reloader feature doesn't work on Windows. "
                "Follow the issue for more details: "
                "https://github.com/frol/flask-restplus-server-example/issues/16"
            )
        use_reloader = False
    app.run(host=host, port=port, use_reloader=use_reloader)
