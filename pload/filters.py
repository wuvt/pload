from dateutil.tz import gettz, UTC
from flask import current_app
from .view_utils import process_url_for_display


def localize_datetime(fromtime):
    slot_tz = gettz(current_app.config["TIME_SLOT_TZ"])
    return fromtime.replace(tzinfo=UTC).astimezone(slot_tz)


def format_datetime(value, format=None, localize=True):
    if localize:
        value = localize_datetime(value)
    return value.strftime(format or "%Y-%m-%d %H:%M:%S %z")


def tztoutc(fromtime):
    return fromtime.astimezone(UTC)


def public_url(url):
    return process_url_for_display(url)
