"""empty message

Revision ID: 8c8b2d23a5
Revises: 357c2809db4
Create Date: 2015-11-27 20:43:11.241948

"""

# revision identifiers, used by Alembic.
revision = '8c8b2d23a5'
down_revision = '357c2809db4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('team_member') as batch_op:
        batch_op.create_unique_constraint('_team_user_uc', ['team_id', 'user_id'])


def downgrade():
    with op.batch_alter_table('team_member') as batch_op:
        batch_op.drop_constraint('_team_user_uc', type_='unique')
