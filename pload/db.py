from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_db():
    from . import models  # noqa: F401

    db.create_all()
