import datetime
from flask import Blueprint, make_response, request
from .db import db
from .models import QueuedTrack
from .view_utils import require_auth


bp = Blueprint("pload_api_v1", __name__)

output_content_type = "text/plain; charset=utf-8"


@bp.route("/next_track")
@require_auth
def next_track():
    now = datetime.datetime.utcnow()

    # prerecorded playlists contain station IDs, PSAs, promos, etc. as part of
    # the playlist already
    if request.args.get("prerecorded") == "1":
        queue = "prerecorded"
    else:
        queue = None

    next_track = QueuedTrack.query.filter(
        QueuedTrack.timeslot_start <= now,
        QueuedTrack.timeslot_end > now,
        QueuedTrack.queue == queue,
        QueuedTrack.played == False,
    ).first()

    if next_track is not None:
        next_track.played = True
        db.session.commit()

        url = next_track.url
        if next_track.dj_id is not None and next_track.dj_id > 1:
            url = "annotate:trackman_dj_id={dj_id:d}:{url}".format(
                dj_id=next_track.dj_id, url=url
            )

        resp = make_response("{0}\n".format(url))
        resp.headers["Content-Type"] = output_content_type
        return resp

    # if we made it here, we've run out of songs in the playlist
    return "", 404, {"Content-Type": output_content_type}


@bp.route("/underwriting")
@require_auth
def underwriting():
    # TODO
    return "", 404, {"Content-Type": output_content_type}
