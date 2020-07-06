import datetime
from flask import Blueprint, jsonify, make_response, request
from .db import db
from .es import es
from .exceptions import PlaylistValidationException
from .models import QueuedTrack, Playlist
from .view_utils import require_auth, process_url


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

    playlist = Playlist.query.filter(
        Playlist.timeslot_start <= now,
        Playlist.timeslot_end > now,
        Playlist.queue == queue,
        # Playlist.approved != None,
    ).first()
    if playlist is not None:
        next_track = (
            QueuedTrack.query.filter(
                QueuedTrack.playlist_id == playlist.id, QueuedTrack.played == False,
            )
            .order_by(QueuedTrack.id)
            .first()
        )

        if next_track is not None:
            next_track.played = True
            db.session.commit()

            url = next_track.url
            if playlist.dj_id is not None and playlist.dj_id > 1:
                url = "annotate:trackman_dj_id={dj_id:d}:{url}".format(
                    dj_id=playlist.dj_id, url=url
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


@bp.route("/validate_track")
def validate_track():
    try:
        url = process_url(request.args["url"])
    except PlaylistValidationException:
        return jsonify({"result": False})
    else:
        return jsonify({"result": True, "url": url,})


@bp.route("/search")
def search():
    results = es.search(q=request.args["q"])
    return jsonify(results["hits"])
