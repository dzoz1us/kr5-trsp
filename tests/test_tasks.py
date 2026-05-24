import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import storage
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def client():
    """Фикстура для очистки хранилища перед каждым тестом"""
    storage._tasks.clear()
    storage._next_id = 1
    return TestClient(app)

# ========== 1. Успешное создание задачи ==========
def test_create_task_success(client):
    response = client.post(
        "/tasks",
        json={"title": "Тестовая задача", "description": "Описание", "status": "todo", "priority": 3},
        headers={"X-User-Id": "10"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Тестовая задача"
    assert data["owner_id"] == 10
    assert "id" in data

# ========== 2. Ошибка 422, если title короче 3 символов ==========
def test_create_task_title_too_short(client):
    response = client.post(
        "/tasks",
        json={"title": "ab", "status": "todo", "priority": 3},
        headers={"X-User-Id": "10"}
    )
    assert response.status_code == 422

# ========== 3. Ошибка 401, если нет заголовка X-User-Id ==========
def test_create_task_no_auth(client):
    response = client.post(
        "/tasks",
        json={"title": "Тест", "status": "todo", "priority": 3}
    )
    assert response.status_code == 401

# ========== 4. Пользователь видит только свои задачи ==========
def test_user_sees_only_own_tasks(client):
    # Создаём задачи для разных пользователей
    client.post("/tasks", json={"title": "Task User 10", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    client.post("/tasks", json={"title": "Task User 20", "status": "todo", "priority": 3}, headers={"X-User-Id": "20"})
    client.post("/tasks", json={"title": "Task User 10 #2", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    
    response = client.get("/tasks", headers={"X-User-Id": "10"})
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 2
    for task in tasks:
        assert task["owner_id"] == 10

# ========== 5. Фильтрация задач по status и min_priority ==========
def test_filter_tasks_by_status_and_priority(client):
    # Создаём задачи с разными параметрами
    client.post("/tasks", json={"title": "Low priority todo", "status": "todo", "priority": 1}, headers={"X-User-Id": "10"})
    client.post("/tasks", json={"title": "High priority done", "status": "done", "priority": 5}, headers={"X-User-Id": "10"})
    client.post("/tasks", json={"title": "Medium priority todo", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    
    # Фильтр по статусу
    response = client.get("/tasks?status=todo", headers={"X-User-Id": "10"})
    tasks = response.json()
    assert len(tasks) == 2
    assert all(t["status"] == "todo" for t in tasks)
    
    # Фильтр по минимальному приоритету
    response = client.get("/tasks?min_priority=3", headers={"X-User-Id": "10"})
    tasks = response.json()
    assert len(tasks) == 2
    assert all(t["priority"] >= 3 for t in tasks)
    
    # Комбинированный фильтр
    response = client.get("/tasks?status=todo&min_priority=3", headers={"X-User-Id": "10"})
    tasks = response.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Medium priority todo"

# ========== 6. Успешное изменение статуса задачи ==========
def test_update_task_status_success(client):
    # Создаём задачу
    create_resp = client.post("/tasks", json={"title": "Task for status update", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]
    
    # Обновляем статус
    response = client.patch(f"/tasks/{task_id}/status", json={"status": "done"}, headers={"X-User-Id": "10"})
    assert response.status_code == 200
    assert response.json()["status"] == "done"
    
    # Проверяем, что статус действительно изменился
    get_resp = client.get(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert get_resp.json()["status"] == "done"

# ========== 7. Ошибка 404 при обращении к чужой или несуществующей задаче ==========
def test_access_others_task_404(client):
    # Создаём задачу для пользователя 10
    create_resp = client.post("/tasks", json={"title": "User 10 task", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]
    
    # Пользователь 20 пытается получить задачу пользователя 10
    response = client.get(f"/tasks/{task_id}", headers={"X-User-Id": "20"})
    assert response.status_code == 404
    
    # Несуществующая задача
    response = client.get("/tasks/999", headers={"X-User-Id": "10"})
    assert response.status_code == 404

# ========== 8. Успешное удаление задачи ==========
def test_delete_task_success(client):
    # Создаём задачу
    create_resp = client.post("/tasks", json={"title": "Task to delete", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]
    
    # Удаляем задачу
    response = client.delete(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert response.status_code == 204
    
    # Проверяем, что задачи больше нет
    get_resp = client.get(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert get_resp.status_code == 404

# ========== Дополнительно: Health check ==========
def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}