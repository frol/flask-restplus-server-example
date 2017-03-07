"""Alter OAuth2Token.token_type to Enum

Revision ID: 82184d7d1e88
Revises: 5e2954a2af18
Create Date: 2016-11-10 21:14:33.787194

"""

# revision identifiers, used by Alembic.
revision = '82184d7d1e88'
down_revision = '5e2954a2af18'

from alembic import op
import sqlalchemy as sa


def upgrade():
    connection = op.get_bind()


    with op.batch_alter_table('oauth2_token') as batch_op:
        tokentypes = sa.dialects.postgresql.ENUM('Bearer', name='tokentypes')
        tokentypes.create(connection)

        batch_op.alter_column('token_type',
               existing_type=sa.VARCHAR(length=40),
               type_=sa.Enum('Bearer', name='tokentypes'),
               existing_nullable=False,
               postgresql_using='token_type::tokentypes')


def downgrade():
    connection = op.get_bind()

    with op.batch_alter_table('oauth2_token') as batch_op:
        batch_op.alter_column('token_type',
               existing_type=sa.Enum('Bearer', name='tokentypes'),
               type_=sa.VARCHAR(length=40),
               existing_nullable=False)

    tokentypes = sa.dialects.postgresql.ENUM('Bearer', name='tokentypes')
    tokentypes.drop(connection)
