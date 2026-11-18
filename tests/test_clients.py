import unittest
from application import create_app
from extensions import db
from models import Client, Franchisee

class TestConfig:
    TESTING = True
    INITIALIZE_DATABASE = False
    SECRET_KEY = "isolated-test-only"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {}

class ClientCrudTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        with self.app.app_context():
            db.metadata.create_all(db.engine, tables=[Franchisee.__table__, Client.__table__])
            db.session.add_all([Franchisee(id=1, name="Franquiciado Principal"), Franchisee(id=2, name="Otra casa")])
            db.session.commit()
        self.client = self.app.test_client()

    def create(self, **values):
        return self.client.post("/api/clients", json={"name": "Cliente", **values})

    def test_create_update_read_and_soft_delete(self):
        response = self.create(name="  José 中文  ", active="false")
        self.assertEqual(201, response.status_code)
        item = response.get_json()
        self.assertEqual("José 中文", item["name"])
        self.assertFalse(item["active"])
        path = f"/api/clients/{item['id']}"
        self.assertTrue(self.client.put(path, json={"active": "true"}).get_json()["active"])
        self.assertEqual(200, self.client.get(path).status_code)
        self.assertFalse(self.client.delete(path).get_json()["active"])

    def test_false_strings_do_not_activate_records(self):
        item = self.create().get_json()
        path = f"/api/clients/{item['id']}"
        for value in (False, "false", "0", 0):
            response = self.client.put(path, json={"active": value})
            self.assertEqual(200, response.status_code)
            self.assertFalse(response.get_json()["active"])

    def test_invalid_payloads_return_json_errors(self):
        for payload in ([], "invalid", {"name": 12}, {"name": ""}, {"name": "x" * 201}, {"name": "X", "active": "maybe"}):
            response = self.client.post("/api/clients", json=payload)
            self.assertEqual(400, response.status_code)
            self.assertIn("error", response.get_json())

    def test_invalid_update_does_not_partially_change_a_client(self):
        item = self.create(name="Original").get_json()
        path = f"/api/clients/{item['id']}"
        response = self.client.put(path, json={"name": "Changed", "email": []})
        self.assertEqual(400, response.status_code)
        self.assertEqual("Original", self.client.get(path).get_json()["name"])

    def test_active_filter_is_validated(self):
        self.create(active=False)
        self.assertEqual(1, len(self.client.get("/api/clients?active=false").get_json()))
        self.assertEqual([], self.client.get("/api/clients?active=true").get_json())
        self.assertEqual(400, self.client.get("/api/clients?active=maybe").status_code)

    def test_other_franchisee_cannot_read_or_modify_a_client(self):
        item = self.create().get_json()
        with self.client.session_transaction() as session:
            session["franchisee_id"] = 2
        path = f"/api/clients/{item['id']}"
        self.assertEqual(404, self.client.get(path).status_code)
        self.assertEqual(404, self.client.put(path, json={"name": "Other"}).status_code)
        self.assertEqual(404, self.client.delete(path).status_code)

if __name__ == "__main__":
    unittest.main()
