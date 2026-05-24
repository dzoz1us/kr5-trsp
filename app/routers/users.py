from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas import User

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/{user_id}")
async def get_user(user_id: int, current_user: User = Depends(get_current_user)):
    return {"id": user_id, "role": "user"}