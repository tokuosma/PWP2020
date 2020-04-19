import json

from flask import Blueprint, redirect, Response
from flask_restful import Api

api_bp = Blueprint("api", __name__, url_prefix="/api")
api = Api(api_bp)

MASON = "application/vnd.mason+json"
NAMESPACE = "https://climatecook.docs.apiary.io/#reference/link-relations"
PROFILES = "https://climatecook.docs.apiary.io/#reference/profiles"

# this import must be placed after we create api to avoid issues with
# circular imports
from climatecook.resources.recipes import IngredientItem, RecipeCollection, RecipeItem
from climatecook.resources.food_items import (FoodItemCollection, FoodItemResource,
    FoodItemEquivalentCollection, FoodItemEquivalentResource)
from climatecook.resources.masonbuilder import MasonBuilder

api.add_resource(RecipeCollection, "/recipes/")
api.add_resource(RecipeItem, "/recipes/<recipe_id>/")
api.add_resource(IngredientItem, "/recipes/<recipe_id/ingredients/<ingredient_id/")

api.add_resource(FoodItemCollection, "/food-items/")
api.add_resource(FoodItemResource, "/food-items/<food_item_id>/")
api.add_resource(FoodItemEquivalentCollection, "/food-item-equivalents/")
api.add_resource(FoodItemEquivalentResource, "/food-items/<food_item_id>/equivalents/<food_item_equivalent_id/")


@api_bp.route("/")
def api_entry():
    masonBuilder = MasonBuilder()
    masonBuilder.add_namespace("clicook", "/api/link-relations/")
    masonBuilder.add_control("clicook:recipes-all", api.url_for(RecipeCollection))
    # TODO: ADD MISSING CONTROLS FOR API ENTRY
    return Response(json.dumps(masonBuilder), 200, mimetype=MASON)


@api_bp.route("/link-relations/")
def redirect_to_apiary_link_rels():
    return redirect(NAMESPACE)


@api_bp.route("/profiles/")
def redirect_to_apiary_profiles():
    return redirect(PROFILES)
