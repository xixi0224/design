import os
from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from app.db import get_conn
from app.services.text_extract import extract_text

router = APIRouter(tags=["upload"])

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    course_id: int = Query(1)
):
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", file.filename)

    content_bytes = await file.read()
    with open(file_path, "wb") as f:
        f.write(content_bytes)

    try:
        text_content = extract_text(file_path, file.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    try:
        conn = get_conn()
        cursor = conn.cursor()
        # 使用文件名作为笔记标题，移除文件扩展名
        title = file.filename
        name_parts = title.split('.')
        if len(name_parts) > 1:
            name_parts.pop()  # 移除扩展名
            title = '.'.join(name_parts)
        
        cursor.execute(
            """
            INSERT INTO zhinote_notes (title, content, created_at)
            VALUES (%s, %s, NOW())
            """,
            (title, text_content)
        )
        doc_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据库写入失败: {str(e)}")

    return {
        "message": "上传成功",
        "doc_id": doc_id,
        "filename": file.filename,
        "text_length": len(text_content)
    }