import os.path
import io
import requests
from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from paramiko.client import SSHClient
from werkzeug.utils import secure_filename
from .forms import PlaylistForm, PrerecordedPlaylistForm
from .lib import sftp_exists


bp = Blueprint("pload", __name__)


class PlaylistExistsException(Exception):
    pass


def process_playlist_upload(
    filename, upload_fo, overwrite=False, line_wrapper=None, dest_prefix=""
):
    if len(current_app.config.get("SFTP_DEST_PATH", "")) > 0:
        dest_path = os.path.join(
            current_app.config["SFTP_DEST_PATH"], dest_prefix, filename
        )

        client = SSHClient()
        client.load_system_host_keys(current_app.config["SFTP_KNOWN_HOSTS"])
        client.connect(
            current_app.config["SFTP_SERVER"],
            port=current_app.config.get("SFTP_PORT", 22),
            username=current_app.config.get("SFTP_USERNAME"),
            key_filename=current_app.config["SFTP_KEY_FILE"],
        )
        sftp = client.open_sftp()

        if not overwrite and sftp_exists(sftp, dest_path):
            raise PlaylistExistsException()
    else:
        dest_path = os.path.join(current_app.config["DEST_PATH"], dest_prefix, filename)
        sftp = None

        if not overwrite and os.path.exists(dest_path):
            raise PlaylistExistsException()

    if line_wrapper is not None:
        if sftp is None:
            playlist_fo = open(dest_path)
        else:
            # create an in-memory playlist buffer
            playlist_fo = io.StringIO()

        for line in upload_fo:
            playlist_fo.write(line_wrapper(line.strip().decode("utf-8")) + "\n")

        if sftp is not None:
            playlist_fo.seek(0)
            sftp.putfo(playlist_fo, dest_path)

        playlist_fo.close()
    else:
        if sftp is not None:
            sftp.putfo(upload_fo, dest_path)
        else:
            upload_fo.save(dest_path)


@bp.route("/", methods=["GET", "POST"])
def upload():
    form = PlaylistForm()
    form.slot.choices = list(current_app.config["TIME_SLOTS"].items())

    if form.validate_on_submit():
        filename = secure_filename(
            "{0}-{1}.m3u".format(form.date.data.strftime("%Y%m%d"), form.slot.data)
        )

        # in some cases, secure_filename can return an empty string, so abort
        # if that happened
        if len(filename) <= 0:
            abort(400)

        try:
            process_playlist_upload(
                filename, form.playlist.data, overwrite=form.overwrite.data
            )
        except PlaylistExistsException:
            flash(
                """\
A playlist already exists for that date and time slot. You'll need to either
overwrite the existing playlist, or pick another date or time slot."""
            )
        else:
            current_app.logger.warning(
                "{user} uploaded the playlist {filename}".format(
                    user=request.headers.get("X-Forwarded-User"), filename=filename
                )
            )

            flash("The playlist has been uploaded.")
            return redirect(url_for(".upload"))

    return render_template("upload.html", form=form)


@bp.route("/prerecorded", methods=["GET", "POST"])
def upload_prerecorded():
    form = PrerecordedPlaylistForm()
    # FIXME: we need more slots for prerecorded stuff
    form.slot.choices = list(current_app.config["TIME_SLOTS"].items())

    # get list of DJs from Trackman and add
    r = requests.get(
        "{0}/api/playlists/dj".format(current_app.config["TRACKMAN_URL"].rstrip("/"))
    )
    if r.status_code == 200:
        data = r.json()
        djs = data.get("djs", [])
        form.dj_id.choices += [(str(dj["id"]), dj["airname"]) for dj in djs]

    if form.validate_on_submit():
        filename = secure_filename(
            "{0}-{1}.m3u".format(form.date.data.strftime("%Y%m%d"), form.slot.data)
        )

        # in some cases, secure_filename can return an empty string, so abort
        # if that happened
        if len(filename) <= 0:
            abort(400)

        def process_line(url):
            return "annotate:trackman_dj_id={dj_id:d}:{url}".format(
                dj_id=int(form.dj_id.data), url=url
            )

        try:
            process_playlist_upload(
                filename,
                form.playlist.data,
                overwrite=form.overwrite.data,
                wrapper=process_line,
                dest_prefix="prerercorded",
            )
        except PlaylistExistsException:
            flash(
                """\
A playlist already exists for that date and time slot. You'll need to either
overwrite the existing playlist, or pick another date or time slot."""
            )
        else:
            current_app.logger.warning(
                "{user} uploaded the playlist {filename}".format(
                    user=request.headers.get("X-Forwarded-User"), filename=filename
                )
            )

            flash("The playlist has been uploaded.")
            return redirect(url_for(".upload_prerecorded"))

    return render_template("upload_prerecorded.html", form=form)
