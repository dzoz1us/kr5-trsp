from pydantic import BaseModel, Field, field_validator
from typing import Optional

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    description: Optional[str] = None
    status: str = Field(..., pattern="^(todo|in_progress|done)$")
    priority: int = Field(..., ge=1, le=5)

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('title cannot be empty')
        return v

class Task(TaskCreate):
    id: int
    owner_id: int

class TaskStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(todo|in_progress|done)$")

class User(BaseModel):
    id: int
    role: str