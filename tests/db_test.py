import os
import random
import tempfile

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError



from climatecook import create_app, db
from climatecook.models import Recipe, RecipeCategory

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

@pytest.fixture
def app_handle():
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


def test_recipe_create(app_handle):
    recipe = Recipe(
        name="donkey-recipe"
    )
    with app_handle.app_context():
        db.session.add(recipe)
        db.session.commit()
        assert Recipe.query.count() == 1


def test_recipe_create_with_invalid_category(app_handle):
    """
    Try adding a recipe with a non-existing category
    """
    fake_id = random.randint(1, 10000000)
    recipe = Recipe(
        name="donkey-recipe",
        recipe_category_id=fake_id
    )
    with app_handle.app_context():
        db.session.add(recipe)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_recipe_create_with_invalid_name(app_handle):
    """
    Try adding a recipe with a non-existing category
    """
    recipe = Recipe(
        name="",
    )
    with app_handle.app_context():
        db.session.add(recipe)
        with pytest.raises(IntegrityError):
            db.session.commit()
            

def test_create_recipe_category(app_handle):

    pass
