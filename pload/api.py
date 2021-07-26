import datetime
import elasticsearch
import mutagen
import requests
import tempfile
import urllib.parse
from flask import Blueprint, jsonify, make_response, request
from .db import db
from .es import es
from .exceptions import PlaylistValidationException
from .models import QueuedTrack, Playlist
from .view_utils import require_auth, get_file_url, process_url


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
        queue = "default"

    playlist = Playlist.query.filter(
        Playlist.timeslot_start <= now,
        Playlist.timeslot_end > now,
        Playlist.queue == queue,
        Playlist.approved != None,
    ).first()
    if playlist is not None:
        next_track = (
            QueuedTrack.query.filter(
                QueuedTrack.playlist_id == playlist.id,
                QueuedTrack.played == False,
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
        result = {
            "result": True,
            "url": url,
        }

        if not request.args.get("skip_metadata"):
            file_url = get_file_url(url)

            try:
                results = es.search(
                    body={
                        "query": {
                            "match": {
                                "url": file_url,
                            }
                        }
                    }
                )
                if results is not None and len(results["hits"]) > 0:
                    for item in results["hits"]["hits"]:
                        # need to make sure URL is an exact match
                        if item["_source"]["url"] == url:
                            for k, v in item["_source"].items():
                                if k != "url":
                                    result[k] = v
                            return jsonify(result)
            except (
                elasticsearch.ImproperlyConfigured,
                elasticsearch.ElasticsearchException,
                elasticsearch.exceptions.RequestError,
            ):
                pass

            ext = file_url.rsplit(".", 1)[-1]

            with tempfile.NamedTemporaryFile(suffix="." + ext) as f:
                try:
                    r = requests.get(file_url, stream=True)
                    r.raise_for_status()
                except requests.exceptions.RequestException:
                    return jsonify(result)

                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                f.seek(0, 0)

                try:
                    m = mutagen.File(f, easy=True)
                except mutagen.MutagenError:
                    pass
                else:
                    if m is not None:
                        tags_to_copy = ("artist", "title", "album", "label")
                        for tag in tags_to_copy:
                            if m.get(tag) is not None and len(m.get(tag)) > 0:
                                result[tag] = m[tag][0]

                        try:
                            result.update(
                                {
                                    "bitrate": m.info.bitrate // 1000,
                                    "sample": m.info.sample_rate,
                                    "length": int(m.info.length),
                                }
                            )
                        except AttributeError:
                            pass

        return jsonify(result)


@bp.route("/search")
def search():
    results = es.search(q=request.args["q"])
    return jsonify(results["hits"])
