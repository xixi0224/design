from fastapi import APIRouter, HTTPException, Query
from typing import List
from app.schemas.study_analysis import StudyRecordCreate, StudyRecordResponse, ExamPointHeatResponse, StudyPlanCreate, StudyPlanResponse, StudyTrendResponse
from app.services.study_service import create_study_record, get_study_records, get_exam_point_heat, create_study_plan, get_study_plans, get_study_trends

router = APIRouter(tags=["study_analysis"])

@router.post("/study-record", response_model=StudyRecordResponse)
async def create_study_record_endpoint(record: StudyRecordCreate):
    try:
        return create_study_record(record)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学习记录创建失败: {str(e)}")

@router.get("/study-records/{user_id}", response_model=List[StudyRecordResponse])
async def get_study_records_endpoint(user_id: int):
    try:
        return get_study_records(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习记录失败: {str(e)}")

@router.get("/exam-points/heat", response_model=List[ExamPointHeatResponse])
async def get_exam_point_heat_endpoint():
    try:
        return get_exam_point_heat()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取考点热度失败: {str(e)}")

@router.post("/study-plans", response_model=StudyPlanResponse)
async def create_study_plan_endpoint(plan: StudyPlanCreate):
    try:
        return create_study_plan(plan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学习计划创建失败: {str(e)}")

@router.get("/study-plans/{user_id}", response_model=List[StudyPlanResponse])
async def get_study_plans_endpoint(user_id: int):
    try:
        return get_study_plans(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习计划失败: {str(e)}")

@router.get("/study-trends/{user_id}", response_model=StudyTrendResponse)
async def get_study_trends_endpoint(user_id: int, days: int = 30):
    try:
        return get_study_trends(user_id, days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习趋势失败: {str(e)}")