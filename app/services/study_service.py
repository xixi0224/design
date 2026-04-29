from datetime import datetime
from app.db import get_conn
from app.schemas.study_analysis import StudyRecordCreate, StudyRecordResponse, ExamPointHeatResponse

def create_study_record(record: StudyRecordCreate):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id FROM zhinote_study_records
        WHERE user_id = %s AND note_id = %s
        ORDER BY created_at DESC LIMIT 1
        """,
        (record.user_id, record.note_id)
    )
    existing = cursor.fetchone()

    if existing:
        cursor.execute(
            """
            UPDATE zhinote_study_records
            SET study_time = study_time + %s, last_study_at = %s
            WHERE id = %s
            """,
            (record.study_time, datetime.now(), existing[0])
        )
        record_id = existing[0]
    else:
        cursor.execute(
            """
            INSERT INTO zhinote_study_records (user_id, note_id, study_time, last_study_at)
            VALUES (%s, %s, %s, %s)
            """,
            (record.user_id, record.note_id, record.study_time, datetime.now())
        )
        record_id = cursor.lastrowid

    conn.commit()
    cursor.close()
    conn.close()

    return StudyRecordResponse(
        id=record_id,
        user_id=record.user_id,
        note_id=record.note_id,
        study_time=record.study_time,
        last_study_at=datetime.now(),
        created_at=datetime.now()
    )

def get_study_records(user_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_id, note_id, study_time, last_study_at, created_at
        FROM zhinote_study_records
        WHERE user_id = %s
        ORDER BY last_study_at DESC
        """,
        (user_id,)
    )
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        StudyRecordResponse(
            id=record[0],
            user_id=record[1],
            note_id=record[2],
            study_time=record[3],
            last_study_at=record[4],
            created_at=record[5]
        )
        for record in records
    ]

def get_exam_point_heat():
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ep.id, ep.content, ep.heat, ep.difficulty
        FROM zhinote_exam_points ep
        ORDER BY ep.heat DESC
        LIMIT 10
        """
    )
    points = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        ExamPointHeatResponse(
            point_id=point[0],
            content=point[1],
            heat=point[2],
            difficulty=point[3]
        )
        for point in points
    ]

def increment_exam_point_heat(point_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE zhinote_exam_points SET heat = heat + 1 WHERE id = %s",
        (point_id,)
    )
    conn.commit()
    cursor.close()
    conn.close()

def create_study_plan(plan):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO zhinote_study_plans (user_id, title, description, start_date, end_date, target_hours)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (plan.user_id, plan.title, plan.description, plan.start_date, plan.end_date, plan.target_hours)
    )
    plan_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    from app.schemas.study_analysis import StudyPlanResponse
    return StudyPlanResponse(
        id=plan_id,
        user_id=plan.user_id,
        title=plan.title,
        description=plan.description,
        start_date=plan.start_date,
        end_date=plan.end_date,
        target_hours=plan.target_hours,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

def get_study_plans(user_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_id, title, description, start_date, end_date, target_hours, created_at, updated_at
        FROM zhinote_study_plans
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )
    plans = cursor.fetchall()
    cursor.close()
    conn.close()

    from app.schemas.study_analysis import StudyPlanResponse
    return [
        StudyPlanResponse(
            id=plan[0],
            user_id=plan[1],
            title=plan[2],
            description=plan[3],
            start_date=plan[4],
            end_date=plan[5],
            target_hours=plan[6],
            created_at=plan[7],
            updated_at=plan[8]
        )
        for plan in plans
    ]

def get_study_trends(user_id: int, days: int = 30):
    conn = get_conn()
    cursor = conn.cursor()
    
    # 计算起始日期
    from datetime import datetime, timedelta
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days-1)
    
    # 获取每日学习时间
    cursor.execute(
        """
        SELECT DATE(last_study_at) as study_date, SUM(study_time) as total_time
        FROM zhinote_study_records
        WHERE user_id = %s AND last_study_at >= %s
        GROUP BY DATE(last_study_at)
        ORDER BY study_date
        """,
        (user_id, start_date)
    )
    daily_data = cursor.fetchall()
    
    # 生成完整的日期范围
    date_map = {}
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        date_map[date_str] = 0
        current_date += timedelta(days=1)
    
    # 填充实际数据
    for date_str, time in daily_data:
        date_map[date_str] = time
    
    # 构建每日趋势
    daily_trends = []
    for date_str, time in date_map.items():
        daily_trends.append({
            "date": datetime.strptime(date_str, '%Y-%m-%d').date(),
            "study_time": time
        })
    
    # 计算每周趋势
    weekly_trends = []
    week_map = {}
    
    for date_str, time in date_map.items():
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        week_start = date_obj - timedelta(days=date_obj.weekday())
        week_key = week_start.strftime('%Y-%m-%d')
        
        if week_key not in week_map:
            week_map[week_key] = {
                "week_start": week_start.date(),
                "week_end": (week_start + timedelta(days=6)).date(),
                "study_time": 0
            }
        week_map[week_key]["study_time"] += time
    
    for week_data in week_map.values():
        weekly_trends.append(week_data)
    
    # 计算每月趋势
    monthly_trends = []
    month_map = {}
    
    for date_str, time in date_map.items():
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        month_key = date_obj.strftime('%Y-%m')
        
        if month_key not in month_map:
            month_map[month_key] = {
                "month": month_key,
                "study_time": 0
            }
        month_map[month_key]["study_time"] += time
    
    for month_data in month_map.values():
        monthly_trends.append(month_data)
    
    # 计算总学习时间和平均每日时间
    total_study_time = sum(time for time in date_map.values())
    average_daily_time = total_study_time / days if days > 0 else 0
    
    cursor.close()
    conn.close()
    
    from app.schemas.study_analysis import StudyTrendResponse, StudyTrendDay, StudyTrendWeek, StudyTrendMonth
    
    return StudyTrendResponse(
        daily_trends=[
            StudyTrendDay(date=item["date"], study_time=item["study_time"])
            for item in daily_trends
        ],
        weekly_trends=[
            StudyTrendWeek(
                week_start=item["week_start"],
                week_end=item["week_end"],
                study_time=item["study_time"]
            )
            for item in weekly_trends
        ],
        monthly_trends=[
            StudyTrendMonth(month=item["month"], study_time=item["study_time"])
            for item in monthly_trends
        ],
        total_study_time=total_study_time,
        average_daily_time=average_daily_time
    )