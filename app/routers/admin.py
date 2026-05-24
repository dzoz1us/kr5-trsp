from fastapi import APIRouter, Depends, HTTPException, status
from app.dependencies import require_admin, get_storage
from app.storage import TaskStorage

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/stats")
async def get_stats(
    admin = Depends(require_admin),
    storage: TaskStorage = Depends(get_storage)
):
    return storage.get_stats()

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_task(
    task_id: int,
    admin = Depends(require_admin),
    storage: TaskStorage = Depends(get_storage)
):
    if not storage.delete_by_admin(task_id):
        raise HTTPException(status_code=404, detail="Task not found")