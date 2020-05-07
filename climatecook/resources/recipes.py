import json

from flask import request, Response
from flask_restful import Resource, reqparse

from climatecook import db
from climatecook.api import api, MASON
from climatecook.resources.masonbuilder import MasonBuilder
from climatecook.models import Recipe, Ingredient, FoodItem, FoodItemEquivalent


class RecipeCollection(Resource):

    def get(self):
        body = RecipeBuilder()
        body.add_namespace("clicook", "/api/link-relations/")
        body.add_control("self", api.url_for(RecipeCollection))
        from climatecook.resources.food_items import FoodItemCollection
        body.add_control("clicook:food-items-all", api.url_for(FoodItemCollection), title="Food items")
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
            item['id'] = recipe.id
            item['name'] = recipe.name
            item.add_control("self", api.url_for(RecipeItem, recipe_id=recipe.id))
            item.add_control("profile", "/api/profiles/")
            items.append(item)

            ingredients = Ingredient.query.filter_by(recipe_id=recipe.id).all()
            emissions_total = 0
            for ingredient in ingredients:
                emissions_total += ingredient.food_item.emission_per_kg \
                    * ingredient.quantity \
                    * ingredient.food_item_equivalent.conversion_factor
            item['emissions_total'] = emissions_total

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

        body.add_control("self", api.url_for(RecipeItem, recipe_id=recipe.id))
        body.add_control_edit_recipe(recipe.id)
        body.add_control_delete_recipe(recipe.id)
        body.add_control_add_ingredient(recipe.id)
        body.add_control("collection", api.url_for(RecipeCollection))
        body.add_control("profile", "/api/profiles/")
        body["name"] = recipe.name
        body["id"] = recipe.id

        items = []
        body["emissions_total"] = 0.0
        ingredients = Ingredient.query.filter_by(recipe_id=recipe_id).all()
        for ingredient in ingredients:
            item = IngredientBuilder()
            item["food_item_id"] = ingredient.food_item_id
            item["recipe_id"] = ingredient.recipe_id
            item["food_item_equivalent_id"] = ingredient.food_item_equivalent_id
            item["quantity"] = ingredient.quantity
            body["emissions_total"] += ingredient.food_item.emission_per_kg \
                * ingredient.quantity \
                * ingredient.food_item_equivalent.conversion_factor
            item.add_control("self", api.url_for(IngredientItem, recipe_id=recipe_id, ingredient_id=ingredient.id))
            item.add_control("profile", "/api/profiles/")
            items.append(item)

        body["items"] = items

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

            if new_id < 0:
                return MasonBuilder.get_error_response(400, "Recipe id must be a positive integer", "")
            recipe.id = new_id

        db.session.commit()
        headers = {
            "Location": api.url_for(RecipeItem, recipe_id=recipe.id)
        }
        response = Response(None, 204, headers=headers)
        return response

    def delete(self, recipe_id):
        """
        Delete recipe
        """
        recipe = Recipe.query.filter_by(id=recipe_id).first()
        if recipe is None:
            return MasonBuilder.get_error_response(404, "Recipe not found.",
            "Recipe with id {0} not found".format(recipe_id))

        db.session.delete(recipe)
        db.session.commit()
        return Response(None, 204)

    def post(self, recipe_id):
        """
        Add new ingredient to recipe
        """
        if request.json is None:
            return MasonBuilder.get_error_response(415, "Request content type must be JSON", "")

        recipe = Recipe.query.filter_by(id=recipe_id).first()

        if recipe is None:
            return MasonBuilder.get_error_response(404, "Recipe not found.",
            "Recipe with id {0} not found".format(recipe_id))

        # ingredients = Ingredient.query.filter_by(recipe_id=recipe.id).all()

        keys = request.json.keys()
        if not set(["food_item_id", "food_item_equivalent_id", "quantity"]).issubset(keys):
            return MasonBuilder.get_error_response(400, "Incomplete request - missing fields", "")

        food_item = FoodItem.query.filter_by(id=request.json['food_item_id']).first()
        if food_item is None:
            return MasonBuilder.get_error_response(404, "FoodItem not found.",
            "FoodItem with id {0} not found".format(request.json['food_item_id']))

        food_item_equivalent = FoodItemEquivalent.query.filter_by(food_item_id=food_item.id) \
            .filter_by(id=request.json['food_item_equivalent_id']).first()

        if food_item_equivalent is None:
            return MasonBuilder.get_error_response(404, "FoodItemEquivalent not found.",
            "FoodItemEquivalent with id {0} not found".format(request.json['food_item_equivalent_id']))

        quantity = 0
        try:
            quantity = float(request.json['quantity'])
            if quantity <= 0:
                raise ValueError
        except ValueError:
            return MasonBuilder.get_error_response(400, "Quantity must be a positive number", "")

        ingredient = Ingredient(
            recipe_id=recipe.id,
            food_item_id=food_item.id,
            food_item_equivalent_id=food_item_equivalent.id,
            quantity=quantity
        )

        db.session.add(ingredient)
        db.session.commit()
        headers = {
            "Location": api.url_for(IngredientItem,
                recipe_id=recipe.id,
                ingredient_id=ingredient.id)
        }
        response = Response(None, 201, headers=headers)
        return response


class IngredientItem(Resource):

    def get(self, recipe_id, ingredient_id):
        body = IngredientBuilder()
        body.add_namespace("clicook", "/api/link-relations/")
        ingredient = Ingredient.query.filter_by(id=ingredient_id).first()

        if ingredient is None:
            return MasonBuilder.get_error_response(404, "Ingredient not found",
            "Ingredient with id {0} not found".format(ingredient_id))

        body.add_control("self", api.url_for(IngredientItem, recipe_id=recipe_id, ingredient_id=ingredient_id))
        body.add_control_edit_ingredient(ingredient.recipe_id, ingredient.id)
        body.add_control_delete_ingredient(ingredient.recipe_id, ingredient.id)
        body.add_control("profile", "/api/profiles/")

        body["id"] = ingredient.id
        body["recipe_id"] = ingredient.recipe_id
        body["food_item_id"] = ingredient.food_item_id
        body["food_item_equivalent_id"] = ingredient.food_item_equivalent_id
        body["quantity"] = ingredient.quantity

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, ingredient_id, recipe_id):
        if request.json is None:
            return MasonBuilder.get_error_response(415, "Request content type must be JSON", "")

        ingredient = Ingredient.query.filter_by(id=ingredient_id).first()

        if ingredient is None:
            return MasonBuilder.get_error_response(404, "Ingredient not found.",
            "Ingredient with id {0} not found".format(ingredient_id))

        keys = request.json.keys()
        if not set(["recipe_id", "food_item_id", "food_item_equivalent_id", "quantity"]).issubset(keys):
            return MasonBuilder.get_error_response(400, "Incomplete request - missing fields", "Missing fields")

        new_id = request.json['id']
        if new_id is not None:
            if new_id != ingredient.id and Ingredient.query.filter_by(id=new_id).first() is not None:
                return MasonBuilder.get_error_response(409, "Ingredient id is already taken",
                    "Ingredient id {0} is already taken".format(new_id))
            if new_id < 0:
                return MasonBuilder.get_error_response(400, "Ingredient id must be a positive integer", "")
            ingredient.id = new_id

        new_food_item_id = request.json['food_item_id']
        if new_food_item_id is not None:
            if new_food_item_id < 0:
                return MasonBuilder.get_error_response(400, "FoodItem id must be a positive integer", "")
            ingredient.food_item_id = new_food_item_id

        new_food_item_equivalent_id = request.json['food_item_equivalent_id']
        if new_food_item_equivalent_id is not None:
            if new_food_item_equivalent_id < 0:
                return MasonBuilder.get_error_response(400, "FoodItemEquivalent id must be a positive integer", "")
            ingredient.food_item_equivalent_id = new_food_item_equivalent_id

        new_recipe_id = request.json['recipe_id']
        if new_recipe_id is not None:
            if new_recipe_id < 0:
                return MasonBuilder.get_error_response(400, "Recipe id must be a positive integer", "")
            ingredient.recipe_id = new_recipe_id

        quantity = 0
        try:
            quantity = float(request.json["quantity"])
            if quantity < 0:
                raise ValueError
        except ValueError:
            return MasonBuilder.get_error_response(400, "Quantity must be a positive number", "")
        ingredient.quantity = quantity

        db.session.commit()
        headers = {
            "Location": api.url_for(IngredientItem, recipe_id=ingredient.recipe_id, ingredient_id=ingredient.id)
        }
        response = Response(None, 204, headers=headers)
        return response

    def delete(self, ingredient_id, recipe_id):
        ingredient = Ingredient.query.filter_by(id=ingredient_id).first()
        if ingredient is None:
            return MasonBuilder.get_error_response(404, "Ingredient not found",
            "Ingredient with id {0} not found".format(ingredient_id))

        db.session.delete(ingredient)
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
            title="Add a new ingredient",
            schema=IngredientBuilder.ingredient_schema()  # Added ingredient schema
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


class IngredientBuilder(MasonBuilder):

    def add_control_edit_ingredient(self, recipe_id, ingredient_id):
        self.add_control(
            "edit",
            href=api.url_for(IngredientItem, recipe_id=recipe_id, ingredient_id=ingredient_id),
            method="PUT",
            encoding="json",
            title="Edit an ingredient",
            schema=IngredientBuilder.ingredient_schema()
        )

    def add_control_delete_ingredient(self, recipe_id, ingredient_id):
        self.add_control(
            "clicook:delete",
            href=api.url_for(IngredientItem, recipe_id=recipe_id, ingredient_id=ingredient_id),
            method="DELETE",
            title="Delete an ingredient",
        )

    @staticmethod
    def ingredient_schema():
        schema = {
            "type": "object",
            "required": ["recipe_id", "food_item_id", "food_item_equivalent_id", "quantity"]
        }
        props = schema["properties"] = {}
        props["recipe_id"] = {
            "description": "Recipes ID",
            "type": "number"
        }
        props["food_item_id"] = {
            "description": "Food items ID",
            "type": "number"
        }
        props["food_item_equivalent_id"] = {
            "description": "Equivalents ID",
            "type": "number"
        }
        props["quantity"] = {
            "description": "Amount of food item",
            "type": "number"
        }
        return schema
