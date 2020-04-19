import click
from flask.cli import with_appcontext
from sqlalchemy import CheckConstraint
from climatecook import db


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()


class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # recipe_category_id = db.Column(db.Integer, db.ForeignKey('recipe_category.id', ondelete="SET NULL"), nullable=True)
    name = db.Column(db.String(64), nullable=False)

    # recipe_category = db.relationship("RecipeCategory", back_populates="recipes")
    # ratings = db.relationship("Rating", back_populates="recipe", cascade="all,delete")
    ingredients = db.relationship("Ingredient", back_populates="recipe", cascade="all,delete")

    __table_args__ = (CheckConstraint('length(name) >= 1', name='cc_recipe_name'),)


# class RecipeCategory(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64), nullable=False)

#     recipes = db.relationship("Recipe", back_populates="recipe_category")


# class Rating(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id', ondelete="CASCADE"), nullable=False)
#     rating = db.Column(db.Integer, nullable=False)
#     comment = db.Column(db.String(2048), nullable=False)

#     recipe = db.relationship("Recipe", back_populates="ratings")

#     __table_args__ = (CheckConstraint('rating >= 1 AND rating <= 5', name='cc_rating_rating'),)


class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id', ondelete="CASCADE"), nullable=False)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=False)
    food_item_equivalent_id = db.Column(db.Integer, db.ForeignKey('food_item_equivalent.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)

    recipe = db.relationship("Recipe", back_populates="ingredients")
    food_item = db.relationship("FoodItem")
    food_item_equivalent = db.relationship("FoodItemEquivalent")

    __table_args__ = (CheckConstraint('quantity > 0', name='cc_ingredient_quantity'),)


class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # food_item_category_id = db.Column(db.Integer, db.ForeignKey('food_item_category.id'), nullable=True)
    name = db.Column(db.String(128), nullable=False)
    emission_per_kg = db.Column(db.Float, nullable=False)
    vegan = db.Column(db.Boolean, nullable=False, default=0)
    organic = db.Column(db.Boolean, nullable=False, default=0)
    domestic = db.Column(db.Boolean, nullable=False, default=0)

    # food_item_category = db.relationship("FoodItemCategory", back_populates="food_items")
    food_item_equivalents = db.relationship("FoodItemEquivalent", back_populates="food_item", cascade="all,delete")

    __table_args__ = (
        CheckConstraint('length(name) >= 1', name='cc_food_item_name'),
        CheckConstraint('emission_per_kg > 0', name='cc_emission_per_kg'),
    )


class FoodItemEquivalent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id', ondelete="CASCADE"), nullable=False)
    unit_type = db.Column(db.Integer, nullable=False)
    conversion_factor = db.Column(db.Float, nullable=False)

    food_item = db.relationship("FoodItem", back_populates="food_item_equivalents")

    __table_args__ = (
        CheckConstraint('unit_type > 0', name='cc_unit_type_enum_defined'),
        CheckConstraint('conversion_factor >= 0', name='cc_conversion_factor'),
        db.UniqueConstraint("unit_type", "food_item_id", name="tuc_unit_type_food_item_id")
    )


# class FoodItemCategory(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(64), nullable=False)

#     food_items = db.relationship("FoodItem", back_populates="food_item_category")

#     __table_args__ = (
#         CheckConstraint('length(name) >= 1', name='cc_food_item_category_name'),
#     )
