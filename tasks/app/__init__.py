# encoding: utf-8
"""
Application related tasks for Invoke.
"""

from invoke import Collection

from . import dependencies, env, db, run, users, swagger

from config import BaseConfig

namespace = Collection(
    dependencies,
    env,
    db,
    run,
    users,
    swagger,
)

namespace.configure({
    'app': {
        'static_root': BaseConfig.STATIC_ROOT,
    }
})
