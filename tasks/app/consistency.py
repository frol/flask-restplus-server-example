# -*- coding: utf-8 -*-
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

            update = False

            if not user.in_alpha:
                user.in_alpha = True
                update = True
            if not user.in_beta:
                user.in_beta = True
                update = True

            email = user.email.strip()
            whitlist = [
                'bluemellophone@gmail.com',
                'sito.org+giraffeadmin@gmail.com',
                'sito.org+gstest@gmail.com',
            ]
            is_wildme = email.endswith('@wildme.org') or email in whitlist
            if is_wildme:
                if not user.is_staff:
                    user.is_staff = True
                    update = True
                if not user.is_admin:
                    user.is_admin = True
                    update = True
                print(user)
            else:
                if user.is_staff:
                    user.is_staff = False
                    update = True
                if user.is_admin:
                    user.is_admin = False
                    update = True

            if update:
                db.session.merge(user)
                updated += 1

    print('Updated %d users' % (updated,))


@app_context_task
def all(context, skip_on_failure=False):
    log.info('Initializing consistency checks...')

    try:
        user_staff_permissions(context)
    except AssertionError as exception:
        if not skip_on_failure:
            log.error('%s', exception)
        else:
            log.debug(
                'The following error was ignored due to the `skip_on_failure` flag: %s',
                exception,
            )
            log.info('Running consistency checks is skipped.')
    else:
        log.info('Consistency checks successfully applied.')
