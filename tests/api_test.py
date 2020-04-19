import json
import os
import tempfile
import random

import pytest
from jsonschema import validate


from climatecook import create_app, db
from climatecook.models import Recipe, FoodItem

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

        i = FoodItem(
            id=i,
            name="test-food-item-{}".format(i),
            emission_per_kg=float(i),
        )
        db.session.add(i)
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
            "emission_per_kg": float(i)
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
        _check_control_delete_method("clicook:delete", client, body)
        # TODO: Check control for add ingredient once ingredients are implemented.
        # _check_control_post_method("clicook:add-ingredient", client, body)
        assert "name" in body
        assert "id" in body
        assert "emissions_total" in body
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
