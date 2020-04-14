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
            item.add_control("self", api.url_for(RecipeItem, recipe_id=recipe.id))
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
            "Location": api.url_for(RecipeItem, recipe_id=recipe.id)
        }
        response = Response(status=201, headers=headers)
        return response


class RecipeItem(Resource):

    def get(self, recipe_id):
        body = RecipeBuilder()
        body.add_namespace("clicook", "/api/link-relations/")
        recipe = Recipe.query.filter_by(id=recipe_id).first()

        if recipe is None:
            return MasonBuilder.get_error_response(404, "Recipe not found.",
            "Recipe with id {0} not found".format(recipe_id))

        body.add_control("self", api.url_for(RecipeCollection), recipe_id=recipe.id)
        body.add_control_edit_recipe(recipe.id)
        body.add_control_delete_recipe(recipe.id)
        body.add_control_add_ingredient(recipe.id)
        body.add_control("collection", api.url_for(RecipeCollection))
        body.add_control("profile", "/api/profiles/")
        # TODO: Add control for food-items with equivalents
        body["name"] = recipe.name
        body["id"] = recipe.id

        items = []
        # TODO: Add ingredients to items
        body["items"] = items
        # TODO: Add emission calculation once ingredients are implemented
        body["emissions_total"] = 0.0

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, recipe_id):
        if request.json is None:
            return MasonBuilder.get_error_response(415, "Request content type must be JSON", "")

        recipe = Recipe.query.filter_by(id=recipe_id).first()

        if recipe is None:
            return MasonBuilder.get_error_response(404, "Recipe not found.",
            "Recipe with id {0} not found".format(recipe_id))

        keys = request.json.keys()
        if 'name' not in keys:
            return MasonBuilder.get_error_response(400, "Incomplete request - missing fields", ["Missing field:name"])

        name = request.json['name']
        if len(name) < 1:
            return MasonBuilder.get_error_response(400, "Name is too short", "")
        elif len(name) > 64:
            return MasonBuilder.get_error_response(400, "Name is too long", "")
        recipe.name = name

        new_id = request.json['id']
        if new_id is not None:
            if new_id != recipe.id and Recipe.query.filter_by(id=new_id).first() is not None:
                return MasonBuilder.get_error_response(409, "Recipe id is already taken",
                    "Recipe id {0} is already taken".format(new_id))
            recipe.id = new_id

        db.session.commit()
        headers = {
            "Location": api.url_for(RecipeItem, recipe_id=recipe.id)
        }
        response = Response(None, 204, headers=headers)
        return response

    def delete(self, recipe_id):
        recipe = Recipe.query.filter_by(id=recipe_id).first()
        if recipe is None:
            return MasonBuilder.get_error_response(404, "Recipe not found.",
            "Recipe with id {0} not found".format(recipe_id))

        db.session.delete(recipe)
        db.session.commit()
        return Response(None, 204)


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

    def add_control_edit_recipe(self, recipe_id):
        self.add_control(
            "edit",
            href=api.url_for(RecipeItem, recipe_id=recipe_id),
            method="PUT",
            encoding="json",
            title="Edit an existing recipe",
            schema=RecipeBuilder.recipe_schema()
        )

    def add_control_delete_recipe(self, recipe_id):
        self.add_control(
            "clicook:delete",
            href=api.url_for(RecipeItem, recipe_id=recipe_id),
            method="DELETE",
            title="Delete an existing recipe"
        )

    def add_control_add_ingredient(self, recipe_id):
        self.add_control(
            "clicook:add-ingredient",
            href=api.url_for(RecipeItem, recipe_id=recipe_id),
            method="POST",
            encoding="json",
            title="Add a new recipe",
            schema={}  # TODO: Add ingredient schema
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
