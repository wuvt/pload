from dateutil.tz import gettz, UTC
from flask import current_app


def localize_datetime(fromtime):
    slot_tz = gettz(current_app.config["TIME_SLOT_TZ"])
    return fromtime.replace(tzinfo=UTC).astimezone(slot_tz)


def format_datetime(value, format=None):
    value = localize_datetime(value)
    return value.strftime(format or "%Y-%m-%d %H:%M:%S %z")
