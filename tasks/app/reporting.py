# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring
"""
This file contains initialization data for development usage only.

You can execute this code via ``invoke app.reporting``
"""
import logging

# from app.extensions import db
from app.modules.payments.models import Payment

from ._utils import app_context_task

log = logging.getLogger(__name__)  # pylint: disable=invalid-name


@app_context_task
def report_purchases(context):
    payments = Payment.query.all()

    programs, addons = {}, {}
    charged, complement = 0, 0
    for payment in payments:
        cart = payment.cart
        charged += payment.charged
        comp = payment.total - payment.charged
        complement += comp
        if comp == 0:
            for item in cart['items']:
                print(item)
                program_id = item.get('program_id', None)
                addon_id = item.get('program_addon_id', None)
                quantity = item.get('quantity', 0)
                if program_id is not None:
                    if program_id not in programs:
                        programs[program_id] = 0
                    programs[program_id] += quantity
                if addon_id is not None:
                    if addon_id not in addons:
                        addons[addon_id] = 0
                    addons[addon_id] += quantity

    print(charged / 100.0)
    print(complement / 100.0)
    print(addons)


@app_context_task
def all(context, skip_on_failure=False):
    log.info('Initializing reporting checks...')

    try:
        report_purchases(context)
    except AssertionError as exception:
        if not skip_on_failure:
            log.error('%s', exception)
        else:
            log.debug(
                'The following error was ignored due to the `skip_on_failure` flag: %s',
                exception,
            )
            log.info('Running reporting is skipped.')
    else:
        log.info('Reporting successfully applied.')
