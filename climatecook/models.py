import click
from flask.cli import with_appcontext
from sqlalchemy import CheckConstraint
from climatecook import db



@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()


class Recipe(db.Model):
    __tablename__ = "Recipes"
    id = db.Column(db.Integer, primary_key=True)
    recipe_category_id = db.Column(db.Integer, db.ForeignKey('recipe_category.id'), nullable=True)
    name = db.Column(db.String(64), nullable=False)
    recipe_category = db.relationship("RecipeCategory", back_populates="recipes")
    __table_args__ = (CheckConstraint('length(name) >= 1', name='cc_recipe_name'),)


class RecipeCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    recipes = db.relationship("Recipe", back_populates="recipe_category")
