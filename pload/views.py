import os.path
from flask import Blueprint, abort, current_app, flash, redirect, \
        render_template, url_for
from paramiko.client import SSHClient
from werkzeug.utils import secure_filename
from .forms import PlaylistForm
from .lib import sftp_exists


bp = Blueprint('pload', __name__)


@bp.route('/', methods=['GET', 'POST'])
def upload():
    form = PlaylistForm()
    form.slot.choices = list(current_app.config['TIME_SLOTS'].items())

    if form.validate_on_submit():
        filename = secure_filename('{0}-{1}.m3u'.format(
            form.date.data.strftime('%Y%m%d'), form.slot.data))

        # in some cases, secure_filename can return an empty string, so abort
        # if that happened
        if len(filename) <= 0:
            abort(400)

        dest_path = os.path.join(current_app.config['SFTP_DEST_PATH'],
                                 filename)

        client = SSHClient()
        client.load_system_host_keys(current_app.config['SFTP_KNOWN_HOSTS'])
        client.connect(
            current_app.config['SFTP_SERVER'],
            port=current_app.config.get('SFTP_PORT', 22),
            username=current_app.config.get('SFTP_USERNAME'),
            key_filename=current_app.config['SFTP_KEY_FILE'])
        sftp = client.open_sftp()

        if not form.overwrite.data and sftp_exists(sftp, dest_path):
            flash("A playlist already exists for that date and time slot. "
                  "You'll need to either overwrite the existing playlist, or "
                  "pick another date or time slot.")
        else:
            sftp.putfo(form.playlist.data, dest_path)

            flash("The playlist has been uploaded.")
            return redirect(url_for('.upload'))

    return render_template('upload.html', form=form)
