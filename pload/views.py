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
        .outerjoin(tracks_sq, tracks_sq.c.playlist_id == Playlist.id)
        .filter(
            Playlist.timeslot_end >= datetime.datetime.utcnow(),
            Playlist.approved != None,
        )
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
                "track_count": track_count or 0,
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


@bp.route("/playlists/edit/<int:playlist_id>", methods=["DELETE"])
def delete_playlist(playlist_id):
    playlist = Playlist.query.get_or_404(playlist_id)

    # Make sure no tracks in the playlist have been played yet
    for track in playlist.tracks.all():
        if track.played:
            return jsonify(
                {
                    "success": False,
                    "message": "One or more tracks in the playlist have already been played.",
                }
            )

    # No tracks have been played, so mark the playlist as not approved
    # We do this instead of deleting to enable restoration of deleted playlists
    # if necessary
    playlist.approved = None
    db.session.commit()
    return jsonify({"success": True,})


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
            db.or_(
                # The new playlist is either exactly at the same time as an
                # existing playlist or there's an existing playlist entirely
                # inside the same time slot
                db.and_(
                    # An existing playlist starts after (inclusive) we do
                    Playlist.timeslot_start >= timeslot_start,
                    # AND that playlist ends before (inclusive) we do
                    Playlist.timeslot_end <= timeslot_end,
                ),
                # The new playlist will start before an existing playlist ends
                db.and_(
                    # An existing playlist starts before (inclusive) we do
                    Playlist.timeslot_start <= timeslot_start,
                    # AND that playlist ends after we start
                    Playlist.timeslot_end > timeslot_start,
                ),
                # The new playlist will end after an existing playlist starts
                db.and_(
                    # An existing playlist starts after (inclusive) we do
                    Playlist.timeslot_start >= timeslot_start,
                    # AND that playlist starts before we end
                    Playlist.timeslot_start < timeslot_end,
                ),
            ),
            Playlist.queue == queue,
            Playlist.approved != None,
        )

        # check for existing playlists in the same slot
        if existing_playlists.count() > 0:
            flash(
                """\
A playlist already exists that overlaps the date and time slot you selected.
You'll need to either delete the existing playlist or pick a different slot."""
            )
        else:
            playlist = Playlist(
                timeslot_start, timeslot_end, form.dj_id.data, form.queue.data
            )
            playlist.approved = datetime.datetime.utcnow()
            db.session.add(playlist)

            db.session.commit()

            return render_template("edit_playlist.html", playlist=playlist, tracks=[],)

    return render_template("create_playlist.html", form=form)
