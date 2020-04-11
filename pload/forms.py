import datetime
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import validators, ValidationError
from wtforms.fields import BooleanField, DateField, SelectField, TimeField
from wtforms.widgets import FileInput, Select
from wtforms.widgets.html5 import DateInput, TimeInput
from .view_utils import get_slot_tz


class BootstrapWidgetMixin(object):
    def __call__(self, field, **kwargs):
        existing_class = kwargs.pop("class", "") or kwargs.pop("class_", "")
        classes = set(existing_class.split())
        classes.add("form-control")
        if field.errors:
            classes.add("is-invalid")
        kwargs["class"] = " ".join(classes)
        return super().__call__(field, **kwargs)


class BootstrapDateInput(BootstrapWidgetMixin, DateInput):
    pass


class BootstrapTimeInput(BootstrapWidgetMixin, TimeInput):
    pass


class BootstrapFileInput(BootstrapWidgetMixin, FileInput):
    pass


class BootstrapSelect(BootstrapWidgetMixin, Select):
    pass


class PlaylistForm(FlaskForm):
    date = DateField(
        "Date", validators=[validators.InputRequired()], widget=BootstrapDateInput()
    )
    slot = SelectField(
        "Time Slot", validators=[validators.required()], widget=BootstrapSelect()
    )
    playlist = FileField(
        "Playlist File",
        validators=[
            FileRequired(),
            FileAllowed(["m3u"], "Only .m3u files may be uploaded."),
        ],
        widget=BootstrapFileInput(),
    )
    overwrite = BooleanField("Overwrite the existing playlist (if one exists)")

    def validate_date(self, field):
        if field.data < datetime.datetime.now(get_slot_tz()).date():
            raise ValidationError("The date cannot be in the past.")


class PrerecordedPlaylistForm(FlaskForm):
    date = DateField(
        "Date", validators=[validators.InputRequired()], widget=BootstrapDateInput()
    )
    time_start = TimeField(
        "Start Time",
        validators=[validators.InputRequired()],
        widget=BootstrapTimeInput(),
    )
    time_end = TimeField(
        "End Time", validators=[validators.InputRequired()], widget=BootstrapTimeInput()
    )
    playlist = FileField(
        "Playlist File",
        validators=[
            FileRequired(),
            FileAllowed(["m3u"], "Only .m3u files may be uploaded."),
        ],
        widget=BootstrapFileInput(),
    )
    overwrite = BooleanField("Overwrite the existing playlist (if one exists)")
    dj_id = SelectField("DJ", choices=[("1", "Automation")], widget=BootstrapSelect())

    def validate_date(self, field):
        if field.data < datetime.datetime.now(get_slot_tz()).date():
            raise ValidationError("The date cannot be in the past.")
