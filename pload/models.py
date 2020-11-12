import datetime
from .db import db


class QueuedTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Unicode(2048), nullable=False)
    played = db.Column(db.Boolean, default=False, nullable=False)
    playlist_id = db.Column(db.Integer, db.ForeignKey("playlist.id"))
    playlist = db.relationship("Playlist", backref=db.backref("tracks", lazy="dynamic"))

    def __init__(self, url, playlist_id):
        self.url = url
        self.playlist_id = playlist_id

    def serialize(self):
        return {
            "id": self.id,
            "url": self.url,
            "played": self.played,
        }


class Playlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timeslot_start = db.Column(db.DateTime, nullable=False)
    timeslot_end = db.Column(db.DateTime, nullable=False)
    dj_id = db.Column(db.Integer, nullable=True)
    queue = db.Column(db.Unicode(255), nullable=True)
    added = db.Column(db.DateTime, default=datetime.datetime.utcnow, nullable=True)
    approved = db.Column(db.DateTime, nullable=True)
    uploader = db.Column(db.Unicode(255), nullable=True)

    def __init__(self, timeslot_start, timeslot_end, dj_id=None, queue=None):
        self.timeslot_start = timeslot_start
        self.timeslot_end = timeslot_end
        self.dj_id = dj_id
        self.queue = queue

    def serialize(self):
        return {
            "id": self.id,
            "timeslot_start": self.timeslot_start,
            "timeslot_end": self.timeslot_end,
            "dj_id": self.dj_id,
            "queue": self.queue,
            "added": self.added,
            "approved": self.approved,
            "uploader": self.uploader,
        }
