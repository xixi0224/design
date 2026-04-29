from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class AudioRecordCreate(BaseModel):
    course_id: int = 1

class AudioRecordResponse(BaseModel):
    id: int
    course_id: int
    filename: str
    duration: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class TextInputCreate(BaseModel):
    course_id: int = 1
    title: str
    content: str

class TextInputResponse(BaseModel):
    id: int
    course_id: int
    title: str
    content: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True