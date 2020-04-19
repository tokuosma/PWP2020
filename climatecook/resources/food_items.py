import json

from flask import request, Response
from flask_restful import Resource, reqparse

from climatecook import db
from climatecook.api import api, MASON
from climatecook.resources.masonbuilder import MasonBuilder
from climatecook.models import FoodItem


class FoodItemCollection(Resource):

    def get(self):
        body = FoodItemBuilder()
        body.add_namespace("clicook", "/api/link-relations/")
        body.add_control("self", api.url_for(FoodItemCollection))
        body.add_control_add_food_item()

        items = []
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str, help='Name of the food item')
        args = parser.parse_args()
        if 'name' in args and args['name'] is not None:
            name = args['name']
            food_items = FoodItem.query.filter(FoodItem.name.startswith(name)).order_by(FoodItem.name).all()
        else:
            food_items = FoodItem.query.order_by(FoodItem.name).all()

        for food_item in food_items:
            item = FoodItemBuilder()
            item['name'] = food_item.name
            item['emission_per_kg'] = food_item.emission_per_kg
            item['vegan'] = food_item.vegan
            item['domestic'] = food_item.domestic
            item['organic'] = food_item.organic
            item.add_control("self", api.url_for(FoodItemResource, food_item_id=food_item.id))
            item.add_control("profile", "/api/profiles/")
            items.append(item)

        body["items"] = items
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self):
        if request.json is None:
            return MasonBuilder.get_error_response(415, "Request content type must be JSON", "")

        required = FoodItemBuilder.food_item_schema()['required']

        missing = []

        for field in required:
            if field not in request.json.keys():
                missing.append(field)

        if len(missing) > 0:
            details = []
            for field in missing:
                details.append("Missing field:{0}".format(field))
            return MasonBuilder.get_error_response(400, "Incomplete request - missing fields", details)

        name = request.json['name']
        if len(name) < 1:
            return MasonBuilder.get_error_response(400, "Name is too short", "")
        elif len(name) > 128:
            return MasonBuilder.get_error_response(400, "Name is too long", "")

        raw_emission_per_kg = request.json['emission_per_kg']
        emission_per_kg = 0.0
        try:
            emission_per_kg = float(raw_emission_per_kg)
        except ValueError:
            return MasonBuilder.get_error_response(400, "emission_per_kg must be a number", "")
        if emission_per_kg < 0:
            return MasonBuilder.get_error_response(400, "emission_per_kg must be a positive number", "")

        vegan = False
        if 'vegan' in request.json.keys() and request.json['vegan'] is not None:
            vegan = request.json['vegan']

        organic = False
        if 'organic' in request.json.keys() and request.json['organic'] is not None:
            organic = request.json['organic']

        domestic = False
        if 'domestic' in request.json.keys() and request.json['domestic'] is not None:
            domestic = request.json['domestic']

        food_item = FoodItem(
            name=name,
            emission_per_kg=emission_per_kg,
            vegan=vegan,
            organic=organic,
            domestic=domestic
        )
        db.session.add(food_item)
        db.session.commit()
        headers = {
            "Location": api.url_for(FoodItemResource, food_item_id=food_item.id)
        }
        response = Response(status=201, headers=headers)
        return response


class FoodItemResource(Resource):

    def get(self, food_item_id):
        raise NotImplementedError

    def post(self, food_item_id):
        raise NotImplementedError

    def put(self, food_item_id):
        raise NotImplementedError

    def delete(self, food_item_id):
        raise NotImplementedError


class FoodItemBuilder(MasonBuilder):

    def add_control_add_food_item(self):
        self.add_control(
            "clicook:add-food-item",
            href=api.url_for(FoodItemCollection),
            method="POST",
            encoding="json",
            title="Add a new food item",
            schema=FoodItemBuilder.food_item_schema()
        )

    def add_control_edit_food_item(self, food_item_id):
        self.add_control(
            "edit",
            href=api.url_for(FoodItemResource, food_item_id=food_item_id),
            method="PUT",
            encoding="json",
            title="Edit an existing food item",
            schema=FoodItemBuilder.food_item_schema()
        )

    def add_control_delete_food_item(self, food_item_id):
        self.add_control(
            "clicook:delete",
            href=api.url_for(FoodItemResource, food_item_id=food_item_id),
            method="DELETE",
            title="Delete an existing food item"
        )

    def add_control_add_food_item_equivalent(self, food_item_id):
        self.add_control(
            "clicook:add-food-item-equivalent",
            href=api.url_for(FoodItemResource, food_item_id=food_item_id),
            method="POST",
            encoding="json",
            title="Add a new food item equivalent",
            schema={}  # TODO: Add food item equivalent schema
        )

    @staticmethod
    def food_item_schema():
        schema = {
            "type": "object",
            "required": ["name", "emission_per_kg"]
        }
        props = schema["properties"] = {}
        # TODO: Add recipe category id if implemented
        props["name"] = {
            "description": "Food items name",
            "type": "string"
        }
        props["emission_per_kg"] = {
            "description": "Amount of emissions per one kilogram of the food item",
            "type": "number"
        }
        props["vegan"] = {
            "description": "Is the food item compatible with a vegan diet",
            "type": "boolean"
        }
        props["organic"] = {
            "description": "Is the item organically produced",
            "type": "boolean"
        }
        props["domestic"] = {
            "description": "Is the item domestically produced",
            "type": "boolean"
        }
        return schema
