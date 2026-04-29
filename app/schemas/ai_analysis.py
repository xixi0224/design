from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel

class AnalysisRequest(BaseModel):
    source_id: int
    source_type: str
    analysis_type: str

class AnalysisResponse(BaseModel):
    id: int
    source_id: int
    source_type: str
    analysis_type: str
    result: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class ASRRequest(BaseModel):
    audio_id: int

class ASRResponse(BaseModel):
    audio_id: int
    text: str
    status: str

class SummaryResponse(BaseModel):
    doc_id: int
    summary: str
    keywords: List[str]

class ExamPointResponse(BaseModel):
    doc_id: int
    exam_points: List[Dict[str, Any]]