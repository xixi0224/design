import json
import dashscope
from dashscope import Generation
from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL

dashscope.api_key = DASHSCOPE_API_KEY

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
        model=DASHSCOPE_MODEL,
        messages=[
            {"role": "system", "content": "你是一个严谨的教育AI助手，只输出JSON。"},
            {"role": "user", "content": prompt}
        ],
        result_format="message",
        response_format={"type": "json_object"}
    )
    return response.output.choices[0].message.content