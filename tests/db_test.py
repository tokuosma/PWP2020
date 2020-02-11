import os
import tempfile

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy import event


from climatecook import create_app, db
from climatecook.models import Recipe, RecipeCategory

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def app():
    db_fd, db_fname = tempfile.mkstemp()

    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }

    app = create_app(config)

    with app.app_context():
        db.create_all()

    yield app

    os.close(db_fd)
    os.unlink(db_fname)


def test_create_recipe(app):
    recipe = Recipe(
        name="donkey-recipe"
    )
    db.session.add(recipe)
    db.session.commit()
    assert Recipe.query.count() == 1
