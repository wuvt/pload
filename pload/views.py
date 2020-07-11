from collections import defaultdict
from dateutil.tz import gettz, UTC
import datetime
from flask import (
    abort,
    Blueprint,
    current_app,
    flash,
    jsonify,
    render_template,
    request,
)
from .db import db
from .exceptions import PlaylistValidationException
from .filters import localize_datetime
from .forms import CreatePlaylistForm
from .models import Playlist, QueuedTrack
from .view_utils import process_url, get_dj_list


bp = Blueprint("pload", __name__)


@bp.route("/")
def index():
    djs = get_dj_list()
    dj_map = {int(dj["id"]): dj["airname"] for dj in djs}
    dj_map[1] = "Automation"

    tracks_sq = (
        QueuedTrack.query.with_entities(
            QueuedTrack.playlist_id,
            db.func.count(QueuedTrack.playlist_id).label("count"),
        )
        .group_by(QueuedTrack.playlist_id)
        .subquery()
    )

    playlists = (
        Playlist.query.with_entities(
            Playlist.id,
            Playlist.timeslot_start,
            Playlist.timeslot_end,
            Playlist.queue,
            Playlist.dj_id,
            tracks_sq.c.count,
        )
        .join(tracks_sq, tracks_sq.c.playlist_id == Playlist.id)
        .filter(Playlist.timeslot_end >= datetime.datetime.utcnow(),)
        .order_by(Playlist.timeslot_start)
        .all()
    )

    # localize dates and then group by them
    unplayed = defaultdict(list)
    for (
        playlist_id,
        timeslot_start,
        timeslot_end,
        queue,
        dj_id,
        track_count,
    ) in playlists:
        if dj_id is None:
            dj_id = 1

        timeslot_start = localize_datetime(timeslot_start)
        timeslot_end = localize_datetime(timeslot_end)

        unplayed[timeslot_start.date()].append(
            {
                "id": playlist_id,
                "timeslot_start": timeslot_start,
                "timeslot_end": timeslot_end,
                "queue": queue,
                "track_count": track_count,
                "dj_id": dj_id,
                "dj": dj_map.get(dj_id, "[DJ #{0}]".format(dj_id)),
            }
        )

    return render_template("index.html", playlist_groups=unplayed)


@bp.route("/playlists/edit/<int:playlist_id>", methods=["GET", "POST"])
def edit_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)

    if request.method == "POST":
        if request.headers.get("X-Requested-With") is None:
            abort(400)

        existing_tracks = QueuedTrack.query.filter(
            QueuedTrack.playlist_id == playlist_id,
        )
        if existing_tracks.filter(QueuedTrack.played == True).count() > 0:
            return jsonify(
                {
                    "success": False,
                    "results": [],
                    "message": "One or more tracks have already been played.",
                }
            )

        for track in existing_tracks.all():
            db.session.delete(track)

        index = 0
        ok = True
        results = []

        for url in request.form.getlist("tracks[]"):
            index += 1

            try:
                url = process_url(url)
            except PlaylistValidationException:
                ok = False
                results.append(
                    {"index": index, "url": url, "status": "Error",}
                )
                continue
            else:
                results.append(
                    {"index": index, "url": url, "status": "OK",}
                )

            track = QueuedTrack(url, playlist.id)
            db.session.add(track)

        if ok:
            db.session.commit()
            return jsonify({"success": True,})
        else:
            db.session.rollback()
            return jsonify(
                {
                    "success": False,
                    "results": results,
                    "message": "One or more tracks failed to pass validation.",
                }
            )

    tracks = playlist.tracks.order_by(QueuedTrack.id)

    # Make sure no tracks in the playlist have been played yet
    for track in tracks.all():
        if track.played:
            return render_template(
                "playlist_being_played.html",
                playlist=playlist,
                tracks=[t.serialize() for t in tracks.all()],
            )

    return render_template(
        "edit_playlist.html",
        playlist=playlist,
        tracks=[t.serialize() for t in tracks.all()],
    )


@bp.route("/playlists/new", methods=["GET", "POST"])
def create_playlist():
    form = CreatePlaylistForm()

    # get list of DJs from Trackman and add
    djs = get_dj_list()
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

        if timeslot_end <= timeslot_start:
            timeslot_end += datetime.timedelta(days=1)

        # convert times to UTC for querying the database
        timeslot_start = timeslot_start.astimezone(UTC)
        timeslot_end = timeslot_end.astimezone(UTC)

        if len(form.queue.data) <= 0:
            queue = None
        else:
            queue = form.queue.data

        existing_playlists = Playlist.query.filter(
            Playlist.timeslot_start >= timeslot_start,
            Playlist.timeslot_end <= timeslot_end,
            Playlist.queue == queue,
        )

        # check if overwriting is necessary
        if existing_playlists.count() > 0 and not form.overwrite.data:
            flash(
                """\
A playlist already exists for that date and time slot. You'll need to either
overwrite the existing playlist, or pick another date or time slot."""
            )
        else:
            # We're overwriting, so delete all tracks for all matching
            # playlists
            for playlist in existing_playlists.all():
                for track in playlist.tracks:
                    db.session.delete(track)
                db.session.delete(playlist)

            playlist = Playlist(
                timeslot_start, timeslot_end, form.dj_id.data, form.queue.data
            )
            db.session.add(playlist)

            db.session.commit()

            return render_template("edit_playlist.html", playlist=playlist, tracks=[],)

    return render_template("create_playlist.html", form=form)
