from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
import json
from app.db import get_conn
from app.services.learning_plan_service import generate_learning_plan_service

router = APIRouter(prefix="/learning-plan", tags=["learning-plan"])

@router.post("/generate")
async def generate_learning_plan(data: Dict[str, Any] = Body(...)):
    """
    生成学习计划
    examDate: 考试日期
    dailyHours: 每日可用时间
    pendingTasks: 待完成任务
    examSubject: 考试科目
    """
    try:
        exam_date = data.get("examDate")
        daily_hours = data.get("dailyHours")
        pending_tasks = data.get("pendingTasks", "")
        exam_subject = data.get("examSubject", "")
        
        if not exam_date or not daily_hours or not exam_subject:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 调用千问大模型生成学习计划
        plan_data = generate_learning_plan_service(
            exam_date=exam_date,
            daily_hours=daily_hours,
            pending_tasks=pending_tasks,
            exam_subject=exam_subject
        )
        
        # 保存学习计划到数据库
        conn = get_conn()
        cursor = conn.cursor()
        
        # 检查是否已有学习计划
        cursor.execute("SELECT id FROM zhinote_learning_plans LIMIT 1")
        existing_plan = cursor.fetchone()
        
        if existing_plan:
            # 更新现有计划
            cursor.execute(
                """
                UPDATE zhinote_learning_plans
                SET exam_date = %s, daily_hours = %s, pending_tasks = %s, exam_subject = %s, plan_data = %s, updated_at = NOW()
                WHERE id = %s
                """,
                (exam_date, daily_hours, pending_tasks, exam_subject, json.dumps(plan_data), existing_plan[0])
            )
        else:
            # 插入新计划
            cursor.execute(
                """
                INSERT INTO zhinote_learning_plans (exam_date, daily_hours, pending_tasks, exam_subject, plan_data, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (exam_date, daily_hours, pending_tasks, exam_subject, json.dumps(plan_data))
            )
            plan_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
        conn.close()
        
        # 计算剩余天数
        from datetime import datetime
        exam_date_str = exam_date.strftime("%Y-%m-%d") if hasattr(exam_date, 'strftime') else str(exam_date)
        exam_datetime = datetime.strptime(exam_date_str, "%Y-%m-%d")
        today = datetime.now()
        remaining_days = (exam_datetime - today).days
        
        return {
            "code": 0,
            "data": {
                "planData": plan_data,
                "remainingDays": remaining_days,
                "totalProgress": 0
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成学习计划失败: {str(e)}")

@router.get("/get")
async def get_learning_plan():
    """
    获取学习计划
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, exam_date, daily_hours, pending_tasks, exam_subject, plan_data, created_at, updated_at
            FROM zhinote_learning_plans
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if not row:
            return {
                "code": 0,
                "data": {
                    "hasPlan": False
                }
            }
        
        plan_id, exam_date, daily_hours, pending_tasks, exam_subject, plan_data_str, created_at, updated_at = row
        
        # 解析计划数据
        plan_data = json.loads(plan_data_str) if plan_data_str else []
        
        # 计算剩余天数
        from datetime import datetime
        exam_date_str = exam_date.strftime("%Y-%m-%d") if hasattr(exam_date, 'strftime') else str(exam_date)
        exam_datetime = datetime.strptime(exam_date_str, "%Y-%m-%d")
        today = datetime.now()
        remaining_days = (exam_datetime - today).days
        
        # 计算总进度 & 今日任务 & 修正星期
        total_tasks = 0
        completed_tasks = 0
        today_tasks = []
        today_str = datetime.now().strftime('%Y-%m-%d')
        weekday_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
        for day in plan_data:
            # 动态更新status：今天的标记为today
            if day.get("date") == today_str:
                day["status"] = "today"
            # 修正星期：用代码计算覆盖可能错误的值
            if day.get("date"):
                try:
                    d = datetime.strptime(day["date"], "%Y-%m-%d")
                    day["weekday"] = weekday_map[d.weekday()]
                except:
                    pass
            for task in day.get("tasks", []):
                # 字段兼容：确保任务有name字段
                if "name" not in task or not task["name"]:
                    task["name"] = task.get("content", task.get("title", task.get("task", "未命名任务")))
                total_tasks += 1
                if task.get("completed", False):
                    completed_tasks += 1
            # 提取今日任务
            if day.get("date") == today_str:
                today_tasks = day.get("tasks", [])

        total_progress = round((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

        return {
            "code": 0,
            "data": {
                "hasPlan": True,
                "planData": plan_data,
                "remainingDays": remaining_days,
                "totalProgress": total_progress,
                "todayTasks": today_tasks,
                "examSubject": exam_subject
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取学习计划失败: {str(e)}")

@router.post("/save-progress")
async def save_progress(data: Dict[str, Any] = Body(...)):
    """
    保存学习计划进度
    planData: 计划数据
    totalProgress: 总进度
    """
    try:
        plan_data = data.get("planData")
        total_progress = data.get("totalProgress")
        
        if not plan_data:
            raise HTTPException(status_code=400, detail="缺少计划数据")
        
        # 更新数据库中的计划数据
        conn = get_conn()
        cursor = conn.cursor()
        
        # 先获取计划ID
        cursor.execute(
            """
            SELECT id FROM zhinote_learning_plans
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="学习计划不存在")
        
        plan_id = row[0]
        
        cursor.execute(
            """
            UPDATE zhinote_learning_plans
            SET plan_data = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (json.dumps(plan_data), plan_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "code": 0,
            "data": {
                "success": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存进度失败: {str(e)}")

@router.post("/toggle-task")
async def toggle_task(data: Dict[str, Any] = Body(...)):
    """
    切换任务完成状态
    date: 日期
    taskId: 任务ID
    """
    try:
        date = data.get("date")
        task_id = data.get("taskId")
        
        if not date or task_id is None:
            raise HTTPException(status_code=400, detail="缺少必要参数")
        
        # 获取当前计划
        conn = get_conn()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, plan_data FROM zhinote_learning_plans
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="学习计划不存在")
        
        plan_id = row[0]
        import json
        plan_data = json.loads(row[1])
        
        # 查找并切换任务状态
        for day in plan_data:
            if day.get("date") == date:
                for task in day.get("tasks", []):
                    if task.get("id") == task_id:
                        task["completed"] = not task.get("completed", False)
                        break
                break
        
        # 更新数据库
        cursor.execute(
            """
            UPDATE zhinote_learning_plans
            SET plan_data = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (json.dumps(plan_data), plan_id)
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "code": 0,
            "data": {
                "success": True
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换任务状态失败: {str(e)}")
