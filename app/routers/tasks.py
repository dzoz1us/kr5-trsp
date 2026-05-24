from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from app.schemas import TaskCreate, TaskStatusUpdate, Task
from app.dependencies import get_current_user, get_storage
from app.storage import TaskStorage

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage)
):
    return storage.create(task_data.model_dump(), current_user.id)

@router.get("", response_model=list[Task])
async def get_tasks(
    status: Optional[str] = Query(None, pattern="^(todo|in_progress|done)$"),
    min_priority: Optional[int] = Query(None, ge=1, le=5),
    current_user = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage)
):
    return storage.get_all(current_user.id, status, min_priority)

@router.get("/{task_id}", response_model=Task)
async def get_task(
    task_id: int,
    current_user = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage)
):
    task = storage.get_by_id(task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.patch("/{task_id}/status", response_model=Task)
async def update_task_status(
    task_id: int,
    update: TaskStatusUpdate,
    current_user = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage)
):
    task = storage.update_status(task_id, current_user.id, update.status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage)
):
    if not storage.delete(task_id, current_user.id):
        raise HTTPException(status_code=404, detail="Task not found")