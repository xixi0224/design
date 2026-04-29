import os
import json
import pymysql
import pdfplumber
from docx import Document
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import dashscope
from dashscope import Generation

app = FastAPI(title="ZhiNote Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "zhinote",
    "charset": "utf8mb4",
}

dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def get_conn():
    return pymysql.connect(**DB_CONFIG)

def extract_text_from_pdf(file_path: str) -> str:
    texts = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                texts.append(text)
    return "\n".join(texts)

def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    texts = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(texts)

def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def extract_text(file_path: str, filename: str) -> str:
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return extract_text_from_pdf(file_path)
    if filename.endswith(".docx"):
        return extract_text_from_docx(file_path)
    if filename.endswith(".txt") or filename.endswith(".md"):
        return extract_text_from_txt(file_path)
    raise HTTPException(status_code=400, detail="暂不支持该文件格式")

def ai_analyze_text(content: str, course_name: str):
    prompt = f"""
你是一个{course_name}课程的AI助教。
请把以下内容整理成严格 JSON 数组，每一项包含：
section, summary, keywords, is_exam_point, importance。

要求：
1. section: 章节标题
2. summary: 50字以内摘要
3. keywords: 3-5个关键词数组
4. is_exam_point: true 或 false
5. importance: "⭐" / "⭐⭐" / "⭐⭐⭐"

只输出 JSON，不要输出任何解释文字。

内容：
{content[:12000]}
"""

    response = Generation.call(
        model="qwen-plus",
        messages=[
            {"role": "system", "content": "你是一个严谨的教育AI助手，只输出JSON。"},
            {"role": "user", "content": prompt}
        ],
        result_format="message",
        response_format={"type": "json_object"}
    )
    return response.output.choices[0].message.content

@app.get("/")
def root():
    return {"message": "ZhiNote backend is running"}

@app.post("/api/upload")
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
        cursor.execute(
            """
            INSERT INTO zhinote_documents (course_id, filename, content, page_count, status)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (course_id, file.filename, text_content, 1, "processing")
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

@app.post("/api/analyze/{doc_id}")
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

@app.get("/api/notes/{doc_id}")
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

@app.get("/api/visualization/{doc_id}")
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

@app.get("/api/animation")
def get_animation(keyword: str = Query("栈")):
    if keyword == "栈":
        return {
            "type": "stack",
            "steps": [
                {"action": "push", "value": "A"},
                {"action": "push", "value": "B"},
                {"action": "pop"}
            ]
        }
    elif keyword == "队列":
        return {
            "type": "queue",
            "steps": [
                {"action": "enqueue", "value": "X"},
                {"action": "enqueue", "value": "Y"},
                {"action": "dequeue"}
            ]
        }
    else:
        return {
            "type": "basic",
            "steps": [
                {"action": "show", "value": keyword}
            ]
        }