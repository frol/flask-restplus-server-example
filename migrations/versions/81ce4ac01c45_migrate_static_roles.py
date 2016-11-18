"""Migrate static roles (new "internal" role type requires data migration)

Revision ID: 81ce4ac01c45
Revises: beb065460c24
Create Date: 2016-11-08 15:58:55.932297

"""

# revision identifiers, used by Alembic.
revision = '81ce4ac01c45'
down_revision = 'beb065460c24'

from alembic import op
import sqlalchemy as sa

UserHelper = sa.Table(
    'user',
    sa.MetaData(),
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('static_roles', sa.Integer),
)

def upgrade():
    connection = op.get_bind()
    for user in connection.execute(UserHelper.select()):
        if user.static_roles & 0x1000:
            continue
        new_static_roles = user.static_roles >> 1
        connection.execute(
            UserHelper.update().where(
                UserHelper.c.id == user.id
            ).values(
                static_roles=new_static_roles
            )
        )

def downgrade():
    connection = op.get_bind()
    for user in connection.execute(UserHelper.select()):
        if not user.static_roles & 0x1000:
            continue
        new_static_roles = user.static_roles << 1
        connection.execute(
            UserHelper.update().where(
                UserHelper.c.id == user.id
            ).values(
                static_roles=new_static_roles
            )
        )
