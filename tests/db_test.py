import os
import random
import tempfile

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError

from climatecook import create_app, db
from climatecook.models import Recipe
# from climatecook.models import Rating, RecipeCategory
from climatecook.models import Ingredient, FoodItem, FoodItemEquivalent
# from climatecook.models import FoodItemCategory


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


# def test_recipe_create_with_category(app_handle):
#     """
#     Create recipe with category
#     """
#     recipe_id = random.randint(1, 10000000)
#     recipe_category_id = random.randint(1, 10000000)

#     recipe_category = RecipeCategory(
#         id=recipe_category_id,
#         name="donkeyfood"
#     )

#     recipe = Recipe(
#         id=recipe_id,
#         name="donkey-recipe",
#         recipe_category_id=recipe_category.id
#     )

#     with app_handle.app_context():
#         db.session.add(recipe_category)
#         db.session.add(recipe)
#         db.session.commit()
#         recipe = Recipe.query.filter_by(id=recipe_id).first()
#         recipe_category = RecipeCategory.query.filter_by(id=recipe_category_id).first()
#         assert recipe.recipe_category.id == recipe_category_id
#         assert recipe_category.recipes[0].id == recipe.id


# def test_recipe_create_with_invalid_category(app_handle):
#     """
#     Try adding a recipe with a non-existing category
#     """
#     fake_id = random.randint(1, 10000000)
#     recipe = Recipe(
#         name="donkey-recipe",
#         recipe_category_id=fake_id
#     )
#     with app_handle.app_context():
#         db.session.add(recipe)
#         with pytest.raises(IntegrityError):
#             db.session.commit()


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


# def test_recipe_category_create(app_handle):
#     """
#     Add valid recipe category
#     """
#     recipe_category = RecipeCategory(
#         name="donkeyfood"
#     )
#     with app_handle.app_context():
#         db.session.add(recipe_category)
#         db.session.commit()
#         assert RecipeCategory.query.count() == 1


# def test_rating_create(app_handle):
#     """
#     Add valid rating
#     """
#     recipe_id = random.randint(1, 10000000)
#     rating_id = random.randint(1, 10000000)
#     recipe = Recipe(
#         id=recipe_id,
#         name="donkey_recipe"
#     )
#     rating = Rating(
#         id=rating_id,
#         recipe_id=recipe_id,
#         rating=5,
#         comment="this is donkeyfood!"
#     )

#     with app_handle.app_context():
#         db.session.add(recipe)
#         db.session.add(rating)
#         db.session.commit()
#         assert Rating.query.count() == 1
#         rating = Rating.query.filter_by(id=rating_id).first()
#         assert rating.recipe.id == recipe_id


# def test_rating_create_invalid_recipe(app_handle):
#     """
#     Try to add rating with invalid recipe id
#     """
#     recipe_id = random.randint(1, 10000000)
#     rating_id = random.randint(1, 10000000)

#     rating = Rating(
#         id=rating_id,
#         recipe_id=recipe_id,
#         rating=5,
#         comment="this is donkeyfood!"
#     )

#     with app_handle.app_context():
#         db.session.add(rating)
#         with pytest.raises(IntegrityError):
#             db.session.commit()


# def test_rating_create_with_invalid_rating(app_handle):
#     """
#     Try to add rating with invalid rating
#     """
#     recipe_id = random.randint(1, 10000000)
#     rating_id = random.randint(1, 10000000)
#     recipe = Recipe(
#         id=recipe_id,
#         name="donkey_recipe"
#     )
#     rating = Rating(
#         id=rating_id,
#         recipe_id=recipe_id,
#         rating=0,
#         comment="this is donkeyfood!"
#     )

#     with app_handle.app_context():
#         db.session.add(recipe)
#         db.session.add(rating)
#         with pytest.raises(IntegrityError):
#             db.session.commit()


def test_ingredient_create(app_handle):
    """
    Add valid ingredient
    """
    recipe_id = random.randint(1, 10000000)
    ingredient_id = random.randint(1, 10000000)
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    recipe = Recipe(
        id=recipe_id,
        name="donkey_recipe"
    )
    ingredient = Ingredient(
        id=ingredient_id,
        recipe_id=recipe_id,
        food_item_id=food_item_id,
        food_item_equivalent_id=food_item_equivalent_id,
        quantity=10.0
    )
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=100.0
    )
    fooditemequivalent = FoodItemEquivalent(
        id=food_item_equivalent_id,
        food_item_id=food_item_id,
        unit_type=10,
        conversion_factor=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(recipe)
        db.session.add(ingredient)
        db.session.add(fooditem)
        db.session.add(fooditemequivalent)
        # db.session.add(fooditemcategory)
        db.session.commit()
        assert Ingredient.query.count() == 1
        ingredient = Ingredient.query.filter_by(id=ingredient_id).first()
        assert ingredient.recipe.id == recipe_id
        assert ingredient.food_item.id == food_item_id
        assert ingredient.food_item_equivalent_id == food_item_equivalent_id


def test_ingredient_create_with_invalid_recipe(app_handle):
    """
    Try to add ingredient with invalid recipe id
    """
    recipe_id = random.randint(1, 10000000)
    ingredient_id = random.randint(1, 10000000)
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    ingredient = Ingredient(
        id=ingredient_id,
        recipe_id=recipe_id,
        food_item_id=food_item_id,
        food_item_equivalent_id=food_item_equivalent_id,
        quantity=10.0
    )
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=100.0
    )
    fooditemequivalent = FoodItemEquivalent(
        id=food_item_equivalent_id,
        food_item_id=food_item_id,
        unit_type=10,
        conversion_factor=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(ingredient)
        db.session.add(fooditem)
        db.session.add(fooditemequivalent)
        # db.session.add(fooditemcategory)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_ingredient_create_with_invalid_fooditem(app_handle):
    """
    Try to add ingredient with invalid fooditem id
    """
    recipe_id = random.randint(1, 10000000)
    ingredient_id = random.randint(1, 10000000)
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    recipe = Recipe(
        id=recipe_id,
        name="donkey_recipe"
    )
    ingredient = Ingredient(
        id=ingredient_id,
        recipe_id=recipe_id,
        food_item_id=food_item_id,
        food_item_equivalent_id=food_item_equivalent_id,
        quantity=10.0
    )
    fooditemequivalent = FoodItemEquivalent(
        id=food_item_equivalent_id,
        food_item_id=food_item_id,
        unit_type=10,
        conversion_factor=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(recipe)
        db.session.add(ingredient)
        db.session.add(fooditemequivalent)
        # db.session.add(fooditemcategory)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_ingredient_create_with_invalid_fooditemequivalent(app_handle):
    """
    Try to add ingredient with invalid fooditemequivalent id
    """
    recipe_id = random.randint(1, 10000000)
    ingredient_id = random.randint(1, 10000000)
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    recipe = Recipe(
        id=recipe_id,
        name="donkey_recipe"
    )
    ingredient = Ingredient(
        id=ingredient_id,
        recipe_id=recipe_id,
        food_item_id=food_item_id,
        food_item_equivalent_id=food_item_equivalent_id,
        quantity=10.0
    )
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(recipe)
        db.session.add(ingredient)
        db.session.add(fooditem)
        # db.session.add(fooditemcategory)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_ingredient_create_with_invalid_quantity(app_handle):
    """
    Try to add ingredient with invalid quantity
    """
    recipe_id = random.randint(1, 10000000)
    ingredient_id = random.randint(1, 10000000)
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    recipe = Recipe(
        id=recipe_id,
        name="donkey_recipe"
    )
    ingredient = Ingredient(
        id=ingredient_id,
        recipe_id=recipe_id,
        food_item_id=food_item_id,
        food_item_equivalent_id=food_item_equivalent_id,
        quantity=-5.5
    )
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=100.0
    )
    fooditemequivalent = FoodItemEquivalent(
        id=food_item_equivalent_id,
        food_item_id=food_item_id,
        unit_type=10,
        conversion_factor=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(recipe)
        db.session.add(ingredient)
        db.session.add(fooditem)
        db.session.add(fooditemequivalent)
        # db.session.add(fooditemcategory)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_fooditem_create(app_handle):
    """
    Add valid fooditem
    """
    food_item_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(fooditem)
        # db.session.add(fooditemcategory)
        db.session.commit()
        assert FoodItem.query.count() == 1
        fooditem = FoodItem.query.filter_by(id=food_item_id).first()
        # assert fooditem.food_item_category.id == food_item_category_id


# def test_fooditem_create_with_invalid_fooditemcategory(app_handle):
#     """
#     Try to add fooditem with invalid fooditemcategory id
#     """
#     food_item_id = random.randint(1, 10000000)
#     food_item_category_id = random.randint(1, 10000000)
#     fooditem = FoodItem(
#         id=food_item_id,
#         food_item_category_id=food_item_category_id,
#         name="donkey_salt",
#         emission_per_kg=100.0
#     )
#     with app_handle.app_context():
#         db.session.add(fooditem)
#         with pytest.raises(IntegrityError):
#             db.session.commit()


def test_fooditem_create_with_invalid_name(app_handle):
    """
    Try to add fooditem with empty name
    """
    food_item_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="",
        emission_per_kg=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(fooditem)
        # db.session.add(fooditemcategory)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_fooditem_create_with_invalid_emission(app_handle):
    """
    Try to add fooditem with negative emission per kg
    """
    food_item_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=-100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(fooditem)
        # db.session.add(fooditemcategory)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_fooditemequivalent_create(app_handle):
    """
    Add valid fooditemequivalent
    """
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=100.0
    )
    fooditemequivalent = FoodItemEquivalent(
        id=food_item_equivalent_id,
        food_item_id=food_item_id,
        unit_type=10,
        conversion_factor=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(fooditem)
        db.session.add(fooditemequivalent)
        # db.session.add(fooditemcategory)
        db.session.commit()
        assert FoodItem.query.count() == 1
        fooditem = FoodItem.query.filter_by(id=food_item_id).first()
        assert fooditem.food_item_equivalents[0].id == food_item_equivalent_id


def test_fooditemequivalent_create_with_invalid_fooditem(app_handle):
    """
    Try to add fooditemequivalent with invalid fooditem id
    """
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id = random.randint(1, 10000000)
    fooditemequivalent = FoodItemEquivalent(
        id=food_item_equivalent_id,
        food_item_id=food_item_id,
        unit_type=10,
        conversion_factor=100.0
    )
    with app_handle.app_context():
        db.session.add(fooditemequivalent)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_fooditemequivalent_create_with_invalid_unit(app_handle):
    """
    Try to add fooditemquivalent with invalid unittype
    """
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=100.0
    )
    fooditemequivalent = FoodItemEquivalent(
        id=food_item_equivalent_id,
        food_item_id=food_item_id,
        unit_type=-10,
        conversion_factor=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(fooditem)
        db.session.add(fooditemequivalent)
        # db.session.add(fooditemcategory)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_fooditemequivalent_create_with_duplicate_unittype(app_handle):
    """
    Try to add food item equivalent with duplicate food item type
    """
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id_1 = random.randint(1, 10000000)
    food_item_equivalent_id_2 = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=100.0
    )
    fooditemequivalent_1 = FoodItemEquivalent(
        id=food_item_equivalent_id_1,
        food_item_id=food_item_id,
        unit_type=10,
        conversion_factor=100.0
    )
    fooditemequivalent_2 = FoodItemEquivalent(
        id=food_item_equivalent_id_2,
        food_item_id=food_item_id,
        unit_type=10,
        conversion_factor=100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(fooditem)
        db.session.add(fooditemequivalent_1)
        db.session.add(fooditemequivalent_2)
        # db.session.add(fooditemcategory)
        with pytest.raises(IntegrityError):
            db.session.commit()


def test_fooditemequivalent_create_with_invalid_conversion(app_handle):
    """
    Try to add fooditemequivalent with invalid conversion factor
    """
    food_item_id = random.randint(1, 10000000)
    food_item_equivalent_id = random.randint(1, 10000000)
    # food_item_category_id = random.randint(1, 10000000)
    fooditem = FoodItem(
        id=food_item_id,
        # food_item_category_id=food_item_category_id,
        name="donkey_salt",
        emission_per_kg=100.0
    )
    fooditemequivalent = FoodItemEquivalent(
        id=food_item_equivalent_id,
        food_item_id=food_item_id,
        unit_type=10,
        conversion_factor=-100.0
    )
    # fooditemcategory = FoodItemCategory(
    #     id=food_item_category_id,
    #     name="donkey"
    # )
    with app_handle.app_context():
        db.session.add(fooditem)
        db.session.add(fooditemequivalent)
        # db.session.add(fooditemcategory)
        with pytest.raises(IntegrityError):
            db.session.commit()


# def test_fooditemcategory_create(app_handle):
#     """
#     Add valid fooditemcategory
#     """
#     food_item_category_id = random.randint(1, 10000000)
#     fooditemcategory = FoodItemCategory(
#         id=food_item_category_id,
#         name="donkey"
#     )
#     with app_handle.app_context():
#         db.session.add(fooditemcategory)
#         db.session.commit()
#         assert FoodItemCategory.query.count() == 1


# def test_fooditemcategory_create_with_invalid_name(app_handle):
#     """
#     Try to add fooditemcategory with invalid empty name
#     """
#     food_item_category_id = random.randint(1, 10000000)
#     fooditemcategory = FoodItemCategory(
#         id=food_item_category_id,
#         name=""
#     )
#     with app_handle.app_context():
#         db.session.add(fooditemcategory)
#         with pytest.raises(IntegrityError):
#             db.session.commit()
