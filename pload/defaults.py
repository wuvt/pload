PLOAD_NAME = "Playlist Loader"
PROXY_FIX_NUM_PROXIES = 1

SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

TIME_SLOTS = {
    "early": "Overnight (00:00-06:00)",
    "morning": "Early Morning (06:00-09:00)",
    "noon": "Morning to Midday (09:00-14:00)",
    "afternoon": "Afternoon (14:00-17:00)",
    "jazz": "Rush Hour Jazz (17:00-19:00)",
    "night": "Evening (19:00-00:00)",
}

TIME_SLOTS_BY_HOUR = {
    0: "early",
    6: "morning",
    14: "noon",
    17: "jazz",
    19: "night",
}

TIME_SLOT_TZ = "America/New_York"

TRACKMAN_URL = "https://trackman-fm.apps.wuvt.vt.edu/"

TRACK_VALIDATE_CHECK_EXISTS = True
