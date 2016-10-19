# encoding: utf-8
"""
Application related tasks for Invoke.
"""

from invoke import Collection

from . import dependencies, env, db, run, users

from config import BaseConfig

namespace = Collection(
    dependencies,
    env,
    db,
    run,
    users,
)

namespace.configure({
    'app': {
        'static_root': BaseConfig.STATIC_ROOT,
    }
})
