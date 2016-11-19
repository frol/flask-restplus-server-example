# encoding: utf-8
"""
Invoke tasks utilities for apps.
"""
import functools

from invoke import Task as BaseTask


class Task(BaseTask):
    """
    A patched Invoke Task adding support for decorated functions.
    """
    def __init__(self, *args, **kwargs):
        super(Task, self).__init__(*args, **kwargs)
        # Make these tasks always contextualized (this is the only option in
        # Invoke >=0.13), so we just backport this default on Invoke 0.12.
        self.contextualized = True

    def argspec(self, body):
        """
        See details in https://github.com/pyinvoke/invoke/pull/399.
        """
        if hasattr(body, '__wrapped__'):
            return self.argspec(body.__wrapped__)
        return super(Task, self).argspec(body)


def app_context_task(*args, **kwargs):
    """
    A helper Invoke Task decorator with auto app context activation.

    Examples:

    >>> @app_context_task
    ... def my_task(context, some_arg, some_option='default'):
    ...     print("Done")

    >>> @app_context_task(
    ...     help={'some_arg': "This is something useful"}
    ... )
    ... def my_task(context, some_arg, some_option='default'):
    ...     print("Done")
    """
    if len(args) == 1:
        func = args[0]

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            """
            A wrapped which tries to get ``app`` from ``kwargs`` or creates a
            new ``app`` otherwise, and actives the application context, so the
            decorated function is run inside the application context.
            """
            app = kwargs.pop('app', None)
            if app is None:
                from app import create_app
                app = create_app()

            with app.app_context():
                return func(*args, **kwargs)

        # This is the default in Python 3, so we just make it backwards
        # compatible with Python 2
        if not hasattr(wrapper, '__wrapped__'):
            wrapper.__wrapped__ = func
        return Task(wrapper, **kwargs)

    return lambda func: app_context_task(func, **kwargs)
