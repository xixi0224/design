import json
import re
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, Request
from typing import List, Dict, Any
from app.db import get_conn
from app.services.ai_service import ai_analyze_text
from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL
import dashscope
from dashscope import Generation

dashscope.api_key = DASHSCOPE_API_KEY

router = APIRouter(tags=["ai"])

@router.post("/ai/class-summary")
async def class_summary(data: Dict[str, Any] = Body(...)):
    try:
        fileId = data.get("fileId")
        
        # 从数据库中获取真实的笔记内容
        conn = get_conn()
        cursor = conn.cursor()
        
        # 查询笔记内容（从zhinote_notes表）
        cursor.execute(
            "SELECT title, content FROM zhinote_notes WHERE id = %s",
            (fileId,)
        )
        note = cursor.fetchone()
        
        if not note:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="笔记不存在")
        
        title, content = note
        
        analysis_result = ai_analyze_text(content, title)

        try:
            analysis_data = json.loads(analysis_result)
            if isinstance(analysis_data, dict):
                analysis_data = [analysis_data]
        except Exception as parse_err:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=500, detail=f"AI分析结果解析失败: {str(parse_err)}")

        # 生成课程大纲
        outline = []
        for i, item in enumerate(analysis_data):
            outline.append({
                'title': f"{i+1}. {item.get('section', '未命名章节')}",
                'subtopics': []
            })

        # 生成每章摘要
        chapterSummaries = [
            {
                "chapter": item.get('section', '未命名章节'),
                "summary": item.get('summary', '暂无摘要')
            }
            for item in analysis_data
        ]

        # 生成重点整理
        keypoints = []
        for item in analysis_data:
            keywords = item.get('keywords', [])
            if isinstance(keywords, list):
                keypoints.extend(keywords)
            elif isinstance(keywords, str):
                keypoints.append(keywords)
        keypoints = list(set(keypoints))[:10]
        keypoints = [{'text': item} for item in keypoints]

        # 难点分析基于AI返回的summary中有"难点"、"困难"等关键词的条目生成
        difficulties = []
        for item in analysis_data:
            summary = item.get('summary', '')
            section = item.get('section', '')
            if any(kw in summary for kw in ['难点', '困难', '复杂', '抽象', '易错', '混淆']):
                difficulties.append({'title': section, 'explanation': summary})
        if not difficulties and analysis_data:
            # 如果没有明确标记难点的，默认取最后一个作为难点
            last = analysis_data[-1]
            difficulties.append({'title': last.get('section', '总结'), 'explanation': last.get('summary', '')})
        
        cursor.close()
        conn.close()
        
        # 返回真实的课堂总结数据
        return {
            "code": 0,
            "data": {
                "outline": outline,
                "chapterSummaries": chapterSummaries,
                "keypoints": keypoints,
                "difficulties": difficulties
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"课堂总结失败: {str(e)}")

@router.post("/ai/generate-summary-image")
async def generate_summary_image(data: Dict[str, Any] = Body(...)):
    try:
        classSummary = data.get("classSummary")
        
        # 导入PIL库生成摘要图
        from PIL import Image, ImageDraw, ImageFont
        import io
        import base64
        import os
        
        # 创建一个白色背景的图片
        width, height = 800, 1200
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # 尝试加载中文字体，如果失败则使用默认字体
        font = None
        title_font = None
        section_font = None
        
        try:
            # 尝试加载Windows系统字体
            import os
            font_paths = [
                "C:\\Windows\\Fonts\\simhei.ttf",  # 黑体字体
                "C:\\Windows\\Fonts\\simsun.ttc",  # 宋体字体
                "C:\\Windows\\Fonts\\msyh.ttf",   # 微软雅黑字体
                "C:\\Windows\\Fonts\\msyhbd.ttf",  # 微软雅黑粗体字体
                "C:\\Windows\\Fonts\\simkai.ttf",  # 楷体字体
                "C:\\Windows\\Fonts\\arial.ttf",  # Arial字体
                "C:\\Windows\\Fonts\\times.ttf"    # Times New Roman字体
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, 24)
                        title_font = ImageFont.truetype(font_path, 32)
                        section_font = ImageFont.truetype(font_path, 28)
                        print(f"成功加载字体: {font_path}")
                        break
                    except Exception as e:
                        print(f"加载字体 {font_path} 失败: {e}")
                        continue
        except Exception as e:
            print(f"字体加载失败: {e}")
        
        # 如果所有字体都加载失败，使用默认字体
        if not font:
            print("使用默认字体")
            font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            section_font = ImageFont.load_default()
        
        # 绘制标题
        draw.text((50, 50), "AI课堂总结", font=title_font, fill='black')
        
        # 绘制课程大纲
        y = 120
        draw.text((50, y), "课程大纲", font=section_font, fill='black')
        y += 30
        if classSummary and 'outline' in classSummary:
            for item in classSummary['outline'][:5]:  # 只显示前5个大纲项
                draw.text((70, y), f"• {item.get('title', '')}", font=font, fill='black')
                y += 30
        
        # 绘制重点整理
        y += 50
        draw.text((50, y), "重点整理", font=section_font, fill='black')
        y += 30
        if classSummary and 'keypoints' in classSummary:
            for item in classSummary['keypoints'][:5]:  # 只显示前5个重点
                draw.text((70, y), f"• {item.get('text', '')}", font=font, fill='black')
                y += 30
        
        # 绘制难点分析
        y += 50
        draw.text((50, y), "难点分析", font=section_font, fill='black')
        y += 30
        if classSummary and 'difficulties' in classSummary:
            for item in classSummary['difficulties'][:5]:  # 只显示前5个难点
                draw.text((70, y), f"• {item.get('title', '')}", font=font, fill='black')
                y += 30
        
        # 将图片转换为base64编码
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # 返回base64编码的图片
        return {
            "code": 0,
            "data": {
                "imageUrl": f"data:image/png;base64,{img_str}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"生成摘要图失败: {str(e)}")

@router.post("/ai/content-compress")
async def content_compress(data: Dict[str, Any] = Body(...)):
    try:
        fileId = data.get("fileId")
        
        # 从数据库中获取真实的笔记内容
        conn = get_conn()
        cursor = conn.cursor()
        
        # 查询笔记内容（从zhinote_notes表）
        cursor.execute(
            "SELECT title, content FROM zhinote_notes WHERE id = %s",
            (fileId,)
        )
        note = cursor.fetchone()
        
        if not note:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="文档不存在")
        
        title, content = note
        
        if not content or len(content) < 10 or not any(c.isalpha() for c in content):
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="文档内容为空或无效，无法进行内容压缩")

        prompt = f"请将以下内容压缩为简洁的摘要，保持核心信息，按照要点形式输出，每个要点以数字序号开头，如'1. '：\n{content[:1000]}"

        response = Generation.call(
            model=DASHSCOPE_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的内容压缩助手，能够将长文本压缩为简洁的摘要。请按照要点形式输出，每个要点以数字序号开头，如'1. '，确保内容清晰、条理分明。"},
                {"role": "user", "content": prompt}
            ],
            result_format="message"
        )

        compressed_text = response.output.choices[0].message.content

        if not compressed_text or len(compressed_text) < 10:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=500, detail="AI内容压缩结果为空，请稍后重试")
        
        # 构建压缩内容
        # 将压缩后的文本按换行符分割成列表
        points = [line.strip() for line in compressed_text.split('\n') if line.strip()]
        
        # 确保标题合理
        if not title or len(title) < 5 or not any(c.isalpha() for c in title):
            title = "一页纸精华笔记"
        
        compressedContent = {
            "title": f"压缩后的{title}",
            "sections": [
                {
                    "title": "核心内容",
                    "points": points
                }
            ]
        }
        
        cursor.close()
        conn.close()
        
        return {
            "code": 0,
            "data": {
                "compressedContent": compressedContent,
                "originalContent": content
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"内容压缩失败: {str(e)}")

@router.post("/ai/save-compressed-version")
async def save_compressed_version(data: Dict[str, Any] = Body(...)):
    try:
        title = data.get("title")
        content = data.get("content")

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO zhinote_notes (title, content, created_at) VALUES (%s, %s, NOW())",
            (title or "压缩笔记", json.dumps(content, ensure_ascii=False) if isinstance(content, dict) else str(content))
        )
        note_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "code": 0,
            "data": {
                "noteId": note_id,
                "title": title
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存压缩版本失败: {str(e)}")

@router.post("/ai/extract-exam-points")
async def extract_exam_points(data: Dict[str, Any] = Body(...)):
    try:
        fileId = data.get("fileId")

        conn = get_conn()
        cursor = conn.cursor()

        # 查询笔记内容（从zhinote_notes表）
        cursor.execute(
            "SELECT title, content FROM zhinote_notes WHERE id = %s",
            (fileId,)
        )
        note = cursor.fetchone()

        if not note:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="文档不存在")

        title, content = note

        if not content or len(content) < 10 or not any(c.isalpha() for c in content):
            cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="文档内容为空或无效")

        # 判断内容类型：普通笔记 vs 试卷/试题
        is_exam_paper = any(kw in content[:500] for kw in [
            "选择题", "填空题", "判断题", "简答题", "一、", "二、", "1.", "2.",
            "A.", "B.", "C.", "D.", "答案", "解析", "得分", "总分", "考试时间"
        ])

        content_hint = "这是一份试卷/试题内容。" if is_exam_paper else "这是一份学习笔记/讲义内容。"

        prompt = f"""你是一个专业的考试内容分析助手。请仔细分析以下内容，识别出其中的高频考点和关键知识点。

{content_hint}

分析要求：
1. 识别5-10个考点，每个考点必须包含：
   - name: 考点名称（简洁明了，5-15字）
   - importance: 重要程度（1-5的整数，5星为最高频/最重要考点）
   - questionTypes: 易考题型数组，必须从以下标准题型中选择：
     * 选择题（含单选题、多选题）
     * 填空题
     * 判断题
     * 简答题
     * 计算题
     * 编程题
     * 论述题
     * 名词解释
     * 综合应用题
     * 案例分析题
   - location: 该考点在内容中的大致位置或出处描述

2. 如果是试卷/试题内容，请重点分析：
   - 各考点对应的题型分布（同一考点可能对应多种题型）
   - 高频重复出现的考点给予更高的importance
   - 注意区分易混淆的相似考点

3. 请严格按照以下JSON数组格式输出，不要包含任何markdown代码块标记，不要包含任何其他文字：
[
  {{"name": "考点名称", "importance": 5, "questionTypes": ["选择题", "填空题"], "location": "第1章 绪论"}},
  ...
]

内容标题：{title}
内容：
{content[:3000]}"""

        response = Generation.call(
            model=DASHSCOPE_MODEL,
            messages=[
                {"role": "system", "content": "你是一个严谨的考试分析专家。请严格按照用户要求的JSON数组格式输出考点列表，只输出JSON，不要输出任何解释文字、markdown标记或代码块。"},
                {"role": "user", "content": prompt}
            ],
            result_format="message",
            response_format={"type": "json_object"}
        )

        exam_points_text = response.output.choices[0].message.content
        print(f"[考点识别] AI原始返回: {exam_points_text[:500]}")

        # 尝试解析JSON
        exam_points_data = None

        # 先尝试直接解析
        try:
            parsed = json.loads(exam_points_text)
            if isinstance(parsed, list):
                exam_points_data = parsed
            elif isinstance(parsed, dict):
                for key in ["exam_points", "examPoints", "data", "results", "考点", "list", "items"]:
                    if key in parsed and isinstance(parsed[key], list):
                        exam_points_data = parsed[key]
                        break
                if exam_points_data is None:
                    exam_points_data = [parsed]
        except Exception as e:
            print(f"[考点识别] JSON直接解析失败: {e}")

        # 如果直接解析失败，用正则提取JSON数组
        if exam_points_data is None:
            json_match = re.search(r'\[.*\]', exam_points_text, re.DOTALL)
            if json_match:
                try:
                    exam_points_data = json.loads(json_match.group())
                except Exception as e:
                    print(f"[考点识别] 正则提取JSON数组失败: {e}")
                    exam_points_data = []
            else:
                exam_points_data = []

        print(f"[考点识别] 解析后数据条数: {len(exam_points_data)}")

        # 字段名映射：兼容中英文及常见变体
        def _get_field(point, *keys):
            for k in keys:
                if k in point:
                    return point[k]
            return ""

        examPoints = []
        for i, point in enumerate(exam_points_data):
            if not isinstance(point, dict):
                continue

            name = _get_field(point, "name", "考点名称", "考点", "title", "content", "主题")
            if not name or not str(name).strip():
                continue

            importance_raw = _get_field(point, "importance", "重要程度", "重要度", "星级", "priority")
            try:
                importance = int(importance_raw)
                if importance < 1:
                    importance = 1
                elif importance > 5:
                    importance = 5
            except Exception:
                importance = 3

            question_types = _get_field(point, "questionTypes", "question_types", "types", "易考题型", "题型", "questionType")
            if isinstance(question_types, str):
                question_types = [t.strip() for t in question_types.replace("、", ",").replace("/", ",").split(",") if t.strip()]
            elif not isinstance(question_types, list):
                question_types = []

            location = _get_field(point, "location", "出现位置", "位置", "出处", "章节", "section")

            print(f"[考点识别] 第{i+1}条: name={name}, importance={importance}, types={question_types}, location={location}")

            examPoints.append({
                "id": i + 1,
                "name": str(name),
                "importance": importance,
                "questionTypes": question_types,
                "location": str(location)
            })

        if not examPoints:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=500, detail="未能识别出考点，请稍后重试")

        # 将考点结果存入 zhinote_analysis 表，供学习报告使用
        try:
            # 先清理该文档已有的考点分析数据
            cursor.execute("DELETE FROM zhinote_analysis WHERE doc_id = %s", (fileId,))

            for point in examPoints:
                cursor.execute(
                    """
                    INSERT INTO zhinote_analysis
                    (doc_id, section, summary, keywords, is_exam_point, importance)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        fileId,
                        point["name"],
                        point["location"],
                        json.dumps(point["questionTypes"], ensure_ascii=False),
                        1,
                        point["importance"]
                    )
                )
            conn.commit()
        except Exception as db_err:
            # 写入数据库失败不影响返回考点结果给前端
            print(f"考点写入数据库失败: {db_err}")
            conn.rollback()

        cursor.close()
        conn.close()

        return {
            "code": 0,
            "data": {
                "examPoints": examPoints
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"考点识别失败: {str(e)}")

@router.post("/ai/extract-knowledge")
async def extract_knowledge(data: Dict[str, Any] = Body(...)):
    try:
        fileId = data.get("fileId")
        
        # 从数据库中获取真实的笔记内容
        conn = get_conn()
        cursor = conn.cursor()
        
        # 查询笔记内容（从zhinote_notes表）
        cursor.execute(
            "SELECT title, content FROM zhinote_notes WHERE id = %s",
            (fileId,)
        )
        note = cursor.fetchone()
        
        if not note:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="文档不存在")
        
        title, content = note
        
        prompt = f"""你是一个专业的知识点提取助手。请从以下内容中提取出主要的知识点。

要求：
1. 提取5-10个核心知识点
2. 每个知识点包含：知识点名称（title）和简要描述（detail）
3. 标注每个知识点所属的章节（chapter）
4. 只输出JSON格式：
{{
  "knowledgeList": [
    {{"title": "知识点名称", "detail": "描述", "chapter": "所属章节"}}
  ],
  "chapters": ["章节1", "章节2"],
  "keywords": [
    {{"word": "关键词", "weight": 10}}
  ]
}}

内容：
{content[:1500]}"""

        response = Generation.call(
            model=DASHSCOPE_MODEL,
            messages=[
                {"role": "system", "content": "你是一个严谨的教育AI助手，只输出JSON。"},
                {"role": "user", "content": prompt}
            ],
            result_format="message",
            response_format={"type": "json_object"}
        )
        
        knowledge_text = response.output.choices[0].message.content
        
        # 解析JSON格式的知识点提取结果
        knowledgeList = []
        chapters = []
        keywords = []

        try:
            parsed = json.loads(knowledge_text)
            if isinstance(parsed, dict):
                knowledgeList = parsed.get("knowledgeList", [])
                chapters = parsed.get("chapters", [])
                keywords = parsed.get("keywords", [])
            elif isinstance(parsed, list):
                knowledgeList = parsed
        except Exception:
            # 如果JSON解析失败，尝试正则提取
            json_match = re.search(r'\{.*\}', knowledge_text, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    knowledgeList = parsed.get("knowledgeList", [])
                    chapters = parsed.get("chapters", [])
                    keywords = parsed.get("keywords", [])
                except Exception:
                    pass

        # 为知识点添加id
        for i, item in enumerate(knowledgeList):
            item["id"] = i + 1
            if "content" not in item:
                item["content"] = item.get("detail", "")
            if "difficulty" not in item:
                item["difficulty"] = "中等"

        if not chapters and knowledgeList:
            chapters = list(set([item.get("chapter", "核心概念") for item in knowledgeList if item.get("chapter")]))

        if not keywords and knowledgeList:
            # 从知识点标题生成简单的关键词
            keywords = []
            for i, item in enumerate(knowledgeList[:8]):
                keywords.append({"word": item.get("title", ""), "weight": max(5, 20 - i * 2)})

        cursor.close()
        conn.close()

        return {
            "code": 0,
            "data": {
                "knowledgeList": knowledgeList,
                "chapters": chapters,
                "keywords": keywords
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识点提取失败: {str(e)}")

@router.post("/library/add-knowledge")
async def add_knowledge(data: Dict[str, Any] = Body(...)):
    try:
        knowledge = data.get("knowledge")
        if not knowledge:
            raise HTTPException(status_code=400, detail="知识点不能为空")

        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO zhinote_notes (title, content, created_at)
            VALUES (%s, %s, NOW())
            """,
            (knowledge.get("title", "知识库笔记"), knowledge.get("detail", ""))
        )
        note_id = cursor.lastrowid
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "code": 0,
            "data": {
                "success": True,
                "noteId": note_id
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加知识点失败: {str(e)}")

@router.post("/ai/add-to-review-plan")
async def add_to_review_plan(data: Dict[str, Any] = Body(...)):
    try:
        examPoint = data.get("examPoint")
        if not examPoint:
            raise HTTPException(status_code=400, detail="考点不能为空")

        # 如果考点已掌握，不需要加入复习计划
        if examPoint.get("isMastered"):
            return {
                "code": 0,
                "data": {
                    "success": False,
                    "message": "该考点已掌握，无需加入复习计划"
                }
            }

        conn = get_conn()
        cursor = conn.cursor()

        # 查找最新的学习计划（接口对齐：learning_plan.py 也用 ORDER BY created_at DESC LIMIT 1）
        cursor.execute(
            """
            SELECT id, plan_data FROM zhinote_learning_plans
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        plan = cursor.fetchone()

        if not plan:
            cursor.close()
            conn.close()
            raise HTTPException(status_code=404, detail="当前没有进行中的学习计划，请先创建学习计划")

        plan_id, plan_data_str = plan
        try:
            plan_data = json.loads(plan_data_str) if isinstance(plan_data_str, str) else plan_data_str
        except Exception:
            plan_data = []

        # 确保 plan_data 是列表
        if not isinstance(plan_data, list):
            plan_data = []

        # 将考点作为新任务添加到今天的任务中
        today_str = datetime.now().strftime("%Y-%m-%d")
        task_added = False
        # 生成唯一任务ID（用时间戳，避免与AI生成的正数ID冲突）
        unique_id = int(datetime.now().timestamp() * 1000) % 1000000000

        for day in plan_data:
            if isinstance(day, dict) and day.get("date") == today_str:
                tasks = day.get("tasks", [])
                # 检查是否已存在相同考点，避免重复添加
                already_exists = any(
                    t.get("name", "").endswith(f"复习考点：{examPoint.get('name', '')}")
                    for t in tasks
                )
                if not already_exists:
                    tasks.append({
                        "id": unique_id,
                        "name": f"复习考点：{examPoint.get('name', '')}",
                        "completed": False,
                        "isExamPoint": True
                    })
                    day["tasks"] = tasks
                task_added = True
                break

        if not task_added:
            # 如果今天没有计划，创建一个新的当天计划条目
            plan_data.append({
                "date": today_str,
                "weekday": "",
                "tasks": [{
                    "id": unique_id,
                    "name": f"复习考点：{examPoint.get('name', '')}",
                    "completed": False,
                    "isExamPoint": True
                }]
            })

        cursor.execute(
            "UPDATE zhinote_learning_plans SET plan_data = %s WHERE id = %s",
            (json.dumps(plan_data, ensure_ascii=False), plan_id)
        )
        conn.commit()
        cursor.close()
        conn.close()

        return {
            "code": 0,
            "data": {
                "success": True,
                "message": "已加入当日学习计划"
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"添加到复习计划失败: {str(e)}")

@router.post("/asr/convert")
async def asr_convert(data: Dict[str, Any] = Body(...)):
    try:
        fileId = data.get("fileId")
        
        # 从数据库获取音频文件路径
        conn = None
        cursor = None
        audio_path = None
        try:
            from app.db import get_conn
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT file_path FROM zhinote_audio_files WHERE id = %s",
                (fileId,)
            )
            result = cursor.fetchone()
            if result:
                audio_path = result[0]
                print(f"找到音频文件: {audio_path}")
            else:
                # 如果数据库中没有找到，尝试从uploads目录中直接查找
                print(f"数据库中未找到音频文件，fileId: {fileId}")
                # 这里可以添加备选逻辑，比如根据fileId生成文件名
        except Exception as db_error:
            print(f"数据库查询失败: {db_error}")
            # 数据库查询失败时，仍然尝试进行语音转文字
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        # 检查音频文件是否存在
        import os
        if not audio_path or not os.path.exists(audio_path):
            # 如果没有找到音频文件，尝试从uploads目录中查找
            import glob
            uploads_dir = "uploads"
            audio_files = glob.glob(f"{uploads_dir}/*.m4a") + glob.glob(f"{uploads_dir}/*.mp3") + glob.glob(f"{uploads_dir}/*.wav")
            if audio_files:
                # 取最新的音频文件
                audio_files.sort(key=os.path.getmtime, reverse=True)
                audio_path = audio_files[0]
                print(f"使用最新的音频文件: {audio_path}")
            else:
                print("没有找到音频文件")
                raise HTTPException(status_code=404, detail="音频文件不存在")
        
        # 调用真实的语音转文字服务
        from app.services.ai_analysis_service import asr_service
        try:
            print(f"开始调用语音转文字服务: {audio_path}")
            transcript_text = asr_service(audio_path)
            print(f"语音转文字结果: {transcript_text}")
            # 处理转写结果
            transcript = []
            if transcript_text:
                # 简单分割文本，实际应该根据时间戳分割
                sentences = transcript_text.split('。')
                start_time = 0
                for i, sentence in enumerate(sentences):
                    if sentence.strip():
                        end_time = start_time + 3  # 假设每句3秒
                        transcript.append({
                            "text": sentence.strip() + '。',
                            "start_time": start_time,
                            "end_time": end_time
                        })
                        start_time = end_time
            
            print(f"处理后的转写结果: {transcript}")
            if not transcript:
                # 如果转写结果为空，返回错误信息
                return {
                    "code": 0,
                    "data": {
                        "transcript": [
                            {"text": "语音转文字成功，但是没有检测到内容。", "start_time": 0, "end_time": 3}
                        ]
                    }
                }
            
            return {
                "code": 0,
                "data": {
                    "transcript": transcript
                }
            }
        except Exception as asr_error:
            print(f"语音转文字失败: {asr_error}")
            # 如果语音转文字失败，返回错误信息
            return {
                "code": 0,
                "data": {
                    "transcript": [
                        {"text": f"语音转文字失败: {str(asr_error)}", "start_time": 0, "end_time": 3}
                    ]
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        print(f"语音转文字接口异常: {e}")
        # 返回错误信息
        return {
            "code": 0,
            "data": {
                "transcript": [
                    {"text": f"语音转文字失败: {str(e)}", "start_time": 0, "end_time": 3}
                ]
            }
        }

@router.get("/asr/get-transcript")
async def get_transcript(fileId: int):
    try:
        conn = get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT transcript_text, status FROM zhinote_audio_records WHERE id = %s",
            (fileId,)
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return {
                "code": 0,
                "data": {
                    "transcript": []
                }
            }

        transcript_text, status = row
        if not transcript_text or status != "processed":
            return {
                "code": 0,
                "data": {
                    "transcript": []
                }
            }

        # 将全文按句号分段，模拟时间戳
        sentences = [s.strip() for s in str(transcript_text).split("。") if s.strip()]
        transcript = []
        start_time = 0
        for s in sentences:
            duration = max(2, len(s) // 5)
            transcript.append({
                "text": s + "。",
                "start_time": start_time,
                "end_time": start_time + duration
            })
            start_time += duration

        return {
            "code": 0,
            "data": {
                "transcript": transcript
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取转写内容失败: {str(e)}")

@router.post("/asr/save-tags")
async def save_tags(data: Dict[str, Any] = Body(...)):
    try:
        segmentIndex = data.get("segmentIndex")
        tags = data.get("tags")
        # 标签功能暂由前端本地维护，后续可扩展为数据库存储
        return {
            "code": 0,
            "data": {
                "success": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存标签失败: {str(e)}")

@router.post("/upload-audio")
async def upload_audio(request: Request):
    try:
        # 处理文件上传
        form = await request.form()
        audio_file = form.get("audio")
        
        if not audio_file:
            raise HTTPException(status_code=400, detail="未上传音频文件")
        
        # 保存文件到本地
        import os
        import uuid
        
        # 创建上传目录
        upload_dir = "uploads"
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
            print(f"创建上传目录: {upload_dir}")
        
        # 使用原始文件名
        file_name = audio_file.filename
        # 确保文件名唯一
        base_name, file_ext = os.path.splitext(file_name)
        counter = 1
        while os.path.exists(os.path.join(upload_dir, file_name)):
            file_name = f"{base_name}_{counter}{file_ext}"
            counter += 1
        file_path = os.path.join(upload_dir, file_name)
        
        # 保存文件
        print(f"开始保存文件: {file_path}")
        print(f"文件大小: {audio_file.size} bytes")
        with open(file_path, "wb") as f:
            content = await audio_file.read()
            f.write(content)
            print(f"写入文件大小: {len(content)} bytes")
        
        # 检查文件是否保存成功
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"文件保存成功，大小: {file_size} bytes")
        else:
            print("文件保存失败，文件不存在")
        
        # 保存到数据库，获取audio_id
        conn = None
        cursor = None
        audio_id = None
        try:
            from app.db import get_conn
            conn = get_conn()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO zhinote_audio_files (file_name, file_path, created_at)
                VALUES (%s, %s, NOW())
                """,
                (file_name, file_path)
            )
            audio_id = cursor.lastrowid
            conn.commit()
            print(f"数据库保存成功，audio_id: {audio_id}")
        except Exception as db_error:
            print(f"数据库保存失败: {db_error}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        
        # 构建可访问的URL路径
        import urllib.parse
        # 将反斜杠替换为正斜杠
        url_path = file_path.replace('\\', '/')
        # 编码文件路径
        encoded_path = urllib.parse.quote(url_path)
        # 构建完整的URL
        file_url = f"/api/audio/{encoded_path}"
        
        # 返回文件URL和audio_id
        return {
            "code": 0,
            "data": {
                "filePath": file_url,
                "audioId": audio_id or 1
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"上传音频异常: {e}")
        raise HTTPException(status_code=500, detail=f"上传音频失败: {str(e)}")


@router.get("/audio/{file_path:path}")
async def serve_audio(file_path: str):
    """提供音频文件访问"""
    try:
        import os
        import urllib.parse
        
        # 解码文件路径
        decoded_path = urllib.parse.unquote(file_path)
        print(f"请求音频文件: {decoded_path}")
        
        # 检查文件是否存在
        if not os.path.exists(decoded_path):
            raise HTTPException(status_code=404, detail="音频文件不存在")
        
        # 读取文件内容
        with open(decoded_path, "rb") as f:
            content = f.read()
        
        # 根据文件扩展名设置MIME类型
        file_ext = decoded_path.split('.')[-1].lower()
        mime_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'm4a': 'audio/mp4'
        }
        mime_type = mime_types.get(file_ext, 'application/octet-stream')
        
        # 返回文件内容
        return Response(
            content=content,
            media_type=mime_type
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"提供音频文件失败: {e}")
        raise HTTPException(status_code=500, detail="提供音频文件失败")
