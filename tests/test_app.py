import os
import sys
import pytest
import time

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
    assert resp.get_json()["done"] is True


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

def test_filter_tasks_by_done_true(client):
    resp1 = client.post("/tasks", json={"title": "Задача 1"})
    assert resp1.status_code == 201
    task1_id = resp1.json["id"]
    
    resp2 = client.post("/tasks", json={"title": "Задача 2"})
    assert resp2.status_code == 201
    task2_id = resp2.json["id"]
    
    resp_update = client.put(f"/tasks/{task2_id}", json={"done": True})
    assert resp_update.status_code == 200
    
    resp = client.get("/tasks?done=true")
    assert resp.status_code == 200
    
    tasks = resp.json
    assert len(tasks) == 1
    assert tasks[0]["id"] == task2_id
    assert tasks[0]["done"] is True


def test_filter_tasks_by_done_false(client):
    resp1 = client.post("/tasks", json={"title": "Задача 1"})
    assert resp1.status_code == 201
    task1_id = resp1.json["id"]
    
    resp2 = client.post("/tasks", json={"title": "Задача 2"})
    assert resp2.status_code == 201
    task2_id = resp2.json["id"]
    
    # Через PUT пометить задачу 2 выполненной
    resp_update = client.put(f"/tasks/{task2_id}", json={"done": True})
    assert resp_update.status_code == 200
    
    # GET /tasks?done=false
    resp = client.get("/tasks?done=false")
    assert resp.status_code == 200
    
    # Проверить: в ответе только задача 1
    tasks = resp.json
    assert len(tasks) == 1
    assert tasks[0]["id"] == task1_id
    assert tasks[0]["done"] is False


def test_filter_tasks_no_filter(client):
    # Создать задачу 1 (не выполнена)
    resp1 = client.post("/tasks", json={"title": "Задача 1"})
    assert resp1.status_code == 201
    task1_id = resp1.json["id"]
    
    # Создать задачу 2
    resp2 = client.post("/tasks", json={"title": "Задача 2"})
    assert resp2.status_code == 201
    task2_id = resp2.json["id"]
    
    # Через PUT пометить задачу 2 выполненной
    resp_update = client.put(f"/tasks/{task2_id}", json={"done": True})
    assert resp_update.status_code == 200
    
    # GET /tasks (без фильтра)
    resp = client.get("/tasks")
    assert resp.status_code == 200
    
    # Проверить: в ответе обе задачи
    tasks = resp.json
    assert len(tasks) == 2
    task_ids = [task["id"] for task in tasks]
    assert task1_id in task_ids
    assert task2_id in task_ids

def test_get_task_returns_boolean_done(client):
    # Создать задачу
    resp = client.post("/tasks", json={"title": "Тестовая задача"})
    assert resp.status_code == 201
    task_id = resp.json["id"]
    
    # Получить задачу через GET /tasks/<id>
    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    
    # Проверить, что done - это булево значение False, а не 0
    task = resp.json
    assert task["done"] is False
    assert isinstance(task["done"], bool)


def test_update_task_returns_boolean_done(client):
    # Создать задачу
    resp = client.post("/tasks", json={"title": "Тестовая задача"})
    assert resp.status_code == 201
    task_id = resp.json["id"]
    
    # Обновить задачу через PUT, установив done=True
    resp = client.put(f"/tasks/{task_id}", json={"done": True})
    assert resp.status_code == 200
    
    # Проверить, что в ответе done - это булево значение True, а не 1
    task = resp.json
    assert task["done"] is True
    assert isinstance(task["done"], bool)
    
    # Дополнительная проверка: получить задачу через GET и убедиться
    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json["done"] is True

def test_stats_with_empty_database(client):
    resp = client.get("/tasks/stats")
    assert resp.status_code == 200
    assert resp.json == {"total": 0, "done": 0, "pending": 0}
    
    
def test_stats_with_mixed_database(client):    
    resp1 = client.post("/tasks", json={"title": "Задача 1"})
    assert resp1.status_code == 201
    
    resp2 = client.post("/tasks", json={"title": "Задача 2"})
    assert resp2.status_code == 201
    task2_id = resp2.json["id"]

    resp3 = client.post("/tasks", json={"title": "Задача 3"})
    assert resp3.status_code == 201
    
    resp_update = client.put(f"/tasks/{task2_id}", json={"done": True})
    assert resp_update.status_code == 200
    
    resp = client.get("/tasks/stats")
    assert resp.status_code == 200
    assert resp.json == {"total": 3, "done": 1, "pending": 2}    

def test_all_tasks_completed(client):    
    task_ids = []
    resp1 = client.post("/tasks", json={"title": "Задача 1"})
    assert resp1.status_code == 201
    task1_id = resp1.json["id"]

    resp_update = client.put(f"/tasks/{task1_id}", json={"done": True})
    assert resp_update.status_code == 200
    
    resp2 = client.post("/tasks", json={"title": "Задача 2"})
    assert resp2.status_code == 201
    task2_id = resp2.json["id"]

    resp3 = client.post("/tasks", json={"title": "Задача 3"})
    assert resp3.status_code == 201
    task3_id = resp3.json["id"]

    task_ids.append(task1_id)
    task_ids.append(task2_id)
    task_ids.append(task3_id)
    
    resp = client.post("/tasks/complete-all")
    assert resp.status_code == 200
    for task in resp.json:
        assert task["done"] is True

def test_all_tasks_completed_empty_base(client):    
    resp = client.post("/tasks/complete-all")
    assert resp.status_code == 200
    assert resp.json == []

def test_garbage_in_done_status(client):    
    resp1 = client.post("/tasks", json={"title": "Задача 1"})
    assert resp1.status_code == 201
    task1_id = resp1.json["id"]

    resp_update = client.put(f"/tasks/{task1_id}", json={"done": True})
    assert resp_update.status_code == 200
    
    resp2 = client.post("/tasks", json={"title": "Задача 2"})
    assert resp2.status_code == 201
    task2_id = resp2.json["id"]

    resp_update = client.put(f"/tasks/{task2_id}", json={"done": "yes"})
    assert resp_update.status_code == 400

    resp3 = client.post("/tasks", json={"title": "Задача 3"})
    assert resp3.status_code == 201
    task3_id = resp3.json["id"]

    resp_update = client.put(f"/tasks/{task3_id}", json={"done": 123})
    assert resp_update.status_code == 400

    resp4 = client.post("/tasks", json={"title": "Задача 4"})
    assert resp4.status_code == 201
    task4_id = resp4.json["id"]

    resp_update = client.put(f"/tasks/{task4_id}")
    assert resp_update.status_code == 200

def test_sort_tasks_by_date_created(client):
    resp1 = client.post("/tasks", json={"title": "Задача 1"})
    task1_id = resp1.json["id"]

    time.sleep(0.1)
    
    resp2 = client.post("/tasks", json={"title": "Задача 2"})
    task2_id = resp2.json["id"]

    time.sleep(0.1)
    
    resp3 = client.post("/tasks", json={"title": "Задача 3"})
    task3_id = resp3.json["id"]
    
    resp = client.get("/tasks?sort=created_at")
    tasks = resp.json
    assert [t["id"] for t in tasks] == [task1_id, task2_id, task3_id]

def test_sort_tasks_by_date_created_desc(client):
    resp1 = client.post("/tasks", json={"title": "Задача 1"})
    task1_id = resp1.json["id"]

    time.sleep(0.1)
    
    resp2 = client.post("/tasks", json={"title": "Задача 2"})
    task2_id = resp2.json["id"]

    time.sleep(0.1)
    
    resp3 = client.post("/tasks", json={"title": "Задача 3"})
    task3_id = resp3.json["id"]
    
    resp = client.get("/tasks?sort=-created_at")
    tasks = resp.json
    assert [t["id"] for t in tasks] == [task3_id, task2_id, task1_id]

def test_create_task_with_too_long_title(client):
    resp = client.post("/tasks", json={"title": "a" * 101})
    assert resp.status_code == 400
    resp = client.post("/tasks", json={"title": "a" * 100})
    assert resp.status_code == 201
    resp = client.post("/tasks", json={"title": "a" * 10})
    assert resp.status_code == 201