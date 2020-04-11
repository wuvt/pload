import os
from flask import Flask
from .views import bp
from .db import db, init_db


def add_security_headers(response):
    response.headers[
        "Content-Security-Policy"
    ] = "default-src 'self'; frame-ancestors 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


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

    from .filters import format_datetime

    app.jinja_env.filters.update(
        {"datetime": format_datetime,}
    )

    app.after_request(add_security_headers)
    db.init_app(app)

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
