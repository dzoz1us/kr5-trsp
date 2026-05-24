from typing import Dict, List, Optional
from app.schemas import Task

class TaskStorage:
    def __init__(self):
        self._tasks: Dict[int, Task] = {}
        self._next_id: int = 1

    def create(self, task_data: dict, owner_id: int) -> Task:
        task = Task(id=self._next_id, owner_id=owner_id, **task_data)
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def get_all(self, owner_id: int, status: Optional[str] = None, min_priority: Optional[int] = None) -> List[Task]:
        tasks = [t for t in self._tasks.values() if t.owner_id == owner_id]
        if status:
            tasks = [t for t in tasks if t.status == status]
        if min_priority:
            tasks = [t for t in tasks if t.priority >= min_priority]
        return tasks

    def get_by_id(self, task_id: int, owner_id: int) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if task and task.owner_id == owner_id:
            return task
        return None

    def update_status(self, task_id: int, owner_id: int, new_status: str) -> Optional[Task]:
        task = self.get_by_id(task_id, owner_id)
        if task:
            # Создаём обновлённую задачу
            updated_data = task.model_dump()
            updated_data['status'] = new_status
            updated_task = Task(**updated_data)
            self._tasks[task_id] = updated_task
            return updated_task
        return None

    def delete(self, task_id: int, owner_id: int) -> bool:
        task = self.get_by_id(task_id, owner_id)
        if task:
            del self._tasks[task_id]
            return True
        return False

    def delete_by_admin(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def get_stats(self) -> dict:
        status_counts = {"todo": 0, "in_progress": 0, "done": 0}
        for task in self._tasks.values():
            status_counts[task.status] += 1
        return {
            "total_tasks": len(self._tasks),
            "by_status": status_counts
        }

# Глобальный экземпляр
storage = TaskStorage()