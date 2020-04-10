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
