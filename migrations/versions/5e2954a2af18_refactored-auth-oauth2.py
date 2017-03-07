"""Refactored auth.OAuth2 models

Revision ID: 5e2954a2af18
Revises: 81ce4ac01c45
Create Date: 2016-11-10 16:45:41.153837

"""

# revision identifiers, used by Alembic.
revision = '5e2954a2af18'
down_revision = '81ce4ac01c45'

import enum

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


OAuth2Client = sa.Table(
    'oauth2_client',
    sa.MetaData(),
    sa.Column('default_scopes', sa.String),
    sa.Column('_default_scopes', sa.String),
    sa.Column('redirect_uris', sa.String),
    sa.Column('_redirect_uris', sa.String),
)

OAuth2Grant = sa.Table(
    'oauth2_grant',
    sa.MetaData(),
    sa.Column('scopes', sa.String),
    sa.Column('_scopes', sa.String),
)

OAuth2Token = sa.Table(
    'oauth2_token',
    sa.MetaData(),
    sa.Column('scopes', sa.String),
    sa.Column('_scopes', sa.String),
)


def upgrade():
    connection = op.get_bind()

    clienttypes = sa.dialects.postgresql.ENUM('public', 'confidential', name='clienttypes')
    clienttypes.create(connection)

    with op.batch_alter_table('oauth2_client') as batch_op:
        batch_op.add_column(
            sa.Column(
                'client_type',
                sa.Enum('public', 'confidential', name='clienttypes'),
                server_default='public',
                nullable=False
            )
        )
        batch_op.add_column(
            sa.Column(
                'default_scopes',
                sqlalchemy_utils.types.scalar_list.ScalarListType(),
                server_default='',
                nullable=False
            )
        )
        batch_op.add_column(
            sa.Column(
                'redirect_uris',
                sqlalchemy_utils.types.scalar_list.ScalarListType(),
                server_default='',
                nullable=False
            )
        )

    connection.execute(
            OAuth2Client.update().values(default_scopes=OAuth2Client.c._default_scopes)
        )
    connection.execute(
            OAuth2Client.update().values(redirect_uris=OAuth2Client.c._redirect_uris)
        )

    with op.batch_alter_table('oauth2_client') as batch_op:
        batch_op.drop_column('_redirect_uris')
        batch_op.drop_column('_default_scopes')
        batch_op.alter_column('redirect_uris', server_default=None)
        batch_op.alter_column('default_scopes', server_default=None)

    with op.batch_alter_table('oauth2_grant') as batch_op:
        batch_op.add_column(
            sa.Column(
                'scopes',
                sqlalchemy_utils.types.scalar_list.ScalarListType(),
                server_default='',
                nullable=False
            )
        )

    connection.execute(
            OAuth2Grant.update().values(scopes=OAuth2Grant.c._scopes)
        )

    with op.batch_alter_table('oauth2_grant') as batch_op:
        batch_op.drop_column('_scopes')
        batch_op.alter_column('scopes', server_default=None)

    with op.batch_alter_table('oauth2_token') as batch_op:
        batch_op.add_column(
            sa.Column(
                'scopes',
                sqlalchemy_utils.types.scalar_list.ScalarListType(),
                server_default='',
                nullable=False
            )
        )

    connection.execute(
            OAuth2Token.update().values(scopes=OAuth2Token.c._scopes)
        )

    with op.batch_alter_table('oauth2_token') as batch_op:
        batch_op.drop_column('_scopes')
        batch_op.alter_column('scopes', server_default=None)


def downgrade():
    connection = op.get_bind()

    with op.batch_alter_table('oauth2_token') as batch_op:
        batch_op.add_column(sa.Column('_scopes', sa.TEXT(), server_default='', nullable=False))

    connection.execute(
            OAuth2Token.update().values(_scopes=OAuth2Token.c.scopes)
        )

    with op.batch_alter_table('oauth2_token') as batch_op:
        batch_op.drop_column('scopes')

    with op.batch_alter_table('oauth2_grant') as batch_op:
        batch_op.add_column(sa.Column('_scopes', sa.TEXT(), server_default='', nullable=False))

    connection.execute(
            OAuth2Grant.update().values(_scopes=OAuth2Grant.c.scopes)
        )

    with op.batch_alter_table('oauth2_grant') as batch_op:
        batch_op.drop_column('scopes')

    with op.batch_alter_table('oauth2_client') as batch_op:
        batch_op.add_column(
            sa.Column(
                '_default_scopes',
                sa.TEXT(),
                server_default='',
                nullable=False
            )
        )
        batch_op.add_column(
            sa.Column(
                '_redirect_uris',
                sa.TEXT(),
                server_default='',
                nullable=False
            )
        )

    connection.execute(
            OAuth2Client.update().values(_default_scopes=OAuth2Client.c.default_scopes)
        )
    connection.execute(
            OAuth2Client.update().values(_redirect_uris=OAuth2Client.c.redirect_uris)
        )

    with op.batch_alter_table('oauth2_client') as batch_op:
        batch_op.drop_column('redirect_uris')
        batch_op.drop_column('default_scopes')
        batch_op.drop_column('client_type')

    clienttypes = sa.dialects.postgresql.ENUM('public', 'confidential', name='clienttypes')
    clienttypes.drop(connection)
