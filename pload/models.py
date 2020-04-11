from .db import db


class QueuedTrack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.Unicode(255), nullable=False)
    timeslot_start = db.Column(db.DateTime, nullable=False)
    timeslot_end = db.Column(db.DateTime, nullable=False)
    queue = db.Column(db.Unicode(255), nullable=True)
    played = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, url, timeslot_start, timeslot_end, queue=None):
        self.url = url
        self.timeslot_start = timeslot_start
        self.timeslot_end = timeslot_end
        self.queue = queue
