import os
from datetime import datetime
from app.db import get_conn
from app.schemas.study_assist import ExportRequest, ExportResponse

def export_note(request: ExportRequest):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT title, content FROM zhinote_auto_notes WHERE id = %s",
        (request.note_id,)
    )
    result = cursor.fetchone()

    if not result:
        raise ValueError("Note not found")

    title, content = result

    os.makedirs("exports", exist_ok=True)
    export_path = os.path.join("exports", f"{title}_{request.note_id}.{request.export_type}")

    if request.export_type == "pdf":
        export_to_pdf(content, export_path)
    elif request.export_type == "docx":
        export_to_docx(content, export_path)
    elif request.export_type == "md":
        export_to_md(content, export_path)
    else:
        raise ValueError("Invalid export type")

    cursor.execute(
        """
        INSERT INTO zhinote_export_records (note_id, export_type, export_path)
        VALUES (%s, %s, %s)
        """,
        (request.note_id, request.export_type, export_path)
    )
    export_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    return ExportResponse(
        id=export_id,
        note_id=request.note_id,
        export_type=request.export_type,
        export_path=export_path,
        created_at=datetime.now()
    )

def export_to_pdf(content: str, export_path: str):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(export_path, pagesize=A4)
        c.setFont("Helvetica", 12)

        lines = content.split('\n')
        y = 800
        for line in lines:
            if y < 50:
                c.showPage()
                c.setFont("Helvetica", 12)
                y = 800
            c.drawString(50, y, line[:100] if len(line) > 100 else line)
            y -= 20

        c.save()
    except ImportError:
        with open(export_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
            f.write(content)

def export_to_docx(content: str, export_path: str):
    try:
        from docx import Document
        doc = Document()
        doc.add_paragraph(content)
        doc.save(export_path)
    except ImportError:
        export_to_md(content, export_path.replace('.docx', '.md'))

def export_to_md(content: str, export_path: str):
    with open(export_path, 'w', encoding='utf-8') as f:
        f.write(content)

def get_export_records(note_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, note_id, export_type, export_path, created_at FROM zhinote_export_records WHERE note_id = %s",
        (note_id,)
    )
    records = cursor.fetchall()
    cursor.close()
    conn.close()

    return [
        ExportResponse(
            id=record[0],
            note_id=record[1],
            export_type=record[2],
            export_path=record[3],
            created_at=record[4]
        )
        for record in records
    ]

def create_reminder(reminder):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO zhinote_reminders (user_id, title, content, reminder_time)
        VALUES (%s, %s, %s, %s)
        """,
        (reminder.user_id, reminder.title, reminder.content, reminder.reminder_time)
    )
    reminder_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    from app.schemas.study_assist import ReminderResponse
    return ReminderResponse(
        id=reminder_id,
        user_id=reminder.user_id,
        title=reminder.title,
        content=reminder.content,
        reminder_time=reminder.reminder_time,
        is_completed=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

def get_reminders(user_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, user_id, title, content, reminder_time, is_completed, created_at, updated_at
        FROM zhinote_reminders
        WHERE user_id = %s
        ORDER BY reminder_time ASC
        """,
        (user_id,)
    )
    reminders = cursor.fetchall()
    cursor.close()
    conn.close()

    from app.schemas.study_assist import ReminderResponse
    return [
        ReminderResponse(
            id=rem[0],
            user_id=rem[1],
            title=rem[2],
            content=rem[3],
            reminder_time=rem[4],
            is_completed=rem[5],
            created_at=rem[6],
            updated_at=rem[7]
        )
        for rem in reminders
    ]

def update_reminder_status(reminder_id: int, is_completed: bool):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE zhinote_reminders SET is_completed = %s WHERE id = %s",
        (is_completed, reminder_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return {"success": True, "reminder_id": reminder_id, "is_completed": is_completed}

def start_timer(request):
    # 这里只是模拟计时器功能，实际前端会处理计时逻辑
    return {
        "success": True,
        "message": f"计时器已启动，时长：{request.duration}秒",
        "duration": request.duration
    }

def start_pomodoro(request):
    # 这里只是模拟番茄钟功能，实际前端会处理计时逻辑
    total_time = (request.work_duration + request.break_duration) * request.cycles
    return {
        "success": True,
        "message": f"番茄钟已启动，工作{request.work_duration}分钟，休息{request.break_duration}分钟，共{request.cycles}个循环",
        "work_duration": request.work_duration,
        "break_duration": request.break_duration,
        "cycles": request.cycles
    }


def complete_pomodoro(duration: int, user_id: int = 1):
    """
    番茄钟完成时记录学习时长
    :param duration: 实际专注时长（分钟）
    :param user_id: 用户ID
    :return: 记录结果
    """
    from datetime import datetime
    from app.db import get_conn
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 检查今天是否已有记录
        cursor.execute(
            """
            SELECT id, study_duration
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
                    updated_at = NOW()
                WHERE id = %s
                """,
                (duration, row[0])
            )
            total_today = row[1] + duration
        else:
            # 插入新记录
            cursor.execute(
                """
                INSERT INTO zhinote_study_stats (study_date, study_duration, review_count, task_count)
                VALUES (%s, %s, 0, 0)
                """,
                (today, duration)
            )
            total_today = duration
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"番茄钟完成！已记录{duration}分钟学习时长",
            "duration": duration,
            "total_today": total_today
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"记录失败: {str(e)}",
            "duration": duration,
            "total_today": 0
        }

def convert_unit(request):
    # 简单的单位转换功能
    conversions = {
        # 长度单位转换（米为基准）
        "m": 1.0,
        "km": 1000.0,
        "cm": 0.01,
        "mm": 0.001,
        "inch": 0.0254,
        "foot": 0.3048,
        # 质量单位转换（千克为基准）
        "kg": 1.0,
        "g": 0.001,
        "mg": 0.000001,
        "lb": 0.453592,
        "oz": 0.0283495,
        # 时间单位转换（秒为基准）
        "s": 1.0,
        "min": 60.0,
        "h": 3600.0,
        "day": 86400.0,
        # 温度单位转换
        "c": "celsius",
        "f": "fahrenheit",
        "k": "kelvin"
    }
    
    # 处理温度转换
    if request.from_unit in ["c", "f", "k"] and request.to_unit in ["c", "f", "k"]:
        if request.from_unit == "c" and request.to_unit == "f":
            converted_value = (request.value * 9/5) + 32
        elif request.from_unit == "f" and request.to_unit == "c":
            converted_value = (request.value - 32) * 5/9
        elif request.from_unit == "c" and request.to_unit == "k":
            converted_value = request.value + 273.15
        elif request.from_unit == "k" and request.to_unit == "c":
            converted_value = request.value - 273.15
        elif request.from_unit == "f" and request.to_unit == "k":
            converted_value = (request.value - 32) * 5/9 + 273.15
        elif request.from_unit == "k" and request.to_unit == "f":
            converted_value = (request.value - 273.15) * 9/5 + 32
        else:
            converted_value = request.value
    else:
        # 处理其他单位转换
        if request.from_unit not in conversions or request.to_unit not in conversions:
            return {
                "success": False,
                "message": "不支持的单位",
                "original_value": request.value,
                "from_unit": request.from_unit,
                "converted_value": 0,
                "to_unit": request.to_unit
            }
        
        # 转换为基准单位，再转换为目标单位
        base_value = request.value * conversions[request.from_unit]
        converted_value = base_value / conversions[request.to_unit]
    
    return {
        "success": True,
        "message": "单位转换成功",
        "original_value": request.value,
        "from_unit": request.from_unit,
        "converted_value": converted_value,
        "to_unit": request.to_unit
    }

def recommend_schools(request):
    conn = get_conn()
    cursor = conn.cursor()
    
    # 构建查询条件
    query = "SELECT id, name, location, ranking, type, min_score, majors, description FROM zhinote_schools WHERE min_score <= %s"
    params = [request.score]
    
    if request.location:
        query += " AND location LIKE %s"
        params.append(f"%{request.location}%")
    
    if request.major:
        query += " AND majors LIKE %s"
        params.append(f"%{request.major}%")
    
    query += " ORDER BY ranking ASC LIMIT 10"
    
    cursor.execute(query, params)
    schools = cursor.fetchall()
    
    # 如果没有学校数据，添加一些示例数据
    if not schools:
        # 添加示例学校数据
        sample_schools = [
            ("清华大学", "北京", 1, "综合性", 680, "计算机科学与技术,电子信息工程,自动化", "中国顶尖综合性大学，以理工科见长"),
            ("北京大学", "北京", 2, "综合性", 675, "法学,经济学,数学", "中国顶尖综合性大学，以人文社科见长"),
            ("复旦大学", "上海", 3, "综合性", 665, "新闻学,经济学,生物学", "华东地区顶尖综合性大学"),
            ("上海交通大学", "上海", 4, "综合性", 660, "机械工程,船舶与海洋工程,计算机", "华东地区顶尖理工科大学"),
            ("浙江大学", "杭州", 5, "综合性", 655, "计算机科学与技术,土木工程,光学工程", "华东地区顶尖综合性大学"),
            ("南京大学", "南京", 6, "综合性", 650, "物理学,化学,天文学", "华东地区顶尖综合性大学"),
            ("中国科学技术大学", "合肥", 7, "理工科", 645, "物理学,化学,地球物理学", "中国顶尖理工科大学"),
            ("武汉大学", "武汉", 8, "综合性", 640, "法学,新闻学,水利工程", "华中地区顶尖综合性大学"),
            ("华中科技大学", "武汉", 9, "综合性", 635, "机械工程,光学工程,计算机", "华中地区顶尖理工科大学"),
            ("中山大学", "广州", 10, "综合性", 630, "临床医学,工商管理,哲学", "华南地区顶尖综合性大学")
        ]
        
        for school in sample_schools:
            cursor.execute(
                """
                INSERT INTO zhinote_schools (name, location, ranking, type, min_score, majors, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                school
            )
        
        conn.commit()
        
        # 重新查询
        cursor.execute(query, params)
        schools = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    from app.schemas.study_assist import SchoolResponse
    school_list = [
        SchoolResponse(
            id=school[0],
            name=school[1],
            location=school[2],
            ranking=school[3],
            type=school[4],
            min_score=school[5],
            majors=school[6],
            description=school[7]
        )
        for school in schools
    ]
    
    return {
        "success": True,
        "message": "学校推荐成功",
        "recommendations": school_list
    }