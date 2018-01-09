# encoding: utf-8
# pylint: disable=invalid-name,wrong-import-position
"""
The starting point of Invoke tasks for Example RESTful API Server project.
"""

import logging
import os
import platform
import sys
import sysconfig
from logging.handlers import RotatingFileHandler
from flask_log_request_id import RequestIDLogFilter
import datetime, time

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
#logging.getLogger('app').setLevel(logging.DEBUG)

try:
    import colorlog
except ImportError:
    pass
else:
    formatter = colorlog.ColoredFormatter(
        (
            '%(asctime)s '
            '[%(request_id)s]'
            '[%(log_color)s%(levelname)s%(reset)s] '
            '[%(cyan)s%(name)s%(reset)s] '
            '%(message_log_color)s%(message)s'
        ),
        reset=True,
        log_colors={
            'DEBUG': 'bold_cyan',
            'INFO': 'bold_green',
            'WARNING': 'bold_yellow',
            'ERROR': 'bold_red',
            'CRITICAL': 'bold_red,bg_white',
        },
        secondary_log_colors={
            'message': {
                'DEBUG': 'white',
                'INFO': 'bold_white',
                'WARNING': 'bold_yellow',
                'ERROR': 'bold_red',
                'CRITICAL': 'bold_red',
            },
        },
        style='%'
    )

    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            break
    else:
        handler = logging.StreamHandler()
        logger.addHandler(handler)
    formatter.converter = time.gmtime
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDLogFilter())

    # Log to file handler
    handler = RotatingFileHandler(datetime.datetime.utcnow()
                                  .strftime("/tmp/flask-stack2_%Y_%m_%d.log"),
                                  maxBytes=100*1024*1024, backupCount=999)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDLogFilter())
    logger.addHandler(handler)

from invoke import Collection
from invoke.executor import Executor

from . import app

# NOTE: `namespace` or `ns` name is required!
namespace = Collection(
    app,
)

def invoke_execute(context, command_name, **kwargs):
    """
    Helper function to make invoke-tasks execution easier.
    """
    results = Executor(namespace, config=context.config).execute((command_name, kwargs))
    target_task = context.root_namespace[command_name]
    return results[target_task]

namespace.configure({
    'run': {
        'shell': '/bin/sh' if platform.system() != 'Windows' else os.environ.get('COMSPEC'),
    },
    'root_namespace': namespace,
    'invoke_execute': invoke_execute,
})
