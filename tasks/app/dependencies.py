# encoding: utf-8
"""
Application dependencies related tasks for Invoke.
"""

from invoke import ctask as task


@task
def install(context):
    """
    Install Python dependencies listed in requirements.txt.
    """
    context.run("pip install --upgrade -r requirements.txt")
