import json
from fastapi import APIRouter, HTTPException
from app.db import get_conn

router = APIRouter(tags=["visualization"])

@router.get("/visualization/{doc_id}")
def get_visualization(doc_id: int):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT section, COUNT(*)
            FROM zhinote_analysis
            WHERE doc_id = %s AND is_exam_point = 1
            GROUP BY section
            ORDER BY COUNT(*) DESC
            """,
            (doc_id,)
        )
        rows = cursor.fetchall()
        bar_data = [{"name": r[0], "value": r[1]} for r in rows]

        cursor.execute(
            "SELECT keywords FROM zhinote_analysis WHERE doc_id = %s",
            (doc_id,)
        )
        all_keywords = []
        for row in cursor.fetchall():
            if row[0]:
                all_keywords.extend(json.loads(row[0]))

        keyword_count = {}
        for k in all_keywords:
            keyword_count[k] = keyword_count.get(k, 0) + 1

        word_cloud = [{"name": k, "value": v} for k, v in keyword_count.items()]

        cursor.close()
        conn.close()

        return {
            "bar_data": bar_data,
            "word_cloud": word_cloud
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"可视化数据获取失败: {str(e)}")