import json
import os
import tempfile
import random

import pytest
from jsonschema import validate


from climatecook import create_app, db
from climatecook.models import Recipe, FoodItem, FoodItemEquivalent, Ingredient

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    app = create_app(config)
    with app.app_context():
        db.create_all()
        _populate_db()

    yield app.test_client()

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)


def _populate_db():
    for i in range(1, 4):
        r = Recipe(
            id=i,
            name="test-recipe-{}".format(i)
        )
        db.session.add(r)

        f = FoodItem(
            id=i,
            name="test-food-item-{}".format(i),
            emission_per_kg=float(i),
        )
        db.session.add(f)

        e = FoodItemEquivalent(
            food_item_id=i,
            unit_type="kilogram",
            conversion_factor=1
        )
        db.session.add(e)

        g = Ingredient(
            id=i,
            recipe_id=i,
            food_item_id=i,
            food_item_equivalent_id=i,
            quantity=1.0,
        )
        db.session.add(g)

    db.session.commit()


def _get_obj(obj_type):
    """
    Creates a valid JSON object of the desired type to be used for PUT and POST tests.
    """
    i = random.randint(1, 10000)
    if(obj_type == "recipe"):
        return {
            "id": i,
            "name": "test-recipe"
        }

    if(obj_type == "food_item"):
        return{
            "id": i,
            "name": "test-food-item-{}".format(i),
            "emission_per_kg": float(i),
            "vegan": False,
            "organic": False,
            "domestic": False
        }

    if(obj_type == "food_item_equivalent"):
        return {
            "id": i,
            "food_item_id": 1,
            "conversion_factor": .1,
            "unit_type": "cup"
        }

    if(obj_type == "ingredient"):
        return {
            "id": i,
            "recipe_id": 1,
            "food_item_id": 1,
            "food_item_equivalent_id": 1,
            "quantity": 1.0
        }


def _check_namespace(client, response):
    """
    Checks that the "clicook" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """

    ns_href = response["@namespaces"]["clicook"]["name"]
    resp = client.get(ns_href)
    # Assert that the redirect link
    assert resp.status_code == 302


def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 200


def _check_control_get_method_redirect(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control gets a redirect.
    """

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    assert resp.status_code == 302


def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 204


def _check_control_put_method(ctrl, client, obj, obj_type):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    body = _get_obj(obj_type)
    body["id"] = obj["id"]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204


def _check_control_post_method(ctrl, client, obj, obj_type):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = _get_obj(obj_type)
    validate(body, schema)
    resp = client.post(href, json=body)
    assert resp.status_code == 201


class TestRecipeCollection(object):

    RESOURCE_URL = "/api/recipes/"

    def test_get(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.
        """
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_post_method("clicook:add-recipe", client, body, "recipe")
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "name" in item
            _check_control_get_method("self", client, item)
            _check_control_get_method_redirect("profile", client, item)

    def test_get_name(self, client):
        """
        Test the GET method with additional query parameter 'name'.
        The query should match one recipe in the test DB.
        """
        resp = client.get(self.RESOURCE_URL + "?name=test-recipe-1")
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_post_method("clicook:add-recipe", client, body, "recipe")
        assert len(body["items"]) == 1
        for item in body["items"]:
            assert "name" in item
            _check_control_get_method("self", client, item)
            _check_control_get_method_redirect("profile", client, item)

    def test_get_name_no_result(self, client):
        """
        Test the GET method with additional query parameter 'name'.
        The query should match no recipe in the test DB.
        """
        resp = client.get(self.RESOURCE_URL + "?name=macaron")
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_post_method("clicook:add-recipe", client, body, "recipe")
        assert len(body["items"]) == 0

    def test_post_valid(self, client):
        """
        Tests the POST method using a valid object.
        """
        valid = _get_obj("recipe")

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        resource_url = self.RESOURCE_URL + "4" + "/"
        assert resp.headers["Location"].endswith(resource_url)
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == valid["name"]

    def test_post_invalid_content_type(self, client):
        """
        Tests the POST method with invalid content type
        """
        valid = _get_obj("recipe")
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_invalid_body(self, client):
        """
        Tests the POST method with invalid body
        """
        invalid = {"game": "kek"}
        resp = client.post(self.RESOURCE_URL, json=invalid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)


class TestRecipeItem(object):

    RESOURCE_URL = "/api/recipes/1/"
    INVALID_RESOURCE_URL = "/api/recipes/lalilulelo/"

    def test_get(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work.
        """
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method_redirect("profile", client, body)
        _check_control_get_method("self", client, body)
        _check_control_put_method("edit", client, body, "recipe")
        _check_control_post_method("clicook:add-ingredient", client, body, "ingredient")
        _check_control_delete_method("clicook:delete", client, body)
        assert "name" in body
        assert "id" in body
        assert "emissions_total" in body
        assert "items" in body
        items = body['items']
        for item in items:
            _check_control_get_method("self", client, item)
            _check_control_get_method_redirect("profile", client, item)

    def test_get_not_found(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.
        """
        resp = client.get(self.INVALID_RESOURCE_URL)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_valid(self, client):
        """
        Tests the PUT method using a valid object.
        """
        valid = _get_obj("recipe")
        valid["id"] = 1
        new_name = "new_name"
        valid["name"] = new_name
        # test with valid and see that it exists afterward
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        resource_url = self.RESOURCE_URL
        assert resp.headers["Location"].endswith(resource_url)
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == new_name

    def test_put_conflict(self, client):
        """
        Tests the PUT method using a object with conflicting id.
        """
        valid = _get_obj("recipe")
        valid["id"] = 2
        # test with valid and see that it exists afterward
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_content_type(self, client):
        """
        Tests the PUT with wrong content type.
        """
        valid = _get_obj("recipe")
        # test with valid and see that it exists afterward
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_content_name(self, client):
        """
        Tests the PUT method using an object with invalid name.
        """
        valid = _get_obj("recipe")
        valid["name"] = ""
        # Name too short
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid["name"] = "KASDKASDKJASDLASJHDLALSJHDLKAJSLDJASIHATEKLDJKLASJDKLASJDKLASJDKLJ"
        # Name too long
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_id(self, client):
        """
        Tests the PUT method using an object with invalid id.
        """
        valid = _get_obj("recipe")
        valid["id"] = -1000
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_delete(self, client):
        """
        Tests the DELETE method using an valid id.
        """
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404

    def test_delete_not_found(self, client):
        """
        Tests the DELETE method using an invalid id.
        """
        resp = client.delete(self.INVALID_RESOURCE_URL)
        assert resp.status_code == 404

    def test_post_valid(self, client):
        """
        Test the POST method using a valid ingredient.
        """
        valid = _get_obj("ingredient")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_not_found(self, client):
        """
        Test the POST method using invalid id's.
        """
        valid = _get_obj("ingredient")
        resp = client.post(self.INVALID_RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid['food_item_id'] = "99999"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid = _get_obj("ingredient")
        valid['food_item_equivalent_id'] = "99999"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_missing_fields(self, client):
        """
        Test the POST method using with missing required fields
        """
        valid = _get_obj("ingredient")
        valid.pop('food_item_id')
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid = _get_obj("ingredient")
        valid.pop('food_item_equivalent_id')
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid = _get_obj("ingredient")
        valid.pop('quantity')
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_invalid_quantity(self, client):
        """
        Test the POST method using with missing required fields
        """
        valid = _get_obj("ingredient")
        valid['quantity'] = "lalilulelo"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid = _get_obj("ingredient")
        valid['quantity'] = -1.0
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)


class TestIngredientItem(object):

    RESOURCE_URL = "/api/recipes/1/ingredients/1"
    INVALID_RESOURCE_URL = "/api/recipes/1/ingredients/lalilulelo"

    def test_get(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB population are present, and their controls.
        """
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        body.json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_post_method("edit", client, body, "ingredient")
        _check_control_delete_method("clicook:delete", client, body)

        assert "id" in body
        assert "recipe_id" in body
        assert "food_item_id" in body
        assert "food_item_equivalent_id" in body
        assert "quantity" in body

    def test_get_not_found(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.
        """
        resp = client.get(self.INVALID_RESOURCE_URL)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_valid(self, client):
        """
        Tests the PUT method using a valid object.
        """
        valid = _get_obj("ingredient")
        valid["id"] = 1
        new_quantity = 58.50
        valid["quantity"] = new_quantity
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        resource_url = self.RESOURCE_URL
        assert resp.headers["Location"].endswith(resource_url)
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["quantity"] == new_quantity

    def test_put_not_found(self, client):
        """
        Test the PUT method with invalid resource url
        """
        valid = _get_obj("ingredient")
        valid["id"] = 1
        resp = client.put(self.INVALID_RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_conflict(self, client):
        """
        Tests the PUT method using a object with conflicting id.
        """
        valid = _get_obj("ingredient")
        valid["id"] = 2
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_content_type(self, client):
        """
        Tests the PUT with wrong content type.
        """
        valid = _get_obj("ingredient")
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_missing_fields(self, client):
        """
        Tests the PUT method using an object with missing resource id.
        """
        valid = _get_obj("ingredient")
        valid["id"] = 1
        valid.pop("resource_id")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_id(self, client):
        """
        Tests the PUT method using an object with invalid id.
        """
        valid = _get_obj("ingredient")
        valid["id"] = -1000
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile". client, body)

    def test_put_invalid_recipe_id(self, client):
        """
        Tests the PUT method using an object with invalid recipe id.
        """
        valid = _get_obj("ingredient")
        valid["recipe_id"] = -1000
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile". client, body)

    def test_put_invalid_food_item_id(self, client):
        """
        Tests the PUT method using an object with invalid food item id.
        """
        valid = _get_obj("ingredient")
        valid["food_item_id"] = -1000
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile". client, body)

    def test_put_invalid_food_item_equivalent_id(self, client):
        """
        Tests the PUT method using an object with invalid equivalent id.
        """
        valid = _get_obj("ingredient")
        valid["food_item_equivalent_id"] = -1000
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile". client, body)

    def test_put_invalid_quantity(self, client):
        """
        Tests the PUT method using an object with invalid quantity.
        """
        valid = _get_obj("ingredient")
        valid["quantity"] = "lalilulelo"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_delete(self, client):
        """
        Tests the DELETE method using an valid id.
        """
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404

    def test_delete_not_found(self, client):
        """
        Tests the DELETE method using an invalid id.
        """
        resp = client.delete(self.INVALID_RESOURCE_URL)
        assert resp.status_code == 404


class TestFoodItemCollection(object):

    RESOURCE_URL = "/api/food-items/"

    def test_get(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.
        """
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_post_method("clicook:add-food-item", client, body, "food_item")
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "name" in item
            _check_control_get_method("self", client, item)
            _check_control_get_method_redirect("profile", client, item)

    def test_get_name(self, client):
        """
        Test the GET method with additional query parameter 'name'.
        The query should match one recipe in the test DB.
        """
        resp = client.get(self.RESOURCE_URL + "?name=test-food-item-1")
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_post_method("clicook:add-food-item", client, body, "food_item")
        assert len(body["items"]) == 1
        for item in body["items"]:
            assert "name" in item
            _check_control_get_method("self", client, item)
            _check_control_get_method_redirect("profile", client, item)

    def test_get_name_no_result(self, client):
        """
        Test the GET method with additional query parameter 'name'.
        The query should match no recipe in the test DB.
        """
        resp = client.get(self.RESOURCE_URL + "?name=macaron")
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_post_method("clicook:add-food-item", client, body, "food_item")
        assert len(body["items"]) == 0

    def test_post_valid(self, client):
        """
        Tests the POST method using a valid object.
        """
        valid = _get_obj("food_item")

        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        resource_url = self.RESOURCE_URL + "4" + "/"
        assert resp.headers["Location"].endswith(resource_url)
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == valid["name"]

    def test_post_invalid_content_type(self, client):
        """
        Tests the POST method with invalid content type
        """
        valid = _get_obj("recipe")
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_invalid_body(self, client):
        """
        Tests the POST method with invalid body
        """
        invalid = {"game": "kek"}
        resp = client.post(self.RESOURCE_URL, json=invalid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_invalid_name(self, client):
        """
        Tests the POST method using an object with invalid name.
        """
        valid = _get_obj("food_item")
        valid["name"] = ""
        # Name too short
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid["name"] = "E" * 129
        # Name too long
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_invalid_emission(self, client):
        """
        Tests the POST method using an object with invalid emission value.
        """
        valid = _get_obj("food_item")
        valid['emission_per_kg'] = "CO2"  # Invalid type
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid['emission_per_kg'] = -1.0  # Invalid value
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)


class TestFoodItemResource(object):

    RESOURCE_URL = "/api/food-items/1/"
    INVALID_RESOURCE_URL = "/api/food-items/lalilulelo/"

    def test_get(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work.
        """
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method_redirect("profile", client, body)
        _check_control_get_method("self", client, body)
        _check_control_put_method("edit", client, body, "food_item")
        _check_control_post_method("clicook:add-food-item-equivalent", client, body, "food_item_equivalent")
        _check_control_delete_method("clicook:delete", client, body)
        assert "name" in body
        assert "id" in body
        assert "emission_per_kg" in body
        # TODO: Check items controls once ingredients are done
        assert "items" in body

    def test_get_not_found(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.
        """
        resp = client.get(self.INVALID_RESOURCE_URL)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_valid(self, client):
        """
        Tests the PUT method using a valid object.
        """
        valid = _get_obj("food_item")
        valid["id"] = 1
        new_name = "new_name"
        valid["name"] = new_name
        # test with valid and see that it exists afterward
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        resource_url = self.RESOURCE_URL
        assert resp.headers["Location"].endswith(resource_url)
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["name"] == new_name

    def test_put_not_found(self, client):
        """
        Test the PUT method with invalid resource url
        """
        valid = _get_obj('food_item')
        valid['id'] = 1
        resp = client.put(self.INVALID_RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_conflict(self, client):
        """
        Tests the PUT method using a object with conflicting id.
        """
        valid = _get_obj("food_item")
        valid["id"] = 2
        # test with valid and see that it exists afterward
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_content_type(self, client):
        """
        Tests the PUT with wrong content type.
        """
        valid = _get_obj("food_item")
        # test with valid and see that it exists afterward
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_content_name(self, client):
        """
        Tests the PUT method using an object with invalid name.
        """
        valid = _get_obj("food_item")
        valid["name"] = ""
        valid["id"] = 1
        # Name too short
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid["name"] = "E" * 129
        # Name too long
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_missing_fields(self, client):
        """
        Tests the PUT method using an object with invalid name.
        """
        valid = _get_obj("food_item")
        valid["id"] = 1
        valid.pop('name')
        # Name too short
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid = _get_obj("food_item")
        valid["id"] = 1
        valid.pop('emission_per_kg')
        # Name too short
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_id(self, client):
        """
        Tests the PUT method using an object with invalid id.
        """
        valid = _get_obj("food_item")
        valid["id"] = -1000
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_emission(self, client):
        """
        Tests the PUT method using an object with invalid emission.
        """
        valid = _get_obj("food_item")
        valid["emission_per_kg"] = "CO2"  # Invalid type
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid = _get_obj("food_item")
        valid["emission_per_kg"] = -100.0  # Invalid value
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_delete(self, client):
        """
        Tests the DELETE method using an valid id.
        """
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404

    def test_delete_not_found(self, client):
        """
        Tests the DELETE method using an invalid id.
        """
        resp = client.delete(self.INVALID_RESOURCE_URL)
        assert resp.status_code == 404

    def test_post_valid(self, client):
        """
        Test add-food-item-equivalent with valid equivalent object
        """
        valid = _get_obj("food_item_equivalent")
        valid['food_item_id'] = 1
        valid['unit_type'] = "millileter"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["unit_type"] == "millileter"
        _check_control_get_method_redirect("profile", client, body)

    def test_post_invalid_content_type(self, client):
        """
        Test add-food-item-equivalent with an invalid content type
        """
        valid = _get_obj("food_item_equivalent")
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_invalid_unit_type(self, client):
        """
        Test add-food-item-equivalent with a invalid unit type
        """
        valid = _get_obj("food_item_equivalent")
        valid['food_item_id'] = 1
        valid['unit_type'] = "kilogram"  # Unit type already reserved
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid = _get_obj("food_item_equivalent")
        valid['food_item_id'] = 1
        valid['unit_type'] = "lalilulelo"  # Invalid value for unit type
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_invalid_conversion_factor(self, client):
        """
        Test add-food-item-equivalent with a invalid unit conversion factor
        """
        valid = _get_obj("food_item_equivalent")
        valid['food_item_id'] = 1
        valid['conversion_factor'] = "lalilulelo"  # Invalid type
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid = _get_obj("food_item_equivalent")
        valid['food_item_id'] = 1
        valid['conversion_factor'] = -1.0  # Invalid value
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_food_item_not_found(self, client):
        """
        Test add-food-item-equivalent with an invalid food item id
        """
        valid = _get_obj("food_item_equivalent")
        resp = client.post(self.INVALID_RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_post_food_item_missing_field(self, client):
        """
        Test add-food-item-equivalent with missing fields
        """
        valid = _get_obj("food_item_equivalent")
        valid.pop('unit_type')
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

        valid = _get_obj("food_item_equivalent")
        valid.pop('conversion_factor')
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)


class TestFoodItemEquivalentResource(object):

    RESOURCE_URL = "/api/food-items/1/equivalents/1/"
    INVALID_RESOURCE_URL = "/api/food-items/1/equivalents/lalilulelo"

    def test_get(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB population are present, and their controls.
        """
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        body.json.loads(resp.data)
        _check_namespace(client, body)
        _check_control_get_method("self", client, body)
        _check_control_post_method("edit", client, body, "ingredient")
        _check_control_delete_method("clicook:delete", client, body)

        assert "id" in body
        assert "food_item_id" in body
        assert "unit_type" in body
        assert "conversion_factor" in body

    def test_get_not_found(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.
        """
        resp = client.get(self.INVALID_RESOURCE_URL)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_valid(self, client):
        """
        Tests the PUT method using a valid object.
        """
        valid = _get_obj("food_item_equivalent")
        valid["id"] = 1
        new_conversion_factor = 1000.0
        valid["conversion_factor"] = new_conversion_factor
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        resource_url = self.RESOURCE_URL
        assert resp.headers["Location"].endswith(resource_url)
        resp = client.get(resp.headers["Location"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["conversion_factor"] == new_conversion_factor

    def test_put_not_found(self, client):
        """
        Test the PUT method with invalid resource url
        """
        valid = _get_obj("food_item_equivalent")
        valid["id"] = 1
        resp = client.put(self.INVALID_RESOURCE_URL, json=valid)
        assert resp.status_code == 404
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_conflict(self, client):
        """
        Tests the PUT method using a object with conflicting id.
        """
        valid = _get_obj("food_item_equivalent")
        valid["id"] = 2
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_content_type(self, client):
        """
        Tests the PUT with wrong content type.
        """
        valid = _get_obj("food_item_equivalent")
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_missing_fields(self, client):
        """
        Tests the PUT method using an object with missing food item id.
        """
        valid = _get_obj("food_item_equivalent")
        valid["id"] = 1
        valid.pop("food_item_id")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_id(self, client):
        """
        Tests the PUT method using an object with invalid id.
        """
        valid = _get_obj("food_item_equivalent")
        valid["id"] = -1000
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile". client, body)

    def test_put_invalid_food_item_id(self, client):
        """
        Tests the PUT method using an object with invalid food item id.
        """
        valid = _get_obj("food_item_equivalent")
        valid["food_item_id"] = -1000
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile". client, body)

    def test_put_invalid_unit_type(self, client):
        """
        Tests the PUT method using an object with invalid unit type.
        """
        valid = _get_obj("food_item_equivalent")
        valid["unit_type"] = "lalilulelo"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_put_invalid_conversion_factor(self, client):
        """
        Tests the PUT method using an object with invalid conversion factor.
        """
        valid = _get_obj("food_item_equivalent")
        valid["conversion_factor"] = "lalilulelo"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        body = json.loads(resp.data)
        _check_control_get_method_redirect("profile", client, body)

    def test_delete(self, client):
        """
        Tests the DELETE method using an valid id.
        """
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404

    def test_delete_not_found(self, client):
        """
        Tests the DELETE method using an invalid id.
        """
        resp = client.delete(self.INVALID_RESOURCE_URL)
        assert resp.status_code == 404
