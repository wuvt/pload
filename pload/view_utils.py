import re
import requests
import requests.exceptions
from dateutil.tz import gettz
from flask import current_app, make_response, request
from functools import wraps
from .exceptions import PlaylistValidationException


annotate_split_re = re.compile(r":(?=(?:[^\"]*\"[^\"]*\")*[^\"]*$)")


def require_auth(f):
    @wraps(f)
    def require_auth_wrapper(*args, **kwargs):
        expected_username = current_app.config["BASIC_AUTH_USERNAME"]
        expected_password = current_app.config["BASIC_AUTH_PASSWORD"]

        auth = request.authorization
        if (
            auth
            and auth.type == "basic"
            and auth.username == expected_username
            and auth.password == expected_password
        ):
            return f(*args, **kwargs)
        else:
            resp = make_response("", 401)
            resp.headers["Content-Type"] = "text/plain"
            resp.headers["WWW-Authenticate"] = "Basic realm='Restricted'"
            return resp

    return require_auth_wrapper


def get_slot_tz():
    return gettz(current_app.config["TIME_SLOT_TZ"])


def validate_url(url):
    if current_app.config["TRACK_VALIDATE_CHECK_EXISTS"]:
        try:
            r = requests.get(url)
            r.raise_for_status()
        except requests.exceptions.RequestException:
            return False

    return True


def process_url(url, skip_validate=False):
    if url.startswith("annotate:"):
        frags = annotate_split_re.split(url, 2)
        frags[2] = process_url(url, skip_validate)
        return ":".join(frags)
    elif url.startswith("ffmpeg:") or url.startswith("replay_gain:"):
        frags = url.split(":", 1)
        frags[1] = process_url(url, skip_validate)
        return ":".join(frags)
    elif url[0:7] == "http://" or url[0:8] == "https://":
        url = requests.utils.requote_uri(url)
        if not skip_validate and not validate_url(url):
            raise PlaylistValidationException()
        return url
    else:
        if not skip_validate:
            raise PlaylistValidationException()
        else:
            return url


def get_dj_list():
    try:
        r = requests.get(
            "{0}/api/playlists/dj".format(
                current_app.config["TRACKMAN_URL"].rstrip("/")
            )
        )
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        current_app.logger.warning("Failed to load DJ list: {0}".format(e))
        return []
    else:
        return r.json().get("djs", [])
