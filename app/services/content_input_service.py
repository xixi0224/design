import os
from datetime import datetime
from app.db import get_conn
from app.schemas.content_input import AudioRecordResponse, TextInputCreate, TextInputResponse

def handle_audio_upload(file, course_id: int):
    os.makedirs("uploads/audio", exist_ok=True)
    file_path = os.path.join("uploads/audio", file.filename)

    # 保存文件内容
    content = file.file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO zhinote_audio_records (course_id, filename, duration, status)
        VALUES (%s, %s, %s, %s)
        """,
        (course_id, file.filename, 0, "uploaded")
    )
    audio_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    return AudioRecordResponse(
        id=audio_id,
        course_id=course_id,
        filename=file.filename,
        duration=0,
        status="uploaded",
        created_at=datetime.now()
    )

def create_text_input(input_data: TextInputCreate):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO zhinote_text_inputs (course_id, title, content, status)
        VALUES (%s, %s, %s, %s)
        """,
        (input_data.course_id, input_data.title, input_data.content, "created")
    )
    text_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()

    return TextInputResponse(
        id=text_id,
        course_id=input_data.course_id,
        title=input_data.title,
        content=input_data.content,
        status="created",
        created_at=datetime.now()
    )