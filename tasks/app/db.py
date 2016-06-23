# encoding: utf-8
# pylint: disable=invalid-name,unused-argument,too-many-arguments
"""
Application database related tasks for Invoke.

Forked from flask-migrate
"""
import argparse
import functools
import logging
import os

try:
    from invoke import ctask as task
except ImportError:  # Invoke 0.13 renamed ctask to task
    from invoke import task

log = logging.getLogger(__name__) # pylint: disable=invalid-name

try:
    from alembic import __version__ as __alembic_version__
    from alembic.config import Config as AlembicConfig
    from alembic import command
except ImportError:
    log.warning("Alembic cannot be imported, so some app.db.* tasks won't be available!")
else:

    alembic_version = tuple([int(v) for v in __alembic_version__.split('.')[0:3]])


    class Config(AlembicConfig):
        """
        Custom config that overwrites template directory.
        """
        def get_template_directory(self):
            package_dir = os.path.abspath(os.path.dirname(__file__))
            return os.path.join(package_dir, 'db_templates')


    def _get_config(directory, x_arg=None, opts=None):
        """
        A helper that prepares AlembicConfig instance.
        """
        config = Config(os.path.join(directory, 'alembic.ini'))
        config.set_main_option('script_location', directory)
        if config.cmd_opts is None:
            config.cmd_opts = argparse.Namespace()
        for opt in opts or []:
            setattr(config.cmd_opts, opt, True)
        if x_arg is not None:
            if not getattr(config.cmd_opts, 'x', None):
                setattr(config.cmd_opts, 'x', [x_arg])
            else:
                config.cmd_opts.x.append(x_arg)
        return config

    @task(
        help={
            'directory': "migration script directory",
            'multidb': "Multiple databases migraton",
        }
    )
    def init(context, directory='migrations', multidb=False):
        """Generates a new migration"""
        from app import create_app
        with create_app().app_context():
            config = Config()
            config.set_main_option('script_location', directory)
            config.config_file_name = os.path.join(directory, 'alembic.ini')
            if multidb:
                command.init(config, directory, 'flask-multidb')
            else:
                command.init(config, directory, 'flask')


    @task(
        help={
            'rev_id': "Specify a hardcoded revision id instead of generating one",
            'version_path': "Specify specific path from config for version file",
            'branch_label': "Specify a branch label to apply to the new revision",
            'splice': "Allow a non-head revision as the 'head' to splice onto",
            'head': "Specify head revision or <branchname>@head to base new revision on",
            'sql': "Don't emit SQL to database - dump to standard output instead",
            'autogenerate': "Populate revision script with andidate migration operatons, based " \
                            "on comparison of database to model",
            'directory': "migration script directory",
        }
    )
    def revision(context, directory='migrations', message=None, autogenerate=False, sql=False,
                 head='head', splice=False, branch_label=None, version_path=None, rev_id=None):
        """Create a new revision file."""
        from app import create_app
        with create_app().app_context():
            config = _get_config(directory)
            if alembic_version >= (0, 7, 0):
                command.revision(config, message, autogenerate=autogenerate, sql=sql,
                                 head=head, splice=splice, branch_label=branch_label,
                                 version_path=version_path, rev_id=rev_id)
            else:
                command.revision(config, message, autogenerate=autogenerate, sql=sql)

    @task(
        help={
            'rev_id': "Specify a hardcoded revision id instead of generating one",
            'version_path': "Specify specific path from config for version file",
            'branch_label': "Specify a branch label to apply to the new revision",
            'splice': "Allow a non-head revision as the 'head' to splice onto",
            'head': "Specify head revision or <branchname>@head to base new revision on",
            'sql': "Don't emit SQL to database - dump to standard output instead",
            'directory': "migration script directory",
        }
    )
    def migrate(context, directory='migrations', message=None, sql=False, head='head', splice=False,
                branch_label=None, version_path=None, rev_id=None):
        """Alias for 'revision --autogenerate'"""
        from app import create_app
        with create_app().app_context():
            config = _get_config(directory, opts=['autogenerate'])
            if alembic_version >= (0, 7, 0):
                command.revision(config, message, autogenerate=True, sql=sql, head=head,
                                 splice=splice, branch_label=branch_label,
                                 version_path=version_path, rev_id=rev_id)
            else:
                command.revision(config, message, autogenerate=True, sql=sql)

    @task(
        help={
            'revision': "revision identifier",
            'directory': "migration script directory",
        }
    )
    def edit(context, revision='current', directory='migrations'):
        """Upgrade to a later version"""
        from app import create_app
        with create_app().app_context():
            if alembic_version >= (0, 8, 0):
                config = _get_config(directory)
                command.edit(config, revision)
            else:
                raise RuntimeError('Alembic 0.8.0 or greater is required')

    @task(
        help={
            'rev_id': "Specify a hardcoded revision id instead of generating one",
            'branch_label': "Specify a branch label to apply to the new revision",
            'message': "one or more revisions, or 'heads' for all heads",
            'directory': "migration script directory",
        }
    )
    def merge(context, directory='migrations', revisions='', message=None, branch_label=None,
              rev_id=None):
        """Merge two revisions together.  Creates a new migration file"""
        from app import create_app
        with create_app().app_context():
            if alembic_version >= (0, 7, 0):
                config = _get_config(directory)
                command.merge(config, revisions, message=message,
                              branch_label=branch_label, rev_id=rev_id)
            else:
                raise RuntimeError('Alembic 0.7.0 or greater is required')

    @task(
        help={
            'tag': "Arbitrary 'tag' name - can be used by custom env.py scripts",
            'sql': "Don't emit SQL to database - dump to standard output instead",
            'revision': "revision identifier",
            'directory': "migration script directory",
            'x_arg': "Additional arguments consumed by custom env.py scripts",
        }
    )
    def upgrade(context, directory='migrations', revision='head', sql=False, tag=None, x_arg=None):
        """Upgrade to a later version"""
        from app import create_app
        with create_app().app_context():
            config = _get_config(directory, x_arg=x_arg)
            command.upgrade(config, revision, sql=sql, tag=tag)


    @task(
        help={
            'tag': "Arbitrary 'tag' name - can be used by custom env.py scripts",
            'sql': "Don't emit SQL to database - dump to standard output instead",
            'revision': "revision identifier",
            'directory': "migration script directory",
            'x_arg': "Additional arguments consumed by custom env.py scripts",
        }
    )
    def downgrade(context, directory='migrations', revision='-1', sql=False, tag=None, x_arg=None):
        """Revert to a previous version"""
        from app import create_app
        with create_app().app_context():
            config = _get_config(directory, x_arg=x_arg)
            if sql and revision == '-1':
                revision = 'head:-1'
            command.downgrade(config, revision, sql=sql, tag=tag)

    @task(
        help={
            'revision': "revision identifier",
            'directory': "migration script directory",
        }
    )
    def show(context, directory='migrations', revision='head'):
        """Show the revision denoted by the given symbol."""
        from app import create_app
        with create_app().app_context():
            if alembic_version >= (0, 7, 0):
                config = _get_config(directory)
                command.show(config, revision)
            else:
                raise RuntimeError('Alembic 0.7.0 or greater is required')

    @task(
        help={
            'verbose': "Use more verbose output",
            'rev_range': "Specify a revision range; format is [start]:[end]",
            'directory': "migration script directory",
        }
    )
    def history(context, directory='migrations', rev_range=None, verbose=False):
        """List changeset scripts in chronological order."""
        from app import create_app
        with create_app().app_context():
            config = _get_config(directory)
            if alembic_version >= (0, 7, 0):
                command.history(config, rev_range, verbose=verbose)
            else:
                command.history(config, rev_range)

    @task(
        help={
            'resolve_dependencies': "Treat dependency versions as down revisions",
            'verbose': "Use more verbose output",
            'directory': "migration script directory",
        }
    )
    def heads(context, directory='migrations', verbose=False, resolve_dependencies=False):
        """Show current available heads in the script directory"""
        from app import create_app
        with create_app().app_context():
            if alembic_version >= (0, 7, 0):
                config = _get_config(directory)
                command.heads(config, verbose=verbose,
                              resolve_dependencies=resolve_dependencies)
            else:
                raise RuntimeError('Alembic 0.7.0 or greater is required')

    @task(
        help={
            'verbose': "Use more verbose output",
            'directory': "migration script directory",
        }
    )
    def branches(context, directory='migrations', verbose=False):
        """Show current branch points"""
        from app import create_app
        with create_app().app_context():
            config = _get_config(directory)
            if alembic_version >= (0, 7, 0):
                command.branches(config, verbose=verbose)
            else:
                command.branches(config)

    @task(
        help={
            'head_only': "Deprecated. Use --verbose for additional output",
            'verbose': "Use more verbose output",
            'directory': "migration script directory",
        }
    )
    def current(context, directory='migrations', verbose=False, head_only=False):
        """Display the current revision for each database."""
        from app import create_app
        with create_app().app_context():
            config = _get_config(directory)
            if alembic_version >= (0, 7, 0):
                command.current(config, verbose=verbose, head_only=head_only)
            else:
                command.current(config)

    @task(
        help={
            'tag': "Arbitrary 'tag' name - can be used by custom env.py scripts",
            'sql': "Don't emit SQL to database - dump to standard output instead",
            'revision': "revision identifier",
            'directory': "migration script directory",
        }
    )
    def stamp(context, directory='migrations', revision='head', sql=False, tag=None):
        """'stamp' the revision table with the given revision; don't run any
        migrations"""
        from app import create_app
        with create_app().app_context():
            config = _get_config(directory)
            command.stamp(config, revision, sql=sql, tag=tag)


@task
def init_development_data(context, upgrade_db=True, skip_on_failure=False):
    """
    Fill a database with development data like default users.
    """
    if upgrade_db:
        context.invoke_execute(context, 'app.db.upgrade')

    log.info("Initializing development data...")

    import app
    flask_app = app.create_app()

    with flask_app.app_context():
        from migrations import initial_development_data
        try:
            initial_development_data.init()
        except AssertionError as exception:
            if not skip_on_failure:
                log.error("%s", exception)
            else:
                log.debug(
                    "The following error was ignored due to the `skip_on_failure` flag: %s",
                    exception
                )
                log.info("Initializing development data step is skipped.")
        else:
            log.info("Fixtures have been successfully applied.")
