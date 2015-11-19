# encoding: utf-8
"""
Application related tasks for Invoke.
"""

from invoke import Collection

from . import dependencies, env, db, run

namespace = Collection(
    dependencies,
    env,
    db,
    run,
)
