from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import List
from app.schemas.study_assist import ExportRequest, ExportResponse, ReminderCreate, ReminderResponse, TimerRequest, TimerResponse, PomodoroRequest, PomodoroResponse, PomodoroCompleteRequest, PomodoroCompleteResponse, UnitConvertRequest, UnitConvertResponse, SchoolRecommendationRequest, SchoolRecommendationResponse
from app.services.assist_service import export_note, get_export_records, create_reminder, get_reminders, update_reminder_status, start_timer, start_pomodoro, complete_pomodoro, convert_unit, recommend_schools

router = APIRouter(tags=["study_assist"])

@router.post("/export", response_model=ExportResponse)
async def export_note_endpoint(request: ExportRequest):
    try:
        return export_note(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")

@router.get("/export/{note_id}", response_model=list[ExportResponse])
async def get_export_records_endpoint(note_id: int):
    try:
        return get_export_records(note_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取导出记录失败: {str(e)}")

@router.post("/reminders", response_model=ReminderResponse)
async def create_reminder_endpoint(reminder: ReminderCreate):
    try:
        return create_reminder(reminder)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建提醒失败: {str(e)}")

@router.get("/reminders/{user_id}", response_model=List[ReminderResponse])
async def get_reminders_endpoint(user_id: int):
    try:
        return get_reminders(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取提醒失败: {str(e)}")

@router.put("/reminders/{reminder_id}/status")
async def update_reminder_status_endpoint(reminder_id: int, is_completed: bool):
    try:
        return update_reminder_status(reminder_id, is_completed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新提醒状态失败: {str(e)}")

@router.post("/tools/timer", response_model=TimerResponse)
async def start_timer_endpoint(request: TimerRequest):
    try:
        return start_timer(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动计时器失败: {str(e)}")

@router.post("/tools/pomodoro", response_model=PomodoroResponse)
async def start_pomodoro_endpoint(request: PomodoroRequest):
    try:
        return start_pomodoro(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动番茄钟失败: {str(e)}")


@router.post("/tools/pomodoro/complete", response_model=PomodoroCompleteResponse)
async def complete_pomodoro_endpoint(request: PomodoroCompleteRequest):
    """
    番茄钟完成时调用，自动记录学习时长
    """
    try:
        result = complete_pomodoro(
            duration=request.duration,
            user_id=request.user_id
        )
        
        if result["success"]:
            return PomodoroCompleteResponse(
                success=True,
                message=result["message"],
                duration=result["duration"],
                total_today=result["total_today"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"记录番茄钟失败: {str(e)}")

@router.post("/tools/unit-convert", response_model=UnitConvertResponse)
async def convert_unit_endpoint(request: UnitConvertRequest):
    try:
        return convert_unit(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"单位转换失败: {str(e)}")

@router.post("/schools/recommend", response_model=SchoolRecommendationResponse)
async def recommend_schools_endpoint(request: SchoolRecommendationRequest):
    try:
        return recommend_schools(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学校推荐失败: {str(e)}")