import json
from fastapi import APIRouter, HTTPException, Body
from app.db import get_conn

router = APIRouter(tags=["notes"])

@router.get("/notes/{doc_id}")
def get_notes(doc_id: int):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT section, summary, keywords, is_exam_point, importance
            FROM zhinote_analysis
            WHERE doc_id = %s
            ORDER BY id ASC
            """,
            (doc_id,)
        )
        rows = cursor.fetchall()

        notes = []
        for r in rows:
            notes.append({
                "section": r[0],
                "summary": r[1],
                "keywords": json.loads(r[2]) if r[2] else [],
                "is_exam_point": bool(r[3]),
                "importance": r[4]
            })

        cursor.close()
        conn.close()
        return {"doc_id": doc_id, "notes": notes}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取笔记失败: {str(e)}")

@router.get("/note/{noteId}")
def get_note_by_id(noteId: int):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 假设笔记存储在zhinote_notes表中
        cursor.execute(
            """
            SELECT id, title, content
            FROM zhinote_notes
            WHERE id = %s
            """,
            (noteId,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="笔记不存在")

        note = {
            "id": row[0],
            "title": row[1],
            "content": row[2]
        }

        cursor.close()
        conn.close()
        return {"code": 0, "data": note}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取笔记失败: {str(e)}")

@router.post("/save-note")
def save_note(title: str = Body(...), content: str = Body(...)):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 插入新笔记
        cursor.execute(
            """
            INSERT INTO zhinote_notes (title, content, created_at)
            VALUES (%s, %s, NOW())
            """,
            (title, content)
        )
        note_id = cursor.lastrowid
        conn.commit()

        cursor.close()
        conn.close()
        return {"code": 0, "data": {"noteId": note_id, "title": title}}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"保存笔记失败: {str(e)}")


@router.put("/notes/{note_id}/title")
def update_note_title(note_id: int, title_data: dict = Body(...)):
    """
    更新笔记标题
    """
    try:
        new_title = title_data.get("title", "").strip()
        
        if not new_title:
            raise HTTPException(status_code=400, detail="笔记名称不能为空")
        
        if len(new_title) > 50:
            raise HTTPException(status_code=400, detail="笔记名称不能超过50个字符")
        
        conn = get_conn()
        cursor = conn.cursor()
        
        # 检查笔记是否存在
        cursor.execute("SELECT id FROM zhinote_notes WHERE id = %s", (note_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="笔记不存在")
        
        # 更新笔记标题
        cursor.execute(
            """
            UPDATE zhinote_notes
            SET title = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (new_title, note_id)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return {
            "code": 0,
            "message": "修改成功",
            "data": {
                "noteId": note_id,
                "title": new_title
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新笔记名称失败: {str(e)}")

@router.put("/notes/{noteId}")
def update_note(noteId: int, title: str = Body(...), content: str = Body(...)):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 更新笔记
        cursor.execute(
            """
            UPDATE zhinote_notes
            SET title = %s, content = %s, updated_at = NOW()
            WHERE id = %s
            """,
            (title, content, noteId)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="笔记不存在")
        
        conn.commit()

        cursor.close()
        conn.close()
        return {"code": 0, "data": {"noteId": noteId, "title": title}}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"更新笔记失败: {str(e)}")

@router.get("/recent-notes")
def get_recent_notes(limit: int = 5):
    """
    获取最近的学习笔记
    limit: 限制返回的记录数，默认5条
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 从zhinote_notes表中获取最近的笔记，按updated_at或created_at降序排序
        cursor.execute(
            """
            SELECT id, title, content, created_at, updated_at
            FROM zhinote_notes
            ORDER BY COALESCE(updated_at, created_at) DESC
            LIMIT %s
            """,
            (limit,)
        )
        rows = cursor.fetchall()

        recent_notes = []
        for row in rows:
            note_id, title, content, created_at, updated_at = row
            
            # 提取来源类型（简单判断）
            source_type = "文本"
            if "[音频转文字]" in content:
                source_type = "音频"
            elif "[PDF导入]" in content:
                source_type = "PDF"
            elif "[Word导入]" in content:
                source_type = "Word"
            elif "[语音录入]" in content:
                source_type = "语音"
            
            # 提取标签（简单判断）
            tags = []
            if "考点" in content:
                tags.append("考点")
            if "重点" in content:
                tags.append("重点")
            if "难点" in content:
                tags.append("难点")
            
            recent_notes.append({
                "id": note_id,
                "title": title,
                "created_at": created_at.strftime("%Y-%m-%d %H:%M"),
                "source_type": source_type,
                "tags": tags
            })

        cursor.close()
        conn.close()
        return {"code": 0, "data": {"recent_notes": recent_notes}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取最近学习记录失败: {str(e)}")

@router.get("/notes-list")
def get_notes_list(limit: int = 10, offset: int = 0):
    """
    获取笔记列表
    limit: 每页记录数，默认10条
    offset: 偏移量，默认0
    """
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 从zhinote_notes表中获取笔记，按updated_at或created_at降序排序
        cursor.execute(
            """
            SELECT id, title, content, created_at, updated_at
            FROM zhinote_notes
            ORDER BY COALESCE(updated_at, created_at) DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset)
        )
        rows = cursor.fetchall()

        # 获取总记录数
        cursor.execute("SELECT COUNT(*) FROM zhinote_notes")
        total = cursor.fetchone()[0]

        notes = []
        for row in rows:
            note_id, title, content, created_at, updated_at = row
            
            # 提取来源类型（简单判断）
            source_type = "文本"
            if "[音频转文字]" in content:
                source_type = "音频"
            elif "[PDF导入]" in content:
                source_type = "PDF"
            elif "[Word导入]" in content:
                source_type = "Word"
            elif "[语音录入]" in content:
                source_type = "语音"
            
            # 提取标签（简单判断）
            tags = []
            if "考点" in content:
                tags.append({"name": "考点", "className": "tag-exam"})
            if "重点" in content:
                tags.append({"name": "重点", "className": "tag-important"})
            if "难点" in content:
                tags.append({"name": "难点", "className": "tag-difficult"})
            
            notes.append({
                "id": note_id,
                "title": title,
                "date": created_at.strftime("%Y-%m-%d"),
                "source": source_type,
                "tags": tags
            })

        cursor.close()
        conn.close()
        return {"code": 0, "data": {"notes": notes, "total": total}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取笔记列表失败: {str(e)}")
