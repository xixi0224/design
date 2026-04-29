from datetime import datetime
from typing import List
from pydantic import BaseModel

class ExportRequest(BaseModel):
    note_id: int
    export_type: str

class ExportResponse(BaseModel):
    id: int
    note_id: int
    export_type: str
    export_path: str
    created_at: datetime

    class Config:
        from_attributes = True

class ReminderCreate(BaseModel):
    user_id: int
    title: str
    content: str
    reminder_time: datetime

class ReminderResponse(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    reminder_time: datetime
    is_completed: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TimerRequest(BaseModel):
    duration: int  # 倒计时时长（秒）
    title: str = "学习倒计时"

class TimerResponse(BaseModel):
    success: bool
    message: str
    duration: int

class PomodoroRequest(BaseModel):
    work_duration: int = 25  # 工作时长（分钟）
    break_duration: int = 5  # 休息时长（分钟）
    cycles: int = 4  # 循环次数

class PomodoroResponse(BaseModel):
    success: bool
    message: str
    work_duration: int
    break_duration: int
    cycles: int

class PomodoroCompleteRequest(BaseModel):
    duration: int  # 实际专注时长（分钟）
    user_id: int = 1  # 用户ID，暂时默认为1

class PomodoroCompleteResponse(BaseModel):
    success: bool
    message: str
    duration: int
    total_today: int  # 今日总学习时长

class UnitConvertRequest(BaseModel):
    value: float
    from_unit: str
    to_unit: str

class UnitConvertResponse(BaseModel):
    success: bool
    message: str
    original_value: float
    from_unit: str
    converted_value: float
    to_unit: str

class SchoolRecommendationRequest(BaseModel):
    user_id: int
    major: str
    score: int
    location: str = ""

class SchoolResponse(BaseModel):
    id: int
    name: str
    location: str
    ranking: int
    type: str
    min_score: int
    majors: str
    description: str

class SchoolRecommendationResponse(BaseModel):
    success: bool
    message: str
    recommendations: List[SchoolResponse]