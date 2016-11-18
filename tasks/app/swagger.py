"""
Swagger related invoke tasks
"""
import logging

try:
    from invoke import ctask as task
except ImportError:  # Invoke 0.13 renamed ctask to task
    from invoke import task


@task(default=True)
def export(context):
    """
    Export swagger.json content
    """
    # set logging level to ERROR to avoid [INFO] messages in result
    logging.getLogger().setLevel(logging.ERROR)

    from app import create_app
    app = create_app()
    swagger_content = app.test_client().get('/api/v1/swagger.json').data
    print(swagger_content.decode('utf-8'))
