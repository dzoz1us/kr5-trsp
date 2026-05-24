from fastapi import Header, HTTPException, Depends
from typing import Optional
from app.schemas import User
from app.storage import storage

async def get_current_user(
    x_user_id: Optional[str] = Header(None),
    x_user_role: str = Header("user")
) -> User:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="X-User-Id header required")
    try:
        user_id = int(x_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid X-User-Id")
    
    return User(id=user_id, role=x_user_role)

async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

def get_storage():
    return storage