import json

from flask import Response
from flask_restful import Resource

from climatecook import db
from climatecook.api import api, MASON
from climatecook.resources.masonbuilder import MasonBuilder
from climatecook.models import Recipe


class RecipeCollection(Resource):

    def get(self):
        body = RecipeBuilder()
        body.add_namespace("clicook", "/api/link-relations/")
        body.add_control("self", api.url_for(RecipeCollection))
        body.add_control_add_recipe()

        items = []
        recipes = Recipe.query.order_by(Recipe.name).all()
        for recipe in recipes:
            item = RecipeBuilder()
            item.add_control("self", api.url_for(RecipeItem, id=recipe.id))
            item.add_control("profile", "/api/profiles/")

        body["items"] = items
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        pass


class RecipeItem(Resource):

    def get(self, id):
        pass

    def put(self, id):
        pass

    def delete(self, id):
        pass


class RecipeBuilder(MasonBuilder):

    def add_control_add_recipe(self):
        self.add_control(
            "clicook:add-recipe",
            href=api.url_for(RecipeCollection),
            method="POST",
            encoding="json",
            title="Add a new recipe",
            schema=RecipeBuilder.recipe_schema()
        )

    @staticmethod
    def recipe_schema():
        schema = {
            "type": "object",
            "required": ["name"]
        }
        props = schema["properties"] = {}
        # TODO: Add recipe category id if implemented
        props["name"] = {
            "description": "Recipes name",
            "type": "string"
        }
        return schema
