import sys
import os

# Добавляем корневую директорию в путь Python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.storage import storage

@pytest.fixture
def client():
    """Фикстура для очистки хранилища перед каждым тестом"""
    storage._tasks.clear()
    storage._next_id = 1
    return TestClient(app)


# 1. /users/me возвращает текущего пользователя
def test_users_me_returns_current_user(client):
    response = client.get("/users/me", headers={"X-User-Id": "10"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 10
    assert data["role"] == "user"


def test_users_me_with_admin_role(client):
    response = client.get("/users/me", headers={"X-User-Id": "10", "X-User-Role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 10
    assert data["role"] == "admin"


# 2. Пользователь без заголовка X-User-Id получает 401
def test_no_x_user_id_returns_401(client):
    response = client.get("/users/me")
    assert response.status_code == 401
    assert "X-User-Id" in response.json()["detail"]


def test_invalid_x_user_id_returns_401(client):
    response = client.get("/users/me", headers={"X-User-Id": "not_a_number"})
    assert response.status_code == 401


# 3. Обычный пользователь получает 403 при обращении к /admin/stats
def test_regular_user_cannot_access_admin_stats(client):
    response = client.get("/admin/stats", headers={"X-User-Id": "10"})
    assert response.status_code == 403
    assert "Admin access required" in response.json()["detail"]


def test_regular_user_cannot_access_admin_delete(client):
    # Сначала создаём задачу
    client.post("/tasks", json={"title": "Test task", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    
    # Пытаемся удалить через админский эндпоинт как обычный пользователь
    response = client.delete("/admin/tasks/1", headers={"X-User-Id": "10"})
    assert response.status_code == 403


# 4. Администратор получает статистику по всем задачам
def test_admin_can_access_stats(client):
    # Создаём задачи для разных пользователей
    client.post("/tasks", json={"title": "Task 1", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    client.post("/tasks", json={"title": "Task 2", "status": "in_progress", "priority": 4}, headers={"X-User-Id": "20"})
    client.post("/tasks", json={"title": "Task 3", "status": "done", "priority": 5}, headers={"X-User-Id": "10"})
    
    response = client.get("/admin/stats", headers={"X-User-Id": "10", "X-User-Role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 3
    assert data["by_status"]["todo"] == 1
    assert data["by_status"]["in_progress"] == 1
    assert data["by_status"]["done"] == 1


def test_admin_stats_empty_storage(client):
    response = client.get("/admin/stats", headers={"X-User-Id": "10", "X-User-Role": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 0
    assert data["by_status"]["todo"] == 0


# 5. Обычный пользователь не может удалить чужую задачу через /tasks/{task_id}
def test_regular_user_cannot_delete_others_task(client):
    # Пользователь 10 создаёт задачу
    create_resp = client.post("/tasks", json={"title": "User 10 task", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]
    
    # Пользователь 20 пытается удалить задачу пользователя 10
    response = client.delete(f"/tasks/{task_id}", headers={"X-User-Id": "20"})
    assert response.status_code == 404  # Задача не найдена для этого пользователя


def test_regular_user_can_delete_own_task(client):
    # Пользователь 10 создаёт задачу
    create_resp = client.post("/tasks", json={"title": "User 10 task", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]
    
    # Пользователь 10 удаляет свою задачу
    response = client.delete(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert response.status_code == 204


# 6. Администратор может удалить чужую задачу через /admin/tasks/{task_id}
def test_admin_can_delete_any_task(client):
    # Пользователь 10 создаёт задачу
    create_resp = client.post("/tasks", json={"title": "User 10 task", "status": "todo", "priority": 3}, headers={"X-User-Id": "10"})
    task_id = create_resp.json()["id"]
    
    # Администратор удаляет задачу пользователя 10
    response = client.delete(f"/admin/tasks/{task_id}", headers={"X-User-Id": "1", "X-User-Role": "admin"})
    assert response.status_code == 204
    
    # Проверяем, что задачи больше нет
    get_resp = client.get(f"/tasks/{task_id}", headers={"X-User-Id": "10"})
    assert get_resp.status_code == 404


def test_admin_delete_nonexistent_task_404(client):
    response = client.delete("/admin/tasks/999", headers={"X-User-Id": "1", "X-User-Role": "admin"})
    assert response.status_code == 404


# 7. Дополнительные тесты для пользователей
def test_get_user_by_id(client):
    response = client.get("/users/42", headers={"X-User-Id": "10"})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 42
    assert data["role"] == "user"


# 8. Проверка маршрутов в Swagger (структурно)
def test_routers_are_registered(client):
    # Проверяем, что эндпоинты существуют
    response = client.get("/users/me", headers={"X-User-Id": "10"})
    assert response.status_code == 200
    
    response = client.get("/tasks", headers={"X-User-Id": "10"})
    assert response.status_code == 200
    
    # Проверяем, что админский эндпоинт требует авторизацию
    response = client.get("/admin/stats")
    assert response.status_code == 401  # Требует X-User-Id