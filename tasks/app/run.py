# encoding: utf-8
# pylint: disable=too-many-arguments
"""
Application execution related tasks for Invoke.
"""

try:
    from invoke import ctask as task
except ImportError:  # Invoke 0.13 renamed ctask to task
    from invoke import task


@task(default=True)
def run(
        context,
        host='127.0.0.1',
        port=5000,
        development=True,
        install_dependencies=True,
        upgrade_db=True
    ):
    """
    Run Example RESTful API Server.
    """
    if install_dependencies:
        context.invoke_execute(context, 'app.dependencies.install')
    if upgrade_db:
        context.invoke_execute(context, 'app.db.upgrade')
        if development:
            context.invoke_execute(
                context,
                'app.db.init_development_data',
                upgrade_db=False,
                skip_on_failure=True
            )

    from app import create_app
    create_app(
        flask_config='development' if development else 'production'
    ).run(
        host=host,
        port=port
    )
