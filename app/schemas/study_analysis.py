from datetime import datetime, date
from typing import List
from pydantic import BaseModel

class StudyRecordCreate(BaseModel):
    user_id: int
    note_id: int
    study_time: int

class StudyRecordResponse(BaseModel):
    id: int
    user_id: int
    note_id: int
    study_time: int
    last_study_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

class ExamPointHeatResponse(BaseModel):
    point_id: int
    content: str
    heat: int
    difficulty: str

class StudyPlanCreate(BaseModel):
    user_id: int
    title: str
    description: str
    start_date: date
    end_date: date
    target_hours: int

class StudyPlanResponse(BaseModel):
    id: int
    user_id: int
    title: str
    description: str
    start_date: date
    end_date: date
    target_hours: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StudyTrendDay(BaseModel):
    date: date
    study_time: int

class StudyTrendWeek(BaseModel):
    week_start: date
    week_end: date
    study_time: int

class StudyTrendMonth(BaseModel):
    month: str
    study_time: int

class StudyTrendResponse(BaseModel):
    daily_trends: List[StudyTrendDay]
    weekly_trends: List[StudyTrendWeek]
    monthly_trends: List[StudyTrendMonth]
    total_study_time: int
    average_daily_time: float