# encoding: utf-8
# pylint: disable=missing-docstring
"""
This file contains initialization data for development usage only.

You can execute this code via ``invoke app.consistency``
"""
import logging
import tqdm

from app.extensions import db
from app.modules.users.models import User

from ._utils import app_context_task

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app_context_task
def user_staff_permissions(context):
    users = User.query.all()

    updated = 0
    with db.session.begin():
        for user in tqdm.tqdm(users):
            if user.is_admin:
                print(user)
            else:
                if user.is_staff:
                    user.is_staff = False
                    db.session.merge(user)
                    updated += 1

    print('Updated %d users' % (updated, ))


@app_context_task
def all(context, skip_on_failure=False):
    log.info("Initializing consistency checks...")

    try:
        user_staff_permissions(context)
    except AssertionError as exception:
        if not skip_on_failure:
            log.error("%s", exception)
        else:
            log.debug(
                "The following error was ignored due to the `skip_on_failure` flag: %s",
                exception
            )
            log.info("Running consistency checks is skipped.")
    else:
        log.info("Consistency checks successfully applied.")
