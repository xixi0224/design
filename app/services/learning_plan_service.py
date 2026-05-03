import json
from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL

def generate_learning_plan_service(exam_date: str, daily_hours: float, pending_tasks: str, exam_subject: str):
    """
    使用千问大模型生成学习计划
    """
    try:
        import dashscope
        from dashscope import Generation
        
        dashscope.api_key = DASHSCOPE_API_KEY
        
        # 构建提示词
        prompt = f"""
请为以下考试生成一个详细的学习计划：

考试科目：{exam_subject}
考试日期：{exam_date}
每日可用时间：{daily_hours}小时
待完成任务：{pending_tasks if pending_tasks else '无'}

要求：
1. 从今天开始，到考试前一天，每天安排具体的学习任务
2. 每天的任务数量根据每日可用时间合理安排，一般每小时1-2个任务
3. 任务内容要具体、可执行，如"复习数据结构-树"、"做算法题-动态规划"等
4. 考试前一周要安排模拟考试和重点复习
5. 考试前三天要安排轻松复习和休息
6. 每个任务包含：id（从1开始递增）、name（任务名称）、completed（默认false）
7. 返回格式必须是JSON数组，每个元素包含：date（日期，格式YYYY-MM-DD）、weekday（星期几）、tasks（任务列表）
8. 不要包含任何其他文字，只返回JSON数组

示例格式：
[
  {{
    "date": "2024-06-01",
    "weekday": "星期六",
    "tasks": [
      {{"id": 1, "name": "复习数据结构-树", "completed": false}},
      {{"id": 2, "name": "做算法题-动态规划", "completed": false}}
    ]
  }}
]
"""
        
        response = Generation.call(
            model=DASHSCOPE_MODEL,
            messages=[
                {"role": "system", "content": "你是一个专业的学习计划制定助手，能够根据考试时间、每日可用时间和待完成任务，生成科学合理的学习计划。请严格按照要求的JSON格式返回数据，不要包含任何其他文字。"},
                {"role": "user", "content": prompt}
            ],
            result_format="message"
        )
        
        plan_text = response.output.choices[0].message.content
        
        # 尝试解析JSON
        import re
        json_match = re.search(r'\[.*\]', plan_text, re.DOTALL)
        if json_match:
            plan_data = json.loads(json_match.group())
        else:
            # 如果无法解析，尝试直接解析
            try:
                plan_data = json.loads(plan_text)
            except:
                # 如果仍然失败，返回默认计划
                plan_data = generate_default_plan(exam_date, daily_hours, exam_subject)
        
        # 验证计划数据格式
        if not isinstance(plan_data, list):
            plan_data = generate_default_plan(exam_date, daily_hours, exam_subject)
        
        # 为每天添加考试科目
        for day in plan_data:
            day["examSubject"] = exam_subject
        
        return plan_data
        
    except Exception as e:
        print(f"生成学习计划失败: {e}")
        # 返回默认计划
        return generate_default_plan(exam_date, daily_hours, exam_subject)

def generate_default_plan(exam_date: str, daily_hours: float, exam_subject: str):
    """
    生成默认学习计划
    """
    from datetime import datetime, timedelta
    
    try:
        exam_datetime = datetime.strptime(exam_date, "%Y-%m-%d")
    except:
        exam_datetime = datetime.now() + timedelta(days=30)
    
    today = datetime.now()
    days_until_exam = (exam_datetime - today).days
    
    if days_until_exam <= 0:
        days_until_exam = 30
    
    plan_data = []
    task_id = 1
    
    # 基础任务模板
    base_tasks = [
        "复习基础知识",
        "做练习题",
        "整理笔记",
        "背诵重点",
        "模拟测试"
    ]
    
    # 考试科目相关任务
    subject_tasks = {
        "计算机408": [
            "复习数据结构",
            "复习算法",
            "复习操作系统",
            "复习计算机网络",
            "做数据结构题",
            "做算法题",
            "做操作系统题",
            "做网络题"
        ],
        "高等数学": [
            "复习微积分",
            "复习线性代数",
            "复习概率论",
            "做微积分题",
            "做线性代数题",
            "做概率论题"
        ],
        "大学英语": [
            "背单词",
            "做阅读理解",
            "练习听力",
            "练习写作",
            "翻译练习"
        ]
    }
    
    # 获取科目相关任务
    tasks = subject_tasks.get(exam_subject, base_tasks)
    
    # 生成每日计划
    for i in range(days_until_exam):
        current_date = today + timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][current_date.weekday()]
        
        # 计算当天任务数量
        num_tasks = int(daily_hours)
        if num_tasks < 1:
            num_tasks = 1
        if num_tasks > 8:
            num_tasks = 8
        
        # 生成当天任务
        day_tasks = []
        for j in range(num_tasks):
            task_name = tasks[(task_id - 1) % len(tasks)]
            day_tasks.append({
                "id": task_id,
                "name": task_name,
                "completed": False
            })
            task_id += 1
        
        # 确定状态
        status = "pending"
        if i == 0:
            status = "today"
        elif i < days_until_exam - 7:
            status = "pending"
        elif i < days_until_exam - 3:
            status = "review"
        else:
            status = "final"
        
        plan_data.append({
            "date": date_str,
            "weekday": weekday,
            "tasks": day_tasks,
            "status": status,
            "examSubject": exam_subject
        })
    
    return plan_data
