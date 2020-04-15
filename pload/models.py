from .db import db


class QueuedTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Unicode(255), nullable=False)
    timeslot_start = db.Column(db.DateTime, nullable=False)
    timeslot_end = db.Column(db.DateTime, nullable=False)
    queue = db.Column(db.Unicode(255), nullable=True)
    played = db.Column(db.Boolean, default=False, nullable=False)
    dj_id = db.Column(db.Integer)

    def __init__(self, url, timeslot_start, timeslot_end, queue=None, dj_id=None):
        self.url = url
        self.timeslot_start = timeslot_start
        self.timeslot_end = timeslot_end
        self.queue = queue
        self.dj_id = dj_id

    def serialize(self):
        return {
            "id": self.id,
            "url": self.url,
            "timeslot_start": self.timeslot_start,
            "timeslot_end": self.timeslot_end,
            "queue": self.queue,
            "played": self.played,
            "dj_id": self.dj_id,
        }
