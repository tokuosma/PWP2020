import json

from flask import request, Response
from flask_restful import Resource, reqparse

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
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Name of the recipe')
        args = parser.parse_args()
        if 'name' in args and args['name'] is not None:
            name = args['name']
            recipes = Recipe.query.filter(Recipe.name.startswith(name)).order_by(Recipe.name).all()
        else:
            recipes = Recipe.query.order_by(Recipe.name).all()

        for recipe in recipes:
            item = RecipeBuilder()
            item['name'] = recipe.name
            item.add_control("self", api.url_for(RecipeItem, id=recipe.id))
            item.add_control("profile", "/api/profiles/")
            items.append(item)

        body["items"] = items
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if request.json is None:
            return MasonBuilder.get_error_response(415, "Request content type must be JSON", "")

        keys = request.json.keys()
        if 'name' not in keys:
            return MasonBuilder.get_error_response(400, "Incomplete request - missing fields", ["Missing field:name"])

        name = request.json['name']
        if len(name) < 1:
            return MasonBuilder.get_error_response(400, "Name is too short", "")
        elif len(name) > 64:
            return MasonBuilder.get_error_response(400, "Name is too long", "")

        recipe = Recipe(
            name=name
        )
        db.session.add(recipe)
        db.session.commit()
        headers = {
            "Location": api.url_for(RecipeItem, id=recipe.id)
        }
        response = Response(status=201, headers=headers)
        return response


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
