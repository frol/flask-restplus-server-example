# -*- coding: utf-8 -*-
# pylint: disable=no-self-use
"""
OAuth2 provider setup.

It is based on the code from the example:
https://github.com/lepture/example-oauth2-server

More details are available here:
* http://flask-oauthlib.readthedocs.org/en/latest/oauth2.html
* http://lepture.com/en/2013/create-oauth-server
"""
import logging

from flask import current_app, request, session, render_template  # NOQA
from flask_login import current_user  # NOQA

from flask_mail import Mail, Message, email_dispatched  # NOQA
from premailer import Premailer
import cssutils
import htmlmin

from io import StringIO
import re

import datetime
import pytz


PST = pytz.timezone('US/Pacific')

NEWLINE_TEMP_CODE = '_^_NEWLINE_CHARACTER_^_'
WEBFONTS_PLACEHOLDER_CODE = '_^_WEBFONTS_PLACEHOLDER_^_'


cssutils_log = StringIO()
cssutils_handler = logging.StreamHandler(cssutils_log)


mail = Mail()

pmail_kwargs = {
    'cssutils_logging_handler': cssutils_handler,
    'cssutils_logging_level': logging.FATAL,
    'cache_css_parsing': True,
}
pmail = None

log = logging.getLogger(__name__)


def status(message, app):
    message.status = 'sent'


email_dispatched.connect(status)


def _format_datetime(dt, verbose=False):
    """
    REF: https://stackoverflow.com/a/5891598
    """

    def _suffix(d):
        return 'th' if 11 <= d <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(d % 10, 'th')

    if verbose:
        time_fmtstr = '%B {S}, %Y at %I:%M %p'
    else:
        time_fmtstr = '%B {S}, %Y'
    return dt.strftime(time_fmtstr).replace('{S}', str(dt.day) + _suffix(dt.day))


class Email(Message):
    # pylint: disable=abstract-method
    """
    A project-specific implementation of OAuth2RequestValidator, which connects
    our User and OAuth2* implementations together.
    """

    def __init__(self, *args, **kwargs):
        now = datetime.datetime.now(tz=PST)

        self.template_name = None
        self.template_kwargs = {
            'year': now.year,
        }
        self.status = None

        # Debugging, override all email destinations
        override_recipients = current_app.config.get('MAIL_OVERRIDE_RECIPIENTS', None)
        if override_recipients is not None:
            original_recipients = kwargs.get('recipients', None)
            log.warning('Original recipients: %r' % (original_recipients,))
            log.warning('Override recipients: %r' % (override_recipients,))
            kwargs['recipients'] = override_recipients

        super(Email, self).__init__(*args, **kwargs)

    def template(self, template, **kwargs):
        global pmail
        if pmail is None:
            base_url = current_app.config.get('MAIL_BASE_URL', None)
            if base_url is not None:
                pmail_kwargs['base_url'] = base_url
            pmail = Premailer(**pmail_kwargs)  # REF: https://pypi.org/project/premailer/
        log.info('Using premailer = %r' % (pmail))

        self.template_name = template
        self.template_kwargs.update(kwargs)

        if self.template_name is not None:
            # Render raw HTML template with Jinja2
            self.raw_html = render_template(self.template_name, **self.template_kwargs)

            # Run Premailer
            attempt = 0
            while attempt <= 3:
                attempt += 1
                try:
                    transformed_html = pmail.transform(self.raw_html)
                    break
                except (cssutils.prodparser.Missing):
                    pass

            # Strip out unused leftover CSS and minify before sending
            assert NEWLINE_TEMP_CODE not in transformed_html
            transformed_html_ = transformed_html.replace('\n', NEWLINE_TEMP_CODE)
            minified_css_html_ = re.sub(
                r'<style type="text/css">.*</style>', '', transformed_html_
            )
            minified_css_html = minified_css_html_.replace(NEWLINE_TEMP_CODE, '\n')
            minified_html = htmlmin.minify(
                minified_css_html,
                remove_comments=True,
                remove_empty_space=True,
                remove_all_empty_space=True,
            )

            # Add web fonts
            webfonts = [
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Assistant:200|Chango|Molle:400i&display=swap">',
                '<link rel="stylesheet" href="https://fonts.googleapis.com/icon?family=Material+Icons">',
                '<link rel="stylesheet" href="https://fonts.googleapis.com/css?family=Source+Code+Pro&display=swap">',
            ]
            webfonts_html = ''.join(webfonts)
            minified_html = minified_html.replace(
                '</head>', '%s</head>' % (WEBFONTS_PLACEHOLDER_CODE,)
            )
            final_html = minified_html.replace(WEBFONTS_PLACEHOLDER_CODE, webfonts_html)

            with open('email.latest.html', 'w') as temp:
                temp.write(final_html)

            self.html = final_html

        return self

    def attach(self, filepath, atatchment_name, attachment_type='image/png'):
        with current_app.open_resource(filepath) as asset:
            self.attach(atatchment_name, attachment_type, asset.read())

        return self

    def go(self, *args, **kwargs):
        mail.send(self)
        response = {
            'status': self.status,
        }
        return response
