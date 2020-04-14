import json
import os
import tempfile

import pytest
from jsonschema import validate


from climatecook import create_app, db
from climatecook.models import Recipe

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
    db.session.commit()


def _get_obj(obj_type):
    """
    Creates a valid JSON object of the desired type to be used for PUT and POST tests.
    """
    if(obj_type == "recipe"):
        return {
            "name": "test-recipe"
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
    body["name"] = obj["name"]
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
