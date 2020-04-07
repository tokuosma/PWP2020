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
from climatecook.resources.recipes import RecipeCollection, RecipeItem
from climatecook.resources.masonbuilder import MasonBuilder

api.add_resource(RecipeCollection, "/recipes/")
api.add_resource(RecipeItem, "/recipes/<id>/")


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
