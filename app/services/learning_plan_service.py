import json
import re
from datetime import datetime
import dashscope
from dashscope import Generation
from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL

dashscope.api_key = DASHSCOPE_API_KEY

def generate_learning_plan_service(exam_date: str, daily_hours: float, pending_tasks: str, exam_subject: str):
    """
    使用千问大模型生成学习计划
    """
    today_str = datetime.now().strftime('%Y-%m-%d')

    prompt = f"""请为以下考试生成一个详细的学习计划：

考试科目：{exam_subject}
考试日期：{exam_date}
每日可用时间：{daily_hours}小时
待完成任务：{pending_tasks if pending_tasks else '无'}
今天日期：{today_str}

要求：
1. 从今天（{today_str}）开始，到考试前一天，每天安排具体的学习任务
2. 每天的任务数量根据每日可用时间合理安排，一般每小时1-2个任务
3. 任务内容要具体、可执行，结合考试科目和待完成任务来个性化安排
4. 考试前一周要安排模拟考试和重点复习
5. 考试前三天要安排轻松复习和休息
6. 每个任务包含：id（从1开始递增）、name（任务名称）、completed（默认false）
7. 返回格式必须是纯JSON数组，不要用markdown代码块包裹
8. 每个数组元素包含：date（日期，格式YYYY-MM-DD）、weekday（星期几）、tasks（任务列表）、status（今天为"today"，其他为"pending"）
9. 不要包含任何其他文字，只返回JSON数组

示例格式：
[
  {{
    "date": "{today_str}",
    "weekday": "星期一",
    "tasks": [
      {{"id": 1, "name": "复习{exam_subject}-基础概念", "completed": false}},
      {{"id": 2, "name": "做{exam_subject}-练习题", "completed": false}}
    ],
    "status": "today"
  }}
]
"""

    response = Generation.call(
        model=DASHSCOPE_MODEL,
        messages=[
            {"role": "system", "content": "你是一个专业的学习计划制定助手，能够根据考试时间、每日可用时间和待完成任务，生成科学合理的个性化学习计划。请严格按照要求的JSON格式返回数据，不要包含任何其他文字，不要用markdown代码块包裹。"},
            {"role": "user", "content": prompt}
        ],
        result_format="message"
    )

    plan_text = response.output.choices[0].message.content
    print(f"[学习计划] AI返回内容: {plan_text[:300]}...")

    # 清理可能的markdown代码块标记
    cleaned = plan_text.strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned)
        cleaned = re.sub(r'\s*```$', '', cleaned)
        cleaned = cleaned.strip()

    # 解析JSON
    json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
    if json_match:
        plan_data = json.loads(json_match.group())
    else:
        plan_data = json.loads(cleaned)

    # 验证格式
    if not isinstance(plan_data, list) or len(plan_data) == 0:
        raise ValueError("AI返回的学习计划格式错误，请重试")

    # 补全字段 & 修正星期
    weekday_map = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    for day in plan_data:
        day["examSubject"] = exam_subject
        # 用代码计算正确的星期，覆盖AI可能错误的值
        if day.get("date"):
            try:
                d = datetime.strptime(day["date"], "%Y-%m-%d")
                day["weekday"] = weekday_map[d.weekday()]
            except:
                pass
        if day.get("date") == today_str:
            day["status"] = "today"
        elif "status" not in day:
            day["status"] = "pending"
        for task in day.get("tasks", []):
            # 字段兼容：AI可能返回content而不是name
            if "name" not in task or not task["name"]:
                task["name"] = task.get("content", task.get("title", task.get("task", "未命名任务")))
            if "completed" not in task:
                task["completed"] = False

    print(f"[学习计划] 成功生成 {len(plan_data)} 天的学习计划")
    return plan_data
