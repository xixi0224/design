from fastapi import APIRouter, HTTPException, Body
from app.schemas.ai_analysis import AnalysisRequest, AnalysisResponse, ASRRequest, ASRResponse
from app.services.ai_analysis_service import analyze_content, perform_asr
from app.db import get_conn

router = APIRouter(tags=["ai_analysis"])

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_content_endpoint(request: AnalysisRequest):
    try:
        return analyze_content(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")

@router.post("/asr", response_model=ASRResponse)
async def perform_asr_endpoint(request: ASRRequest):
    try:
        return perform_asr(request.audio_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"语音转文本失败: {str(e)}")

@router.post("/generate-complete-note")
async def generate_complete_note(docId: int = Body(...)):
    try:
        conn = get_conn()
        cursor = conn.cursor()

        # 从zhinote_analysis表中获取分析数据
        cursor.execute(
            """
            SELECT section, summary, keywords, is_exam_point, importance
            FROM zhinote_analysis
            WHERE doc_id = %s
            ORDER BY id ASC
            """,
            (docId,)
        )
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="未找到文档分析数据")

        # 从zhinote_notes表中获取原始笔记内容
        cursor.execute(
            """
            SELECT title, content
            FROM zhinote_notes
            WHERE id = %s
            """,
            (docId,)
        )
        note = cursor.fetchone()
        
        if not note:
            raise HTTPException(status_code=404, detail="未找到原始笔记")
        
        title, original_content = note

        # 构建分析数据字符串
        analysis_data = ""
        for section, summary, keywords, is_exam_point, importance in rows:
            analysis_data += f"章节: {section}\n"
            analysis_data += f"总结: {summary}\n"
            analysis_data += f"关键词: {keywords}\n"
            analysis_data += f"是否考点: {'是' if is_exam_point else '否'}\n"
            analysis_data += f"重要程度: {importance}\n\n"

        # 调用阿里云通义千问大模型生成完整笔记
        import dashscope
        from dashscope import Generation
        from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL
        
        dashscope.api_key = DASHSCOPE_API_KEY
        
        prompt = f"""请根据以下分析数据，生成一份格式规整、内容全面的完整笔记。

要求：
1. 自动分好章节，有清晰的标题层级
2. 重点内容高亮
3. 考点有特殊边框
4. 内容全面，逻辑清晰
5. 格式美观，适合阅读

原始笔记标题：{title}

原始笔记内容：
{original_content[:500]}

分析数据：
{analysis_data}
"""
        
        response = Generation.call(
            model=DASHSCOPE_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的笔记整理助手，能够将分析数据整合成格式规整、内容全面的完整笔记。"},
                {"role": "user", "content": prompt}
            ],
            result_format="message"
        )
        
        # 获取生成的笔记内容
        generated_content = response.output.choices[0].message.content

        # 保存到笔记表
        cursor.execute(
            """
            INSERT INTO zhinote_notes (title, content, created_at)
            VALUES (%s, %s, NOW())
            """,
            (f"{title}_完整笔记", generated_content)
        )
        note_id = cursor.lastrowid
        conn.commit()

        cursor.close()
        conn.close()
        return {"code": 0, "data": {"noteId": note_id, "title": f"{title}_完整笔记"}}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成完整笔记失败: {str(e)}")

@router.post("/generate-tags")
async def generate_tags(data: dict = Body(...)):
    try:
        noteId = data.get("noteId")
        course = data.get("course", "408")
        
        if not noteId:
            raise HTTPException(status_code=400, detail="笔记ID不能为空")
        
        conn = get_conn()
        cursor = conn.cursor()
        
        # 从zhinote_notes表中获取笔记内容
        cursor.execute(
            """
            SELECT title, content
            FROM zhinote_notes
            WHERE id = %s
            """,
            (noteId,)
        )
        note = cursor.fetchone()
        
        if not note:
            raise HTTPException(status_code=404, detail="未找到笔记")
        
        title, content = note
        
        # 调用阿里云通义千问大模型生成标签
        import dashscope
        from dashscope import Generation
        from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL
        
        dashscope.api_key = DASHSCOPE_API_KEY
        
        prompt = f"""请根据以下笔记内容，为其生成5-8个相关的标签。

要求：
1. 标签要与笔记内容相关
2. 标签要简洁明了
3. 标签要涵盖笔记的主要内容和主题
4. 请严格按照以下格式输出，不要包含任何其他内容：
标签1,标签2,标签3,标签4,标签5

课程：{course}

笔记标题：{title}

笔记内容：
{content[:1000]}
"""
        
        response = Generation.call(
            model=DASHSCOPE_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的知识分类助手，能够根据笔记内容生成相关的标签。"},
                {"role": "user", "content": prompt}
            ],
            result_format="message"
        )
        
        # 获取生成的标签
        tags_text = response.output.choices[0].message.content
        tags = [tag.strip() for tag in tags_text.split(",")]
        
        # 保存标签到数据库
        # 假设我们有一个zhinote_note_tags表来存储笔记标签
        for tag in tags:
            # 检查标签是否已存在
            cursor.execute(
                """
                SELECT id FROM zhinote_tags WHERE name = %s
                """,
                (tag,)
            )
            tag_record = cursor.fetchone()
            
            if not tag_record:
                # 创建新标签
                cursor.execute(
                    """
                    INSERT INTO zhinote_tags (name, created_at)
                    VALUES (%s, NOW())
                    """,
                    (tag,)
                )
                tag_id = cursor.lastrowid
            else:
                tag_id = tag_record[0]
            
            # 关联标签到笔记
            cursor.execute(
                """
                INSERT IGNORE INTO zhinote_note_tags (note_id, tag_id, created_at)
                VALUES (%s, %s, NOW())
                """,
                (noteId, tag_id)
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"code": 0, "data": {"tags": tags}}
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成标签失败: {str(e)}")

@router.post("/generate-knowledge-graph")
async def generate_knowledge_graph(data: dict = Body(...)):
    try:
        noteId = data.get("noteId")
        course = data.get("course", "408")
        
        if not noteId:
            raise HTTPException(status_code=400, detail="笔记ID不能为空")
        
        conn = get_conn()
        cursor = conn.cursor()
        
        # 从zhinote_notes表中获取笔记内容
        cursor.execute(
            """
            SELECT title, content
            FROM zhinote_notes
            WHERE id = %s
            """,
            (noteId,)
        )
        note = cursor.fetchone()
        
        if not note:
            raise HTTPException(status_code=404, detail="未找到笔记")
        
        title, content = note
        
        # 调用阿里云通义千问大模型生成知识图谱数据
        import dashscope
        from dashscope import Generation
        from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL
        
        dashscope.api_key = DASHSCOPE_API_KEY
        
        prompt = f"""请根据以下笔记内容，生成一个知识图谱的节点和边数据。

要求：
1. 提取笔记中的核心概念作为节点
2. 分析概念之间的关系作为边
3. 为每个节点添加定义和掌握程度（0-100）
4. 请严格按照以下JSON格式输出，不要包含任何其他内容：
{{
  "nodes": [
    {{"id": "节点1", "name": "节点名称", "definition": "节点定义", "mastery": 掌握程度}}, 
    ...
  ],
  "links": [
    {{"source": "源节点", "target": "目标节点", "relation": "关系类型"}}, 
    ...
  ]
}}

课程：{course}

笔记标题：{title}

笔记内容：
{content[:1500]}
"""
        
        response = Generation.call(
            model=DASHSCOPE_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的知识图谱构建助手，能够根据笔记内容提取核心概念并分析它们之间的关系。"},
                {"role": "user", "content": prompt}
            ],
            result_format="message"
        )
        
        # 获取生成的知识图谱数据
        graph_data_text = response.output.choices[0].message.content
        
        # 解析JSON
        import json
        import re
        
        # 提取JSON
        json_match = re.search(r'\{.*\}', graph_data_text, re.DOTALL)
        if not json_match:
            raise HTTPException(status_code=500, detail="生成的知识图谱数据格式错误")
        
        graph_data = json.loads(json_match.group())
        
        # 为节点添加类别
        categories = []
        category_map = {}
        for node in graph_data.get("nodes", []):
            node_type = node.get("type", "概念")
            if node_type not in category_map:
                category_map[node_type] = len(categories)
                categories.append({"name": node_type})
            node["category"] = category_map[node_type]
        
        # 保存知识图谱数据到数据库
        # 假设我们有一个zhinote_knowledge_graph表来存储知识图谱数据
        # 这里简化处理，只返回生成的数据
        
        cursor.close()
        conn.close()
        
        return {"code": 0, "data": {"nodes": graph_data.get("nodes", []), "links": graph_data.get("links", []), "categories": categories}}
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成知识图谱失败: {str(e)}")

@router.post("/generate-learning-report")
async def generate_learning_report(data: dict = Body(...)):
    try:
        userId = data.get("userId", 1)
        course = data.get("course", "408")
        
        conn = get_conn()
        cursor = conn.cursor()
        
        # 获取用户的笔记数据
        cursor.execute(
            """
            SELECT id, title, content
            FROM zhinote_notes
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 10
            """,
            (userId,)
        )
        notes = cursor.fetchall()
        
        if not notes:
            raise HTTPException(status_code=404, detail="未找到用户笔记")
        
        # 构建笔记内容字符串
        notes_content = ""
        for note_id, title, content in notes:
            notes_content += f"笔记标题: {title}\n"
            notes_content += f"笔记内容: {content[:500]}\n\n"
        
        # 调用阿里云通义千问大模型生成学习报告数据
        import dashscope
        from dashscope import Generation
        from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL
        
        dashscope.api_key = DASHSCOPE_API_KEY
        
        prompt = f"""请根据以下用户笔记内容，生成一份学习报告数据。

要求：
1. 分析考点热度，生成考点名称和出现次数
2. 分析学习趋势，生成过去30天的学习时长数据
3. 分析知识点掌握度，生成各个知识领域的掌握程度
4. 分析章节学习时间分布，生成各章节的学习时间
5. 分析笔记内容分类占比，生成各分类的占比
6. 分析每周平均专注度，生成过去12周的专注度数据
7. 分析高频关键词，生成关键词和出现次数
8. 请严格按照以下JSON格式输出，不要包含任何其他内容：
{{
  "heatData": [
    {{"name": "考点名称", "value": 出现次数}},
    ...
  ],
  "trendData": [学习时长数据数组，共30个元素],
  "radarData": {{
    "indicator": [
      {{"name": "知识领域名称", "max": 100}},
      ...
    ],
    "value": [掌握程度数组]
  }},
  "chapterData": {{
    "categories": ["章节名称数组"],
    "values": [学习时间数组]
  }},
  "categoryData": [
    {{"name": "分类名称", "value": 占比}},
    ...
  ],
  "focusData": [专注度数据数组，共12个元素],
  "wordCloudData": [
    {{"name": "关键词", "value": 出现次数}},
    ...
  ]
}}

课程：{course}

用户笔记内容：
{notes_content}
"""
        
        response = Generation.call(
            model=DASHSCOPE_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的学习分析助手，能够根据用户笔记内容生成详细的学习报告数据。"},
                {"role": "user", "content": prompt}
            ],
            result_format="message"
        )
        
        # 获取生成的学习报告数据
        report_data_text = response.output.choices[0].message.content
        
        # 解析JSON
        import json
        import re
        
        # 提取JSON
        json_match = re.search(r'\{.*\}', report_data_text, re.DOTALL)
        if not json_match:
            raise HTTPException(status_code=500, detail="生成的学习报告数据格式错误")
        
        report_data = json.loads(json_match.group())
        
        cursor.close()
        conn.close()
        
        return {"code": 0, "data": report_data}
    
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"生成学习报告失败: {str(e)}")
