from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any
from app.db import get_conn
from datetime import datetime, timedelta

router = APIRouter(prefix="/study-stats", tags=["study-stats"])

@router.post("/check-in")
async def check_in(data: Dict[str, Any] = Body(...)):
    """
    学习打卡
    studyDuration: 学习时长（分钟）
    taskCount: 完成任务数
    """
    try:
        study_duration = data.get("studyDuration", 0)
        task_count = data.get("taskCount", 0)
        
        if study_duration <= 0:
            raise HTTPException(status_code=400, detail="学习时长必须大于0")
        
        conn = get_conn()
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 检查今天是否已有记录
        cursor.execute(
            """
            SELECT id, study_duration, review_count, task_count
            FROM zhinote_study_stats
            WHERE study_date = %s
            LIMIT 1
            """,
            (today,)
        )
        row = cursor.fetchone()
        
        if row:
            # 更新现有记录
            cursor.execute(
                """
                UPDATE zhinote_study_stats
                SET study_duration = study_duration + %s,
                    task_count = task_count + %s,
                    review_count = review_count + 1,
                    updated_at = NOW()
                WHERE id = %s
                """,
                (study_duration, task_count, row[0])
            )
        else:
            # 插入新记录
            cursor.execute(
                """
                INSERT INTO zhinote_study_stats (study_date, study_duration, review_count, task_count, created_at)
                VALUES (%s, %s, 1, %s, NOW())
                """,
                (today, study_duration, task_count)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "code": 0,
            "data": {
                "success": True,
                "message": "打卡成功"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"打卡失败: {str(e)}")

@router.get("/stats")
async def get_stats(days: int = 7):
    """
    获取学习统计数据
    days: 统计天数，默认7天
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # 计算开始日期
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        # 获取统计数据
        cursor.execute(
            """
            SELECT study_date, study_duration, review_count, task_count
            FROM zhinote_study_stats
            WHERE study_date >= %s
            ORDER BY study_date DESC
            """,
            (start_date,)
        )
        rows = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 计算总计数据
        total_duration = sum(row[1] for row in rows)
        total_reviews = sum(row[2] for row in rows)
        total_tasks = sum(row[3] for row in rows)
        
        # 构建每日数据
        daily_stats = []
        for row in rows:
            daily_stats.append({
                "date": row[0].strftime("%Y-%m-%d"),
                "studyDuration": row[1],
                "reviewCount": row[2],
                "taskCount": row[3]
            })
        
        return {
            "code": 0,
            "data": {
                "totalDuration": total_duration,
                "totalReviews": total_reviews,
                "totalTasks": total_tasks,
                "dailyStats": daily_stats
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计数据失败: {str(e)}")

@router.get("/summary")
async def get_summary():
    """
    获取学习统计摘要
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # 获取总学习时长（分钟）
        cursor.execute("SELECT COALESCE(SUM(study_duration), 0) FROM zhinote_study_stats")
        total_duration = cursor.fetchone()[0]
        
        # 获取总复习次数
        cursor.execute("SELECT COALESCE(SUM(review_count), 0) FROM zhinote_study_stats")
        total_reviews = cursor.fetchone()[0]
        
        # 获取真实笔记数量（从 zhinote_notes 表统计）
        cursor.execute("SELECT COUNT(*) FROM zhinote_notes")
        total_notes = cursor.fetchone()[0]
        
        # 获取总任务数（保留原字段，用于其他用途）
        cursor.execute("SELECT COALESCE(SUM(task_count), 0) FROM zhinote_study_stats")
        total_tasks = cursor.fetchone()[0]
        
        # 获取学习天数
        cursor.execute("SELECT COUNT(DISTINCT study_date) FROM zhinote_study_stats")
        study_days = cursor.fetchone()[0] or 0
        
        # 获取最近7天的数据
        start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        cursor.execute(
            """
            SELECT study_date, study_duration, review_count, task_count
            FROM zhinote_study_stats
            WHERE study_date >= %s
            ORDER BY study_date DESC
            """,
            (start_date,)
        )
        recent_stats = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        # 计算最近7天的数据
        recent_duration = sum(row[1] for row in recent_stats)
        recent_reviews = sum(row[2] for row in recent_stats)
        recent_tasks = sum(row[3] for row in recent_stats)
        
        return {
            "code": 0,
            "data": {
                "totalDuration": total_duration,
                "totalReviews": total_reviews,
                "totalNotes": total_notes,
                "totalTasks": total_tasks,
                "studyDays": study_days,
                "recentDuration": recent_duration,
                "recentReviews": recent_reviews,
                "recentTasks": recent_tasks
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计摘要失败: {str(e)}")
