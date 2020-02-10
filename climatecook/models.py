import click
from flask.cli import with_appcontext

from climatecook import db


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(64))
