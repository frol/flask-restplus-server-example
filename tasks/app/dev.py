# encoding: utf-8
# pylint: disable=missing-docstring
"""
This file contains initialization data for development usage only.

You can execute this code via ``invoke app.db.init_development_data``
"""
from app.extensions import db  # NOQA
from app.modules.users.models import User  # NOQA


from ._utils import app_context_task


@app_context_task
def embed(context):
    import utool as ut
    ut.embed()
