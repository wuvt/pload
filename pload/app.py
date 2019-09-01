import os
from flask import Flask
from .views import bp


def create_app(config=None):
    app = Flask(__name__)

    app.config.from_object('pload.defaults')

    config_path = os.environ.get('APP_CONFIG_PATH', 'config.json')
    app.config.from_json(config_path, silent=True)

    setup_app(app)
    return app


def setup_app(app):
    if app.config.get('PROXY_FIX') is not None:
        from werkzeug.contrib.fixers import ProxyFix
        app.wsgi_app = ProxyFix(
            app.wsgi_app,
            num_proxies=app.config['PROXY_FIX_NUM_PROXIES'])

    if app.debug:
        from werkzeug.debug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

    app.register_blueprint(bp, url_prefix='')


app = create_app()
