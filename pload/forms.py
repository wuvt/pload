from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import validators
from wtforms.fields import BooleanField, DateField, SelectField
from wtforms.widgets import FileInput, Select
from wtforms.widgets.html5 import DateInput


class BootstrapWidgetMixin(object):
    def __call__(self, field, **kwargs):
        existing_class = kwargs.pop('class', '') or kwargs.pop('class_', '')
        classes = set(existing_class.split())
        classes.add('form-control')
        if field.errors:
            classes.add('is-invalid')
        kwargs['class'] = ' '.join(classes)
        return super().__call__(field, **kwargs)


class BootstrapDateInput(BootstrapWidgetMixin, DateInput):
    pass


class BootstrapFileInput(BootstrapWidgetMixin, FileInput):
    pass


class BootstrapSelect(BootstrapWidgetMixin, Select):
    pass


class PlaylistForm(FlaskForm):
    date = DateField(
        "Date",
        validators=[validators.InputRequired()],
        widget=BootstrapDateInput())
    slot = SelectField(
        "Time Slot",
        validators=[validators.required()],
        widget=BootstrapSelect())
    playlist = FileField(
        "Playlist File",
        validators=[
            FileRequired(),
            FileAllowed(['m3u'], "Only .m3u files may be uploaded."),
        ],
        widget=BootstrapFileInput())
    overwrite = BooleanField("Overwrite the existing playlist (if one exists)")
