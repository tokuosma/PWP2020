import json
import os
import random
import tempfile

import pytest

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


class TestRecipeCollection(object):

    RESOURCE_URL = "/api/recipes/"

    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body["items"]) == 3
        for item in body["items"]:
            assert "name" in item
            