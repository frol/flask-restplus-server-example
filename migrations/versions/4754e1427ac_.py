"""empty message

Revision ID: 4754e1427ac
Revises: 2b5af066bb9
Create Date: 2015-11-27 19:43:31.118013

"""

# revision identifiers, used by Alembic.
revision = '4754e1427ac'
down_revision = '2b5af066bb9'

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


def upgrade():
    op.rename_table('team_members', 'team_member')
    op.add_column('team_member', sa.Column('is_leader', sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table('team_member') as batch_op:
        batch_op.drop_column('is_leader')
    op.rename_table('team_member', 'team_members')
