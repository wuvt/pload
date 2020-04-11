from collections import defaultdict
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
    # if a track fails, ok will be set to False and no future db.session.commit
    ok = True
    results = []
    index = 0

    # db.session.begin_nested()

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

    for line in playlist_fo:
        url = line.strip().decode("utf-8")
        if url.startswith("#"):
            continue

        index += 1

        if not skip_validate and not validate_url(url):
            ok = False
            results.append(
                {"index": index, "url": url, "status": "Error",}
            )
            continue
        else:
            results.append(
                {"index": index, "url": url, "status": "OK",}
            )

        if line_wrapper is not None:
            url = line_wrapper(url)

        track = QueuedTrack(url, timeslot_start, timeslot_end, queue)
        db.session.add(track)

    if ok:
        db.session.commit()
    else:
        db.session.rollback()

    return ok, results


@bp.route("/")
def index():
    slot_tz = gettz(current_app.config["TIME_SLOT_TZ"])
    unplayed_tracks = (
        QueuedTrack.query
        .options(db.load_only('timeslot_start', 'timeslot_end', 'queue'))
        .with_entities(QueuedTrack.timeslot_start, QueuedTrack.timeslot_end, QueuedTrack.queue)
        .filter(QueuedTrack.played == False)
        .group_by(QueuedTrack.timeslot_start, QueuedTrack.timeslot_end, QueuedTrack.queue)
        .order_by(QueuedTrack.timeslot_start)
        .all()
    )

    # localize dates and then group by them
    unplayed = defaultdict(list)
    for timeslot_start, timeslot_end, queue in unplayed_tracks:
        timeslot_start = timeslot_start.replace(tzinfo=UTC).astimezone(slot_tz)
        timeslot_end = timeslot_end.replace(tzinfo=UTC).astimezone(slot_tz)
        unplayed[timeslot_start.date()].append({
            'timeslot_start': timeslot_start,
            'timeslot_end': timeslot_end,
            'queue': queue,
        })

    return render_template("index.html", unplayed_tracks=unplayed)


@bp.route("/upload/playlist", methods=["GET", "POST"])
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
            ok, results = process_playlist_upload(
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
        else:
            if ok:
                current_app.logger.warning(
                    "{user} uploaded a playlist that covers {start} until {end}".format(
                        user=request.headers.get("X-Forwarded-User"),
                        start=timeslot_start,
                        end=timeslot_end,
                    )
                )

            return render_template(
                "upload_report.html",
                prerecorded=False,
                timeslot_start=timeslot_start,
                timeslot_end=timeslot_end,
                ok=ok,
                results=results,
            )

    return render_template("upload.html", form=form)


@bp.route("/upload/prerecorded", methods=["GET", "POST"])
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
            ok, results = process_playlist_upload(
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
        else:
            if ok:
                current_app.logger.warning(
                    "{user} uploaded a prerecorded playlist that covers {start} until {end}".format(
                        user=request.headers.get("X-Forwarded-User"),
                        start=timeslot_start,
                        end=timeslot_end,
                    )
                )

            return render_template(
                "upload_report.html",
                prerecorded=True,
                timeslot_start=timeslot_start,
                timeslot_end=timeslot_end,
                ok=ok,
                results=results,
            )

    return render_template("upload_prerecorded.html", form=form)
