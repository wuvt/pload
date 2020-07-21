PLOAD_NAME = "Playlist Loader"
PROXY_FIX_NUM_PROXIES = 1

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

ELASTICSEARCH_HOSTS = [
    "http://elasticsearch:9200/",
]

TIME_SLOT_TZ = "America/New_York"

TRACKMAN_URL = "https://trackman-fm.apps.wuvt.vt.edu/"

TRACK_VALIDATE_CHECK_EXISTS = True
TRACK_URL_REWRITES = [
    (r"^https:\/\/files\.apps\.wuvt\.vt\.edu", "http://alexandria.wuvt.vt.edu"),
    (
        r"^https:\/\/linx\.apps\.wuvt\.vt\.edu(\/[^\/]+)$",
        "https://linx.apps.wuvt.vt.edu/selif\\1",
    ),
]
TRACK_URL_DISPLAY_REWRITES = [
    (r"^http:\/\/alexandria\.wuvt\.vt\.edu", "https://files.apps.wuvt.vt.edu"),
    (r"^http:\/\/192\.168\.0\.25", "https://files.apps.wuvt.vt.edu"),
    (
        r"^https:\/\/linx\.apps\.wuvt\.vt\.edu\/selif\/",
        "https://linx.apps.wuvt.vt.edu/",
    ),
]
