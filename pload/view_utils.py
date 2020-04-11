import requests
import requests.exceptions
from dateutil.tz import gettz
from flask import current_app, make_response, request
from functools import wraps


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
