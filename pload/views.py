import os.path
from flask import Blueprint, current_app, flash, redirect, render_template, \
        url_for
from paramiko.client import SSHClient
from .forms import PlaylistForm


bp = Blueprint('pload', __name__)


@bp.route('/', methods=['GET', 'POST'])
def upload():
    form = PlaylistForm()
    form.slot.choices = list(current_app.config['TIME_SLOTS'].items())

    if form.validate_on_submit():
        f = form.playlist.data

        client = SSHClient()
        client.load_system_host_keys(current_app.config['SFTP_KNOWN_HOSTS'])
        client.connect(
            current_app.config['SFTP_SERVER'],
            port=current_app.config.get('SFTP_PORT', 22),
            username=current_app.config.get('SFTP_USERNAME'),
            key_filename=current_app.config['SFTP_KEY_FILE'])
        sftp = client.open_sftp()

        # A note on the filename: yes, there is no sanitization, since
        # filenames are generated entirely from the configuration
        # If you accept user input here, you need to use werkzeug's
        # secure_filename function
        sftp.putfo(
            f,
            os.path.join(
                current_app.config['SFTP_DEST_PATH'],
                '{0}.m3u'.format(form.slot.data))
        )

        flash("The playlist has been uploaded.")
        return redirect(url_for('.upload'))

    return render_template('upload.html', form=form)
