# encoding: utf-8
# pylint: disable=too-many-arguments
"""
Application execution related tasks for Invoke.
"""

from invoke import ctask as task


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
    Run DDOTS RESTful API Server.
    """
    if install_dependencies:
        context.invoke_execute(context, 'app.dependencies.install')
    if upgrade_db:
        context.invoke_execute(context, 'app.db.upgrade')

    from app import create_app
    create_app(
        flask_config='development' if development else 'production'
    ).run(
        host=host,
        port=port
    )
