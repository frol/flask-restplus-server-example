# encoding: utf-8
"""
Application environment related tasks for Invoke.
"""

try:
    from invoke import ctask as task
except ImportError:  # Invoke 0.13 renamed ctask to task
    from invoke import task


@task
def enter(context, install_dependencies=True, upgrade_db=True):
    """
    Enter into IPython notebook shell with an initialized app.
    """
    if install_dependencies:
        context.invoke_execute(context, 'app.dependencies.install')
    if upgrade_db:
        context.invoke_execute(context, 'app.db.upgrade')
        context.invoke_execute(
            context,
            'app.db.init_development_data',
            upgrade_db=False,
            skip_on_failure=True
        )


    import pprint

    from werkzeug import script
    import flask

    import app
    flask_app = app.create_app()

    def shell_context():
        context = dict(pprint=pprint.pprint)
        context.update(vars(flask))
        context.update(vars(app))
        return context

    with flask_app.app_context():
        script.make_shell(shell_context, use_ipython=True)()
