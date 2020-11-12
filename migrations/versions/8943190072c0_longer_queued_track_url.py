"""Allow longer queued track URL

Revision ID: 8943190072c0
Revises: ee89f3174bf7
Create Date: 2020-11-12 02:12:28.748714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8943190072c0'
down_revision = 'ee89f3174bf7'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'queued_track',
        'url',
        existing_type=sa.VARCHAR(length=255),
        type_=sa.VARCHAR(length=2048))


def downgrade():
    op.alter_column(
        'queued_track',
        'url',
        existing_type=sa.VARCHAR(length=2048),
        type_=sa.VARCHAR(length=255))
