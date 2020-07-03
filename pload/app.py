import base64
import os
import urllib.parse
from flask import Flask
from .views import bp
from .db import db, init_db, migrate
from .es import es


def generate_nonce():
    """Returns a random nonce."""
    NONCE_LENGTH = 16
    return base64.b64encode(os.urandom(NONCE_LENGTH)).decode("utf-8")


def add_security_headers(script_nonce=None):
    def add_security_headers_func(response):
        csp_bits = ["default-src 'self'"]

        if script_nonce is not None:
            csp_bits.append("script-src 'self' 'nonce-{0}'".format(script_nonce))
        else:
            csp_bits.append("script-src 'self'")

        csp_bits.append("img-src 'self' data:")
        csp_bits.append("frame-ancestors 'self'")

        response.headers["Content-Security-Policy"] = "; ".join(csp_bits)
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    return add_security_headers_func


def create_app(config=None):
    app = Flask(__name__)

    app.config.from_object("pload.defaults")

    config_path = os.environ.get("APP_CONFIG_PATH", "config.json")
    app.config.from_json(config_path, silent=True)

    setup_app(app)
    return app


def setup_app(app):
    if app.config.get("PROXY_FIX") is not None:
        from werkzeug.contrib.fixers import ProxyFix

        app.wsgi_app = ProxyFix(
            app.wsgi_app, num_proxies=app.config["PROXY_FIX_NUM_PROXIES"]
        )

    if app.debug:
        from werkzeug.debug import DebuggedApplication

        app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

    from .filters import format_datetime, tztoutc

    app.jinja_env.filters.update(
        {
            "datetime": format_datetime,
            "urldecode": urllib.parse.unquote,
            "tztoutc": tztoutc,
        }
    )

    script_nonce = generate_nonce()
    app.jinja_env.globals["script_nonce"] = script_nonce
    app.after_request(add_security_headers(script_nonce))

    db.init_app(app)
    migrate.init_app(app, db)
    es.init_app(app)

    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite://"):
        with app.app_context():
            init_db()

    app.register_blueprint(bp, url_prefix="")

    from .api import bp as api_bp

    app.register_blueprint(api_bp, url_prefix="/api")


app = create_app()


@app.cli.command()
def initdb():
    with app.app_context():
        init_db()
