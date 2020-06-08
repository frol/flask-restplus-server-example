# -*- coding: utf-8 -*-
"""
Application related tasks for Invoke.
"""

from invoke import Collection

from . import consistency, dependencies, dev, env, db, run, users, swagger, boilerplates

from config import BaseConfig

import os

namespace = Collection(
    consistency, dependencies, dev, env, db, run, users, swagger, boilerplates,
)

namespace.configure({'app': {'static_root': BaseConfig.STATIC_ROOT,}})

# Ensure database folder

# Ensure database asset store
_db_path = getattr(BaseConfig, 'PROJECT_DATABASE_PATH', None)
_asset_path = getattr(BaseConfig, 'ASSET_DATABASE_PATH', None)

if _db_path is not None and not os.path.exists(_db_path):
    print('Creating DB path: %r' % (_db_path,))
    os.mkdir(_db_path)

if _asset_path is not None and not os.path.exists(_asset_path):
    print('Creating Asset path: %r' % (_asset_path,))
    os.mkdir(_asset_path)
