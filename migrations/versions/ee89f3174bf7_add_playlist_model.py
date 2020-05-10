"""Add Playlist model

Revision ID: ee89f3174bf7
Revises: 3ee9d7edb80e
Create Date: 2020-05-09 05:56:10.899755

"""
from alembic import op
import datetime
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.declarative import declarative_base

# revision identifiers, used by Alembic.
revision = "ee89f3174bf7"
down_revision = "3ee9d7edb80e"
branch_labels = None
depends_on = None


Base = declarative_base()


class QueuedTrack(Base):
    __tablename__ = "queued_track"
    id = sa.Column(sa.Integer, primary_key=True)
    url = sa.Column(sa.Unicode(255), nullable=False)
    playlist_id = sa.Column(sa.Integer, sa.ForeignKey("playlist.id"))
    playlist = sa.orm.relationship(
        "Playlist", backref=sa.orm.backref("tracks", lazy="dynamic")
    )
    played = sa.Column(sa.Boolean, default=False, nullable=False)
    timeslot_start = sa.Column(sa.DateTime, nullable=False)
    timeslot_end = sa.Column(sa.DateTime, nullable=False)
    queue = sa.Column(sa.Unicode(255), nullable=True)
    dj_id = sa.Column(sa.Integer, nullable=True)


class Playlist(Base):
    __tablename__ = "playlist"
    id = sa.Column(sa.Integer, primary_key=True)
    timeslot_start = sa.Column(sa.DateTime, nullable=False)
    timeslot_end = sa.Column(sa.DateTime, nullable=False)
    dj_id = sa.Column(sa.Integer, nullable=True)
    queue = sa.Column(sa.Unicode(255), nullable=True)
    added = sa.Column(sa.DateTime, default=datetime.datetime.utcnow, nullable=True)
    approved = sa.Column(sa.DateTime, nullable=True)
    uploader = sa.Column(sa.Unicode(255), nullable=True)

    def __init__(self, timeslot_start, timeslot_end, dj_id=None, queue=None):
        self.timeslot_start = timeslot_start
        self.timeslot_end = timeslot_end
        self.dj_id = dj_id
        self.queue = queue


def upgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    # Add new tables, columns, and constraints
    Playlist.__table__.create(bind)
    op.add_column("queued_track", sa.Column("playlist_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "queued_track", "playlist", ["playlist_id"], ["id"])

    # Migrate data
    for timeslot_start, timeslot_end, queue, dj_id in session.query(
        QueuedTrack.timeslot_start,
        QueuedTrack.timeslot_end,
        QueuedTrack.queue,
        QueuedTrack.dj_id,
    ).group_by(
        QueuedTrack.timeslot_start,
        QueuedTrack.timeslot_end,
        QueuedTrack.queue,
        QueuedTrack.dj_id,
    ):
        if timeslot_start is not None and timeslot_end is not None:
            playlist = Playlist(timeslot_start, timeslot_end, dj_id, queue)
            session.add(playlist)
            session.commit()

            for track in session.query(QueuedTrack).filter(
                QueuedTrack.timeslot_start == timeslot_start,
                QueuedTrack.timeslot_end == timeslot_end,
                QueuedTrack.queue == queue,
                QueuedTrack.dj_id == dj_id,
            ):
                track.playlist_id = playlist.id
            session.commit()

    # Drop old columns
    op.drop_column("queued_track", "dj_id")
    op.drop_column("queued_track", "queue")
    op.drop_column("queued_track", "timeslot_end")
    op.drop_column("queued_track", "timeslot_start")


def downgrade():
    bind = op.get_bind()
    session = sa.orm.Session(bind=bind)

    # Add new columns
    op.add_column(
        "queued_track",
        sa.Column(
            "timeslot_start",
            postgresql.TIMESTAMP(),
            autoincrement=False,
            nullable=True,
        ),
    )
    op.add_column(
        "queued_track",
        sa.Column(
            "timeslot_end", postgresql.TIMESTAMP(), autoincrement=False, nullable=True
        ),
    )
    op.add_column(
        "queued_track",
        sa.Column("queue", sa.VARCHAR(length=255), autoincrement=False, nullable=True),
    )
    op.add_column(
        "queued_track",
        sa.Column("dj_id", sa.INTEGER(), autoincrement=False, nullable=True),
    )

    # Migrate data
    for playlist in session.query(Playlist):
        for track in playlist.tracks:
            track.timeslot_start = playlist.timeslot_start
            track.timeslot_end = playlist.timeslot_end
            track.queue = playlist.queue
            track.dj_id = playlist.dj_id
    session.commit()

    # Drop constraints, columns, and tables
    op.drop_constraint(
        "queued_track_playlist_id_fkey", "queued_track", type_="foreignkey"
    )
    op.drop_column("queued_track", "playlist_id")
    op.drop_table("playlist")
