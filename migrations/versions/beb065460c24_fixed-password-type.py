"""Upgraded to the correct PasswordType implementation
https://github.com/kvesteri/sqlalchemy-utils/pull/254

Revision ID: beb065460c24
Revises: 8c8b2d23a5
Create Date: 2016-11-09 09:10:40.630496

"""

# revision identifiers, used by Alembic.
revision = 'beb065460c24'
down_revision = '8c8b2d23a5'

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


UserHelper = sa.Table(
    'user',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('password', sa.String),
    sa.Column('_password', sa.String),
)

def upgrade():
    connection = op.get_bind()
    if connection.engine.name != 'sqlite':
        return
    
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('_password',
               sqlalchemy_utils.types.password.PasswordType(max_length=128),
               server_default='',
               nullable=False
            ))
    
    connection.execute(
            UserHelper.update().values(_password=UserHelper.c.password)
        )
    
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('password')
        batch_op.alter_column('_password', server_default=None, new_column_name='password')


def downgrade():
    connection = op.get_bind()
    if connection.engine.name != 'sqlite':
        return
    
    with op.batch_alter_table('user') as batch_op:
        batch_op.add_column(sa.Column('_password',
               type_=sa.NUMERIC(precision=128),
               server_default='',
               nullable=False
            ))
    
    connection.execute(
            UserHelper.update().values(_password=UserHelper.c.password)
        )
    
    with op.batch_alter_table('user') as batch_op:
        batch_op.drop_column('password')
        batch_op.alter_column('_password', server_default=None, new_column_name='password')
