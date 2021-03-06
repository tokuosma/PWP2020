from flask import Blueprint, render_template, abort
from jinja2 import TemplateNotFound

client_bp = Blueprint("client", __name__, url_prefix="/client", static_folder="static", template_folder="static/html")


@client_bp.route('/')
def index():
    try:
        return render_template('index.html')
    except TemplateNotFound:
        abort(404)
