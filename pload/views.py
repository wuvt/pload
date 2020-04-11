from dateutil.tz import gettz, UTC
import datetime
import requests
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from .db import db
from .exceptions import PlaylistExistsException, PlaylistValidationException
from .forms import PlaylistForm, PrerecordedPlaylistForm
from .models import QueuedTrack
from .view_utils import validate_url


bp = Blueprint("pload", __name__)


def process_playlist_upload(
    timeslot_start,
    timeslot_end,
    playlist_fo,
    queue=None,
    line_wrapper=None,
    overwrite=False,
    skip_validate=False,
):
    existing_tracks = QueuedTrack.query.filter(
        QueuedTrack.timeslot_start >= timeslot_start,
        QueuedTrack.timeslot_end <= timeslot_end,
        QueuedTrack.queue == queue,
    )
    if existing_tracks.count() > 0 and not overwrite:
        raise PlaylistExistsException()
    elif overwrite:
        for track in existing_tracks.all():
            db.session.delete(track)
        db.session.commit()

    for line in playlist_fo:
        url = line.strip().decode("utf-8")
        if url.startswith("#"):
            continue
        if not skip_validate and not validate_url(url):
            raise PlaylistValidationException()
        if line_wrapper is not None:
            url = line_wrapper(url)
        track = QueuedTrack(url, timeslot_start, timeslot_end, queue)
        db.session.add(track)

    db.session.commit()


@bp.route("/", methods=["GET", "POST"])
def upload():
    form = PlaylistForm()
    form.slot.choices = list(current_app.config["TIME_SLOTS"].items())

    if form.validate_on_submit():
        slots = sorted(
            current_app.config["TIME_SLOTS_BY_HOUR"].items(), key=lambda x: x[0]
        )
        slot_tz = gettz(current_app.config["TIME_SLOT_TZ"])

        timeslot_start = datetime.datetime(
            form.date.data.year,
            form.date.data.month,
            form.date.data.day,
            tzinfo=slot_tz,
        )
        timeslot_end = datetime.datetime(
            form.date.data.year,
            form.date.data.month,
            form.date.data.day,
            tzinfo=slot_tz,
        )

        for i in range(len(slots)):
            if slots[i][1] == form.slot.data:
                timeslot_start = timeslot_start.replace(hour=slots[i][0])
                if i + 1 < len(slots):
                    timeslot_end = timeslot_start.replace(hour=slots[i + 1][0])
                else:
                    timeslot_end = timeslot_start.replace(hour=slots[0][0])
                    timeslot_end += datetime.timedelta(days=1)
                break

        # convert times to UTC for querying the database
        timeslot_start = timeslot_start.astimezone(UTC)
        timeslot_end = timeslot_end.astimezone(UTC)

        try:
            process_playlist_upload(
                timeslot_start,
                timeslot_end,
                form.playlist.data,
                overwrite=form.overwrite.data,
            )
        except PlaylistExistsException:
            flash(
                """\
A playlist already exists for that date and time slot. You'll need to either
overwrite the existing playlist, or pick another date or time slot."""
            )
        except PlaylistValidationException:
            flash("The playlist you uploaded failed to validate.")
        else:
            current_app.logger.warning(
                "{user} uploaded a playlist that covers {start} until {end}".format(
                    user=request.headers.get("X-Forwarded-User"),
                    start=timeslot_start,
                    end=timeslot_end,
                )
            )

            flash("The playlist has been uploaded.")
            return redirect(url_for(".upload"))

    return render_template("upload.html", form=form)


@bp.route("/prerecorded", methods=["GET", "POST"])
def upload_prerecorded():
    form = PrerecordedPlaylistForm()

    # get list of DJs from Trackman and add
    r = requests.get(
        "{0}/api/playlists/dj".format(current_app.config["TRACKMAN_URL"].rstrip("/"))
    )
    if r.status_code == 200:
        data = r.json()
        djs = data.get("djs", [])
        form.dj_id.choices += [(str(dj["id"]), dj["airname"]) for dj in djs]

    if form.validate_on_submit():
        slot_tz = gettz(current_app.config["TIME_SLOT_TZ"])

        timeslot_start = datetime.datetime(
            form.date.data.year,
            form.date.data.month,
            form.date.data.day,
            form.time_start.data.hour,
            form.time_start.data.minute,
            tzinfo=slot_tz,
        )
        timeslot_end = datetime.datetime(
            form.date.data.year,
            form.date.data.month,
            form.date.data.day,
            form.time_end.data.hour,
            form.time_end.data.minute,
            tzinfo=slot_tz,
        )

        # convert times to UTC for querying the database
        timeslot_start = timeslot_start.astimezone(UTC)
        timeslot_end = timeslot_end.astimezone(UTC)

        def process_line(url):
            return "annotate:trackman_dj_id={dj_id:d}:{url}".format(
                dj_id=int(form.dj_id.data), url=url
            )

        try:
            process_playlist_upload(
                timeslot_start,
                timeslot_end,
                form.playlist.data,
                queue="prerecorded",
                line_wrapper=process_line,
                overwrite=form.overwrite.data,
            )
        except PlaylistExistsException:
            flash(
                """\
A playlist already exists for that date and time slot. You'll need to either
overwrite the existing playlist, or pick another date or time slot."""
            )
        except PlaylistValidationException:
            flash("The playlist you uploaded failed to validate.")
        else:
            current_app.logger.warning(
                "{user} uploaded a prerecorded playlist that covers {start} until {end}".format(
                    user=request.headers.get("X-Forwarded-User"),
                    start=timeslot_start,
                    end=timeslot_end,
                )
            )

            flash("The playlist has been uploaded.")
            return redirect(url_for(".upload_prerecorded"))

    return render_template("upload_prerecorded.html", form=form)
