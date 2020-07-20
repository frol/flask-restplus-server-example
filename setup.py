#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, division
import subprocess
import os

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))


def git_version():
    """
    Return the sha1 of local git HEAD as a string.
    """

    def _minimal_ext_cmd(cmd):
        # construct minimal environment
        env = {}
        for k in ['SYSTEMROOT', 'PATH', 'PYTHONPATH']:
            v = os.environ.get(k)
            if v is not None:
                env[k] = v
        # LANGUAGE is used on win32
        env['LANGUAGE'] = 'C'
        env['LANG'] = 'C'
        env['LC_ALL'] = 'C'
        out = subprocess.Popen(cmd, stdout=subprocess.PIPE, env=env).communicate()[0]
        return out

    try:
        out = _minimal_ext_cmd(['git', 'rev-parse', 'HEAD'])
        git_revision = out.strip().decode('ascii')
    except OSError:
        git_revision = 'unknown-git'
    return git_revision


CLASSIFIERS = """
Development Status :: 3 - Alpha
Intended Audience :: Developers
Intended Audience :: System Administrators
License :: OSI Approved :: GNU General Public License v3 (GPLv3)
Natural Language :: English
Operating System :: POSIX
Operating System :: Unix
Operating System :: MacOS
Programming Language :: Python
Programming Language :: Python :: 3.7
Topic :: Internet :: WWW/HTTP :: Dynamic Content
"""
NAME = 'Houston'
MAINTAINER = 'Wild Me, non-profit'
MAINTAINER_EMAIL = 'dev@wildme.org'
DESCRIPTION = 'The backend server for the new Wildbook frontend and API.'
LONG_DESCRIPTION = DESCRIPTION
KEYWORDS = ['wild me', 'hoston', 'wildbook']
URL = 'https://hoston.dyn.wildme.io/'
DOWNLOAD_URL = ''
LICENSE = 'Apache'
AUTHOR = MAINTAINER
AUTHOR_EMAIL = MAINTAINER_EMAIL
PLATFORMS = ['Linux', 'Mac OS-X', 'Unix']
MAJOR = 0
MINOR = 1
MICRO = 0
REVISION = git_version()
SUFFIX = REVISION[:8]
VERSION = '%d.%d.%d.%s' % (MAJOR, MINOR, MICRO, SUFFIX)
PACKAGES = ['.']


def write_version_py(filename=os.path.join(PROJECT_ROOT, 'app', 'version.py')):
    cnt = """
# THIS FILE IS GENERATED FROM SETUP.PY
version = '%(version)s'
git_revision = '%(git_revision)s'
full_version = '%%(version)s.%%(git_revision)s' %% {
    'version': version,
    'git_revision': git_revision,
}
"""
    FULL_VERSION = VERSION
    if os.path.isdir('.git'):
        GIT_REVISION = REVISION
    elif os.path.exists(filename):
        GIT_REVISION = 'RELEASE'
    else:
        GIT_REVISION = 'unknown'

    FULL_VERSION += '.' + GIT_REVISION
    text = cnt % {'version': VERSION, 'git_revision': GIT_REVISION}
    try:
        with open(filename, 'w') as a:
            a.write(text)
    except Exception as e:
        print(e)


def do_setup():
    paths = [
        'tasks/requirements.txt',
        'app/requirements.txt',
        'tests/requirements.txt',
    ]
    requirements = []
    for path in paths:
        with open(os.path.abspath(os.path.join('.', path))) as req_file:
            requirements_ = req_file.read().splitlines()
            requirements += requirements_

    write_version_py()
    setup(
        name=NAME,
        version=VERSION,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        classifiers=CLASSIFIERS,
        author=AUTHOR,
        author_email=AUTHOR_EMAIL,
        url=URL,
        license=LICENSE,
        platforms=PLATFORMS,
        packages=PACKAGES,
        install_requires=requirements,
        keywords=CLASSIFIERS.replace('\n', ' ').strip(),
    )


if __name__ == '__main__':
    do_setup()
