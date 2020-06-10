# -*- coding: utf-8 -*-
"""
OAuth2 provider models.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""
import logging
import enum

from flask import current_app, request
from sqlalchemy_utils import Timestamp
from app.extensions.email import Email  # , _format_datetime

from app.extensions import db

import datetime
import pytz
import pprint

import uuid


log = logging.getLogger(__name__)
pp = pprint.PrettyPrinter(indent=2)


PST = pytz.timezone('US/Pacific')


class EmailTypes(str, enum.Enum):
    invite = 'invite'
    confirm = 'confirm'
    receipt = 'receipt'


class EmailRecord(db.Model, Timestamp):
    """
    OAuth2 Access Tokens storage model.
    """

    __tablename__ = 'email'

    guid = db.Column(
        db.GUID, default=uuid.uuid4, primary_key=True
    )  # pylint: disable=invalid-name

    recipient = db.Column(db.String, index=True, nullable=False)
    email_type = db.Column(db.Enum(EmailTypes), index=True, nullable=False)

    def __repr__(self):
        return (
            '<{class_name}('
            'guid={self.guid}, '
            'type={self.email_type}, '
            ')>'.format(class_name=self.__class__.__name__, self=self)
        )


class RecordedEmail(Email):
    def __init__(self, *args, **kwargs):
        self.email_type = None
        super(RecordedEmail, self).__init__(*args, **kwargs)

    def go(self, *args, **kwargs):
        response = super(RecordedEmail, self).go(*args, **kwargs)
        try:
            if self.email_type is not None:
                status = response.get('status', None)
                if status in ['sent']:
                    for recipient in self.recipients:
                        record = EmailRecord(
                            recipient=recipient, email_type=self.email_type
                        )
                        with db.session.begin():
                            db.session.add(record)
        except Exception:
            pass
        return response


class ErrorEmail(RecordedEmail):
    def __init__(self, subject, data={}, **kwargs):

        assert 'recipients' not in kwargs
        recipients = current_app.config.get('MAIL_ERROR_RECIPIENTS', None)
        assert recipients is not None
        kwargs['recipients'] = recipients

        super(ErrorEmail, self).__init__(subject, **kwargs)

        timestamp = datetime.datetime.now(tz=PST)
        global_data = {
            'timestamp': timestamp,
            'request': request,
        }
        global_data.update(data)
        global_data_ = pp.pformat(global_data)

        tempate_kwargs = {
            'error_data': global_data_,
        }
        self.template('email.error.html', **tempate_kwargs)


class SystemErrorEmail(ErrorEmail):
    def __init__(self, module, description, data={}, **kwargs):
        subject = 'System Error'

        local_data = {
            'module': module,
            'description': description,
        }
        local_data.update(data)

        super(SystemErrorEmail, self).__init__(subject, data=local_data, **kwargs)
