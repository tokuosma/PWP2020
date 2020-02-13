import os
import random
import tempfile

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError



from climatecook import create_app, db
from climatecook.models import Rating, Recipe, RecipeCategory

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
    """
    Add valid recipe
    """
    recipe = Recipe(
        name="donkey-recipe"
    )
    with app_handle.app_context():
        db.session.add(recipe)
        db.session.commit()
        assert Recipe.query.count() == 1


def test_recipe_create_with_category(app_handle):
    """
    Create recipe with category
    """
    recipe_id = random.randint(1, 10000000)
    recipe_category_id = random.randint(1, 10000000)

    recipe_category = RecipeCategory(
        id=recipe_category_id,
        name="donkeyfood"
    )

    recipe = Recipe(
        id=recipe_id,
        name="donkey-recipe",
        recipe_category_id=recipe_category.id
    )

    with app_handle.app_context():
        db.session.add(recipe_category)
        db.session.add(recipe)
        db.session.commit()
        recipe = Recipe.query.filter_by(id=recipe_id).first()
        recipe_category = RecipeCategory.query.filter_by(id=recipe_category_id).first()
        assert recipe.recipe_category.id == recipe_category_id
        assert recipe_category.recipes[0].id == recipe.id


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
    Try adding a recipe with empty name
    """
    recipe = Recipe(
        name="",
    )
    with app_handle.app_context():
        db.session.add(recipe)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_recipe_category_create(app_handle):
    """
    Add valid recipe category
    """
    recipe_category = RecipeCategory(
        name="donkeyfood"
    )
    with app_handle.app_context():
        db.session.add(recipe_category)
        db.session.commit()
        assert RecipeCategory.query.count() == 1


def test_rating_create(app_handle):
    """
    Add valid rating
    """
    recipe_id = random.randint(1, 10000000)
    rating_id = random.randint(1, 10000000)
    recipe = Recipe(
        id=recipe_id,
        name="donkey_recipe"
    )
    rating = Rating(
        id=rating_id,
        recipe_id=recipe_id,
        rating=5,
        comment="this is donkeyfood!"
    )

    with app_handle.app_context():
        db.session.add(recipe)
        db.session.add(rating)
        db.session.commit()
        assert Rating.query.count() == 1
        rating = Rating.query.filter_by(id=rating_id).first()
        assert rating.recipe.id == recipe_id


def test_rating_create_invalid_recipe(app_handle):
    """
    Try to add rating with invalid recipe id
    """
    recipe_id = random.randint(1, 10000000)
    rating_id = random.randint(1, 10000000)
    
    rating = Rating(
        id=rating_id,
        recipe_id=recipe_id,
        rating=5,
        comment="this is donkeyfood!"
    )

    with app_handle.app_context():
        db.session.add(rating)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_rating_create_with_invalid_rating(app_handle):
    """
    Try to add rating with invalid rating
    """
    recipe_id = random.randint(1, 10000000)
    rating_id = random.randint(1, 10000000)
    recipe = Recipe(
        id=recipe_id,
        name="donkey_recipe"
    )
    rating = Rating(
        id=rating_id,
        recipe_id=recipe_id,
        rating=0,
        comment="this is donkeyfood!"
    )

    with app_handle.app_context():
        db.session.add(recipe)
        db.session.add(rating)
        with pytest.raises(IntegrityError):
            db.session.commit()
