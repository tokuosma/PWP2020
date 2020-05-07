import json

from flask import request, Response
from flask_restful import Resource, reqparse

from climatecook import db
from climatecook.api import api, MASON
from climatecook.resources.masonbuilder import MasonBuilder
from climatecook.models import FoodItem, FoodItemEquivalent, EquivalentUnitType, Ingredient


class FoodItemCollection(Resource):

    def get(self):
        body = FoodItemBuilder()
        body.add_namespace("clicook", "/api/link-relations/")
        body.add_control("self", api.url_for(FoodItemCollection))
        from climatecook.resources.recipes import RecipeCollection
        body.add_control("clicook:recipes-all", api.url_for(RecipeCollection), title="Recipes")
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
            print(food_item.id)
            item.add_control("self", api.url_for(FoodItemResource, food_item_id=food_item.id))
            print(item['@controls']['self'])
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
        body = FoodItemBuilder()
        body.add_namespace("clicook", "/api/link-relations/")
        food_item = FoodItem.query.filter_by(id=food_item_id).first()

        if food_item is None:
            return MasonBuilder.get_error_response(404, "Food item not found.",
            "FoodItem with id {0} not found".format(food_item_id))

        body.add_control("self", api.url_for(FoodItemResource, food_item_id=food_item.id))
        body.add_control_edit_food_item(food_item.id)
        body.add_control_delete_food_item(food_item.id)
        body.add_control_add_food_item_equivalent(food_item.id)
        body.add_control("collection", api.url_for(FoodItemCollection))
        body.add_control("profile", "/api/profiles/")
        # TODO: Add control for food-items with equivalents
        body["id"] = food_item.id
        body['name'] = food_item.name
        body['emission_per_kg'] = food_item.emission_per_kg
        body['vegan'] = food_item.vegan
        body['domestic'] = food_item.domestic
        body['organic'] = food_item.organic

        items = []
        equivalents = FoodItemEquivalent.query.filter_by(food_item_id=food_item.id).all()
        for equivalent in equivalents:
            item = FoodItemEquivalentBuilder()
            item['unit_type'] = equivalent.unit_type
            item['conversion_factor'] = equivalent.conversion_factor
            item.add_control("self", api.url_for(FoodItemEquivalentResource,
                food_item_id=food_item.id,
                food_item_equivalent_id=equivalent.id))
            item.add_control('profile', '/api/profiles/')
            items.append(item)
        body["items"] = items
        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, food_item_id):
        """
        Add food item equivalent
        """
        if request.json is None:
            return MasonBuilder.get_error_response(415, "Request content type must be JSON", "")

        food_item = FoodItem.query.filter_by(id=food_item_id).first()

        if food_item is None:
            return MasonBuilder.get_error_response(404, "Food item not found.",
            "FoodItem with id {0} not found".format(food_item_id))

        equivalents = FoodItemEquivalent.query.filter_by(food_item_id=food_item.id).all()

        keys = request.json.keys()
        if not set(["unit_type", "conversion_factor"]).issubset(keys):
            return MasonBuilder.get_error_response(400, "Incomplete request - missing fields", "")

        unit_type = request.json['unit_type']
        if unit_type not in [e.value for e in EquivalentUnitType]:
            return MasonBuilder.get_error_response(400, "Unknown unit type",
                "Unknown unit type {}".format(unit_type))
        if unit_type in [e.unit_type for e in equivalents]:
            return MasonBuilder.get_error_response(409, "Unit type is reserved",
            "Food item equivalent with unit type {} already exists".format(unit_type))

        conversion_factor = 0
        try:
            conversion_factor = float(request.json['conversion_factor'])
            if conversion_factor < 0:
                raise ValueError
        except ValueError:
            return MasonBuilder.get_error_response(400, "Conversion factor must be a positive number", "")

        food_item_equivalent = FoodItemEquivalent(
            food_item_id=food_item.id,
            unit_type=unit_type,
            conversion_factor=conversion_factor
        )

        db.session.add(food_item_equivalent)
        db.session.commit()
        headers = {
            "Location": api.url_for(FoodItemEquivalentResource,
                food_item_id=food_item.id,
                food_item_equivalent_id=food_item_equivalent.id)
        }
        response = Response(None, 201, headers=headers)
        return response

    def put(self, food_item_id):
        if request.json is None:
            return MasonBuilder.get_error_response(415, "Request content type must be JSON", "")

        food_item = FoodItem.query.filter_by(id=food_item_id).first()

        if food_item is None:
            return MasonBuilder.get_error_response(404, "Food item not found.",
            "FoodItem with id {0} not found".format(food_item_id))

        keys = request.json.keys()
        if 'name' not in keys:
            return MasonBuilder.get_error_response(400, "Incomplete request - missing fields", ["Missing field:name"])
        if 'emission_per_kg' not in keys:
            return MasonBuilder.get_error_response(400,
                "Incomplete request - missing fields",
                ["Missing field:emission_per_kg"])

        name = request.json['name']
        if len(name) < 1:
            return MasonBuilder.get_error_response(400, "Name is too short", "")
        elif len(name) > 128:
            return MasonBuilder.get_error_response(400, "Name is too long", "")
        food_item.name = name

        emissions = 0
        try:
            emissions = float(request.json['emission_per_kg'])
            if emissions < 0:
                raise ValueError
        except ValueError:
            return MasonBuilder.get_error_response(400, "Emissions per kg must be a positive number", "")
        food_item.emission_per_kg = emissions

        if "id" in keys:
            try:
                new_id = int(request.json['id'])
                if new_id is not None:
                    if new_id != food_item.id and FoodItem.query.filter_by(id=new_id).first() is not None:
                        return MasonBuilder.get_error_response(409, "FoodItem id is already taken",
                            "FoodItem id {0} is already taken".format(new_id))

                    if new_id < 0:
                        return MasonBuilder.get_error_response(400, "FoodItem id must be a positive integer", "")
                    food_item.id = new_id
            except ValueError:
                return MasonBuilder.get_error_response(400, "FoodItem id must be a positive integer", "")

        if 'vegan' in request.json.keys() and type(request.json['vegan']) is bool:
            food_item.vegan = request.json['vegan']

        if 'organic' in request.json.keys() and type(request.json['organic']) is bool:
            food_item.organic = request.json['organic']

        if 'domestic' in request.json.keys() and type(request.json['domestic']) is bool:
            food_item.domestic = request.json['domestic']

        db.session.commit()
        headers = {
            "Location": api.url_for(FoodItemResource, food_item_id=food_item.id)
        }
        response = Response(None, 204, headers=headers)
        return response

    def delete(self, food_item_id):
        food_item = FoodItem.query.filter_by(id=food_item_id).first()
        if food_item is None:
            return MasonBuilder.get_error_response(404, "FoodItem not found.",
            "FoodItem with id {0} not found".format(food_item_id))

        num_ingredient = Ingredient.query.filter_by(food_item_id=food_item_id).count()
        if num_ingredient > 0:
            return MasonBuilder.get_error_response(409, "Cannot delete food item in use.",
            "FoodItem with is used for {0} ingredients".format(num_ingredient))

        db.session.delete(food_item)
        db.session.commit()
        return Response(None, 204)


class FoodItemEquivalentResource(Resource):
    def get(self, food_item_id, food_item_equivalent_id):
        body = FoodItemEquivalentBuilder()
        body.add_namespace("clicook", "/api/link-relations/")
        food_item_equivalent = FoodItemEquivalent.query.filter_by(id=food_item_equivalent_id).first()

        if food_item_equivalent is None:
            return MasonBuilder.get_error_response(404, "Equivalent not found",
            "FoodItemEquivalent with id {0} not found".format(food_item_equivalent_id))

        body.add_control("self", api.url_for(FoodItemEquivalentResource, food_item_id=food_item_equivalent.food_item_id,
        food_item_equivalent_id=food_item_equivalent.id))
        body.add_control_edit_food_item_equivalent(food_item_equivalent.food_item_id, food_item_equivalent.id)
        body.add_control_delete_food_item_equivalent(food_item_equivalent.food_item_id, food_item_equivalent.id)
        body.add_control("profile", "/api/profiles/")

        body["id"] = food_item_equivalent.id
        body["food_item_id"] = food_item_equivalent.food_item_id
        body["unit_type"] = food_item_equivalent.unit_type
        body["conversion_factor"] = food_item_equivalent.conversion_factor

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, food_item_id, food_item_equivalent_id):
        if request.json is None:
            return MasonBuilder.get_error_response(415, "Request content type must be JSON", "")

        food_item_equivalent = FoodItemEquivalent.query.filter_by(id=food_item_equivalent_id).first()

        if food_item_equivalent is None:
            return MasonBuilder.get_error_response(404, "Food item equivalent not found.",
            "FoodItemEquivalent with id {0} not found".format(food_item_equivalent_id))

        keys = request.json.keys()
        if not set(["food_item_id", "unit_type", "conversion_factor"]).issubset(keys):
            return MasonBuilder.get_error_response(400, "Incomplete request - missing fields", "")

        unit_type = request.json['unit_type']
        if unit_type not in [e.value for e in EquivalentUnitType]:
            return MasonBuilder.get_error_response(400, "Unknown unit type",
                "Unknown unit type {}".format(unit_type))
        food_item_equivalent.unit_type = unit_type

        conversion_factor = 0
        try:
            conversion_factor = float(request.json['conversion_factor'])
            if conversion_factor < 0:
                raise ValueError
        except ValueError:
            return MasonBuilder.get_error_response(400, "Conversion factor must be a positive number", "")
        food_item_equivalent.conversion_factor = conversion_factor
        if "food_item_id" in keys:
            try:
                new_food_item_id = int(request.json["food_item_id"])
                if new_food_item_id is not None:
                    if new_food_item_id < 0:
                        return MasonBuilder.get_error_response(400,
                            "FoodItem id must be a positive integer", "")
            except ValueError:
                return MasonBuilder.get_error_response(400, "FoodItem id must be a positive integer", "")
        if "id" in keys:
            try:
                new_id = int(request.json['id'])
                if new_id is not None:
                    if new_id != food_item_equivalent.id and FoodItemEquivalent.query \
                            .filter_by(id=new_id).first() is not None:
                        return MasonBuilder.get_error_response(409, "FoodItemEquivalent id is already taken",
                            "FoodItemEquivalent id {0} is already taken".format(new_id))

                    if new_id < 0:
                        return MasonBuilder.get_error_response(400,
                            "FoodItemEquivalent id must be a positive integer", "")
                    food_item_equivalent.id = new_id
            except ValueError:
                return MasonBuilder.get_error_response(400, "FoodItemEquivalent id must be a positive integer", "")

        db.session.commit()
        headers = {
            "Location": api.url_for(FoodItemEquivalentResource, food_item_equivalent_id=food_item_equivalent.id, food_item_id=food_item_id)
        }
        response = Response(None, 204, headers=headers)
        return response

    def delete(self, food_item_equivalent_id, food_item_id):
        food_item_equivalent = FoodItemEquivalent.query.filter_by(id=food_item_equivalent_id).first()
        if food_item_equivalent is None:
            return MasonBuilder.get_error_response(404, "FoodItemEquivalent not found.",
            "FoodItemEquivalent with id {0} not found".format(food_item_equivalent_id))
        db.session.delete(food_item_equivalent)
        db.session.commit()
        return Response(None, 204)


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
            schema=FoodItemBuilder.food_item_equivalent_schema()
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

    @staticmethod
    def food_item_equivalent_schema():
        schema = {
            "type": "object",
            "required": ["food_item_id", "unit_type", "conversion_factor"]
        }
        props = schema["properties"] = {}
        props["food_item_id"] = {
            "description": "Food items ID",
            "type": "number"
        }
        props["unit_type"] = {
            "description": "Unit type",
            "type": "string",
            'enum': [e.value for e in EquivalentUnitType]
        }
        props["conversion_factor"] = {
            "description": "Translates unit to kg",
            "type": "number"
        }
        return schema


class FoodItemEquivalentBuilder(MasonBuilder):
    def add_control_edit_food_item_equivalent(self, food_item_id, food_item_equivalent_id):
        self.add_control(
            "edit",
            href=api.url_for(FoodItemEquivalentResource, food_item_id=food_item_id,
            food_item_equivalent_id=food_item_equivalent_id),
            method="PUT",
            encoding="json",
            title="Edit an existing equivalent",
            schema=FoodItemBuilder.food_item_equivalent_schema()
        )

    def add_control_delete_food_item_equivalent(self, food_item_id, food_item_equivalent_id):
        self.add_control(
            "clicook:delete",
            href=api.url_for(FoodItemEquivalentResource, food_item_id=food_item_id,
            food_item_equivalent_id=food_item_equivalent_id),
            method="DELETE",
            title="Delete an existing equivalent",
        )
