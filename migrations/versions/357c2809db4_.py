"""empty message

Revision ID: 357c2809db4
Revises: 4754e1427ac
Create Date: 2015-11-27 20:22:12.644342

"""

# revision identifiers, used by Alembic.
revision = '357c2809db4'
down_revision = '4754e1427ac'

from alembic import op
import sqlalchemy as sa


def upgrade():
    with op.batch_alter_table('team_member') as batch_op:
        batch_op.alter_column('is_leader',
               existing_type=sa.BOOLEAN(),
               nullable=False)


def downgrade():
    with op.batch_alter_table('team_member') as batch_op:
        batch_op.alter_column('is_leader',
               existing_type=sa.BOOLEAN(),
               nullable=True)
