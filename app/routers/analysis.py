import json
from fastapi import APIRouter, HTTPException
from app.db import get_conn
from app.services.ai_service import ai_analyze_text

router = APIRouter(tags=["analysis"])

@router.post("/analyze/{doc_id}")
def analyze_document(doc_id: int):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT d.content, c.name
            FROM zhinote_documents d
            JOIN zhinote_courses c ON d.course_id = c.id
            WHERE d.id = %s
            """,
            (doc_id,)
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="文档不存在")

        content, course_name = row
        raw_result = ai_analyze_text(content, course_name)

        try:
            analysis_results = json.loads(raw_result)
            if isinstance(analysis_results, dict):
                analysis_results = [analysis_results]
        except Exception:
            analysis_results = [{
                "section": f"{course_name}-默认章节",
                "summary": raw_result[:100],
                "keywords": ["知识点"],
                "is_exam_point": True,
                "importance": "⭐⭐"
            }]

        cursor.execute("DELETE FROM zhinote_analysis WHERE doc_id = %s", (doc_id,))

        for item in analysis_results:
            cursor.execute(
                """
                INSERT INTO zhinote_analysis
                (doc_id, section, summary, keywords, is_exam_point, importance)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    doc_id,
                    item.get("section", ""),
                    item.get("summary", ""),
                    json.dumps(item.get("keywords", []), ensure_ascii=False),
                    int(bool(item.get("is_exam_point", False))),
                    item.get("importance", "⭐⭐")
                )
            )

        cursor.execute("UPDATE zhinote_documents SET status='done' WHERE id=%s", (doc_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return {"message": "分析完成", "count": len(analysis_results), "results": analysis_results}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")