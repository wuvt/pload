"""Add dj_id to QueuedTrack

Revision ID: 3ee9d7edb80e
Revises: 
Create Date: 2020-04-12 20:17:27.576595

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "3ee9d7edb80e"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("queued_track", sa.Column("dj_id", sa.Integer(), nullable=True))


def downgrade():
    op.drop_column("queued_track", "dj_id")
