PLOAD_NAME = "Playlist Loader"
PROXY_FIX_NUM_PROXIES = 1

TIME_SLOTS = {
    "early": "Overnight (00:00-06:00)",
    "morning": "Early Morning (06:00-09:00)",
    "noon": "Morning to Midday (09:00-14:00)",
    "afternoon": "Afternoon (14:00-17:00)",
    "jazz": "Rush Hour Jazz (17:00-19:00)",
    "night": "Evening (19:00-00:00)",
}

PRERECORDED_TIME_SLOTS = [
    ('00:00', '02:00'),
    ('02:00', '04:00'),
    ('04:00', '07:00'),
    ('07:00', '09:00'),
    ('09:00', '11:00'),
    ('11:00', '12:00'),
    ('12:00', '14:00'),
    ('14:00', '17:00'),
    ('17:00', '19:00'),
    ('19:00', '21:00'),
    ('21:00', '00:00'),
]

TIME_SLOTS_BY_HOUR = {
    0: "early",
    6: "morning",
    14: "noon",
    17: "jazz",
    19: "night",
}

TRACKMAN_URL = "https://trackman-fm.apps.wuvt.vt.edu/"
