import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as app_module
import models


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    # чистим БД перед каждым тестом
    conn = models.get_connection()
    conn.execute("DELETE FROM tasks")
    conn.commit()
    conn.close()
    with app_module.app.test_client() as c:
        yield c


def test_create_and_list_task(client):
    resp = client.post("/tasks", json={"title": "Купить кофе для офиса"})
    assert resp.status_code == 201

    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 1


def test_get_single_task(client):
    created = client.post("/tasks", json={"title": "Настроить CI"}).get_json()
    resp = client.get(f"/tasks/{created['id']}")
    assert resp.status_code == 200
    assert resp.get_json()["title"] == "Настроить CI"


def test_get_missing_task_returns_404(client):
    resp = client.get("/tasks/9999")
    assert resp.status_code == 404


def test_update_task(client):
    created = client.post("/tasks", json={"title": "Написать доку"}).get_json()
    resp = client.put(f"/tasks/{created['id']}", json={"done": True})
    assert resp.status_code == 200
    assert resp.get_json()["done"] == 1


def test_delete_existing_task(client):
    created = client.post("/tasks", json={"title": "Временная задача"}).get_json()
    resp = client.delete(f"/tasks/{created['id']}")
    assert resp.status_code == 200

def test_delete_missing_task_return_404(client):   
    resp = client.delete("/tasks/9999")
    assert resp.status_code == 404

def test_create_task_without_title_fails(client):
    resp = client.post("/tasks", json={})
    assert resp.status_code == 400

def test_create_task_with_empty_title_fails(client):
    resp = client.post("/tasks", json={"title": ""})
    assert resp.status_code == 400

def test_create_task_with_whitespace_title_fails(client):
    resp = client.post("/tasks", json={"title": "   "})
    assert resp.status_code == 400

def test_create_task_with_valid_title_succeeds(client):
    resp = client.post("/tasks", json={"title": "нормальное название"})
    assert resp.status_code == 201