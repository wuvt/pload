import datetime
import requests
import urllib.parse
from flask import Blueprint, current_app, make_response
from .kv import redis_client
from .view_utils import require_auth


bp = Blueprint('pload_api_v1', __name__)


@bp.route('/next_track')
@require_auth
def next_track():
    now = datetime.datetime.now()

    current_slot = None
    for hour, slot in current_app.config['TIME_SLOTS_BY_HOUR'].items():
        if hour <= now.hour:
            current_slot = slot

    if current_slot is None:
        return "", 500, {'Content-Type': "text/plain"}

    filename = '{0}-{1}.m3u'.format(now.strftime('%Y%m%d'), current_slot)

    r = requests.get(urllib.parse.urljoin(
        current_app.config['PLAYLISTS_BASE_URL'], filename))
    if r.status_code != 200:
        return "", 404, {'Content-Type': "text/plain"}
    data = r.text

    key = 'playlist:{0}:index'.format(filename)
    value = redis_client.get(key)
    if value is not None:
        expected_index = int(value)
    else:
        expected_index = None

    file_index = 0
    for line in data.splitlines():
        if line.startswith('#'):
            continue

        if expected_index is None or file_index == expected_index:
            redis_client.incr(key, 1)
            redis_client.expire(key, 86400)

            resp = make_response("{0}\n".format(line))
            resp.headers['Content-Type'] = "text/plain"
            return resp
        else:
            file_index += 1

    # if we made it here, we've ran out of songs in the playlist
    return "", 404, {'Content-Type': "text/plain"}


@bp.route('/underwriting')
@require_auth
def underwriting():
    # TODO
    return "", 404, {'Content-Type': "text/plain"}
