import datetime
import os.path
import requests
import urllib.parse
from flask import Blueprint, current_app, make_response, request
from .kv import redis_client
from .view_utils import require_auth


bp = Blueprint("pload_api_v1", __name__)


@bp.route("/next_track")
@require_auth
def next_track():
    now = datetime.datetime.now()

    current_slot = None
    for hour, slot in current_app.config["TIME_SLOTS_BY_HOUR"].items():
        if hour <= now.hour:
            current_slot = slot

    if current_slot is None:
        return "", 500, {"Content-Type": "text/plain"}

    filename = "{0}-{1}.m3u".format(now.strftime("%Y%m%d"), current_slot)

    # prerecorded playlists contain station IDs, PSAs, promos, etc. as part of
    # the playlist already; they are stored at a different location and use a
    # different key prefix
    if request.args.get("prerecorded") == "1":
        playlist_key = "prerecorded:{0}:index".format(filename)
    else:
        playlist_key = "playlist:{0}:index".format(filename)

    if len(current_app.config.get("DEST_PATH", "")) <= 0:
        if request.args.get("prerecorded") == "1":
            playlist_url = urllib.parse.urljoin(
                current_app.config["PLAYLISTS_BASE_URL"], "prerecorded", filename
            )
        else:
            playlist_url = urllib.parse.urljoin(
                current_app.config["PLAYLISTS_BASE_URL"], filename
            )

        r = requests.get(playlist_url)
        if r.status_code != 200:
            return "", 404, {"Content-Type": "text/plain"}
        data = r.text
    else:
        if request.args.get("prerecorded") == "1":
            filepath = os.path.join(
                current_app.config["DEST_PATH"], "prerecorded", filename
            )
        else:
            filepath = os.path.join(current_app.config["DEST_PATH"], filename)

        if not os.path.exists(filepath):
            return "", 404, {"Content-Type": "text/plain"}

        with open(filepath) as f:
            data = f.readlines()

    value = redis_client.get(playlist_key)
    if value is not None:
        expected_index = int(value)
    else:
        expected_index = None

    file_index = 0
    for line in data.splitlines():
        if line.startswith("#"):
            continue

        if expected_index is None or file_index == expected_index:
            redis_client.incr(playlist_key, 1)
            redis_client.expire(playlist_key, 86400)

            resp = make_response("{0}\n".format(line))
            resp.headers["Content-Type"] = "text/plain"
            return resp
        else:
            file_index += 1

    # if we made it here, we've run out of songs in the playlist
    return "", 404, {"Content-Type": "text/plain"}


@bp.route("/underwriting")
@require_auth
def underwriting():
    # TODO
    return "", 404, {"Content-Type": "text/plain"}
