import json
import os
import shutil
import dashscope
from dashscope import Generation
from datetime import datetime
from app.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL
from app.db import get_conn
from app.schemas.ai_analysis import AnalysisRequest, AnalysisResponse, ASRResponse, SummaryResponse, ExamPointResponse

dashscope.api_key = DASHSCOPE_API_KEY

def get_source_content(source_id: int, source_type: str):
    conn = get_conn()
    cursor = conn.cursor()

    if source_type == "document":
        cursor.execute("SELECT content FROM zhinote_documents WHERE id = %s", (source_id,))
    elif source_type == "audio":
        cursor.execute("SELECT filename FROM zhinote_audio_records WHERE id = %s", (source_id,))
    elif source_type == "text":
        cursor.execute("SELECT content FROM zhinote_text_inputs WHERE id = %s", (source_id,))
    else:
        raise ValueError("Invalid source type")

    result = cursor.fetchone()
    cursor.close()
    conn.close()

    if not result:
        raise ValueError("Source not found")

    return result[0]

def save_analysis_result(source_id: int, source_type: str, analysis_type: str, result: dict):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO zhinote_ai_analysis (source_id, source_type, analysis_type, result)
        VALUES (%s, %s, %s, %s)
        """,
        (source_id, source_type, analysis_type, json.dumps(result, ensure_ascii=False))
    )
    analysis_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return analysis_id

def analyze_content(request: AnalysisRequest):
    content = get_source_content(request.source_id, request.source_type)

    if request.analysis_type == "summary":
        result = generate_summary(content)
    elif request.analysis_type == "keywords":
        result = extract_keywords(content)
    elif request.analysis_type == "exam_points":
        result = identify_exam_points(content)
    else:
        raise ValueError("Invalid analysis type")

    analysis_id = save_analysis_result(request.source_id, request.source_type, request.analysis_type, result)

    return AnalysisResponse(
        id=analysis_id,
        source_id=request.source_id,
        source_type=request.source_type,
        analysis_type=request.analysis_type,
        result=result,
        created_at=datetime.now()
    )

def generate_summary(content: str):
    prompt = f"""
你是一个课程总结助手。请对以下内容生成简洁的课堂总结。

要求：
1. 总结长度：200字以内
2. 提取3-5个核心关键词
3. 识别主要知识点

只输出JSON，格式如下：
{{"summary": "总结内容", "keywords": ["关键词1", "关键词2", "关键词3"]}}

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
    return json.loads(response.output.choices[0].message.content)

def extract_keywords(content: str):
    prompt = f"""
你是一个关键词提取助手。请从以下内容中提取关键词。

要求：
1. 提取5-10个关键词
2. 按重要性排序
3. 只输出JSON数组格式：["关键词1", "关键词2", ...]

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
    return {"keywords": json.loads(response.output.choices[0].message.content)}

def identify_exam_points(content: str):
    prompt = f"""
你是一个考点分析助手。请从以下内容中识别可能的考试重点。

要求：
1. 识别5-10个可能的考点
2. 标注每个考点的重要性（高/中/低）
3. 只输出JSON格式：
{{"exam_points": [{{"content": "考点内容", "importance": "高", "reason": "识别理由"}}]}}

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
    return json.loads(response.output.choices[0].message.content)

def perform_asr(audio_id: int):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT filename, status FROM zhinote_audio_records WHERE id = %s", (audio_id,))
    result = cursor.fetchone()

    if not result:
        raise ValueError("Audio not found")

    audio_file, status = result
    audio_path = os.path.join("uploads/audio", audio_file)

    if not os.path.exists(audio_path):
        raise ValueError("Audio file not found")

    text = asr_service(audio_path)

    cursor.execute(
        "UPDATE zhinote_audio_records SET status = %s, transcript_text = %s WHERE id = %s",
        ("processed", text, audio_id)
    )
    conn.commit()
    cursor.close()
    conn.close()

    return ASRResponse(
        audio_id=audio_id,
        text=text,
        status="processed"
    )

def asr_service(audio_path: str):
    """
    使用百度云语音识别 API 进行语音转文本
    支持长音频自动分段识别（超过60秒）
    """
    from aip import AipSpeech
    from pydub import AudioSegment
    import io
    
    # 百度云应用信息
    API_KEY = 'HYPim6GzLxhPjBXIv11DRCt8'
    SECRET_KEY = '6Tiai01NZgTpU5cl4fvJMQBT92F2zuGY'
    APP_ID = '122981257'
    
    # 初始化百度云语音客户端
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)
    
    try:
        # 判断输入是 URL 还是本地文件路径
        is_url = audio_path.startswith('http://') or audio_path.startswith('https://')
        
        if is_url:
            # URL 识别：直接调用百度云 API
            print(f"使用 URL 进行语音识别: {audio_path}")
            
            result = client.asrUrl(audio_path, 'm4a', 16000, {
                'dev_pid': 1537,  # 中文普通话
            })
            
            print(f"百度云识别响应: {result}")
            
            if result.get('err_no') == 0 and 'result' in result:
                return ''.join(result['result'])
            else:
                raise Exception(f"ASR 识别失败: {result.get('err_msg', '识别失败')}")
        else:
            # 本地文件路径处理
            print(f"本地文件路径: {audio_path}")
            
            # 获取项目根目录
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            # 构建完整路径
            if not os.path.isabs(audio_path):
                full_path = os.path.join(project_root, audio_path)
            else:
                full_path = audio_path
            
            full_path = os.path.abspath(full_path)
            print(f"完整文件路径: {full_path}")
            
            # 检查文件是否存在
            if not os.path.exists(full_path):
                print(f"本地文件不存在: {full_path}")
                raise RuntimeError(f"音频文件不存在: {full_path}")
            
            print(f"文件存在，大小: {os.path.getsize(full_path)} bytes")
            
            # 使用 pydub 加载音频并获取时长
            audio = AudioSegment.from_file(full_path)
            duration_seconds = len(audio) / 1000.0  # pydub 返回毫秒
            print(f"音频时长: {duration_seconds:.2f} 秒")
            
            # 判断是否需要分段
            MAX_SEGMENT_DURATION = 55  # 每段最多55秒（留5秒余量）
            
            if duration_seconds <= MAX_SEGMENT_DURATION:
                # 短音频：直接识别
                print("短音频，直接识别...")
                
                # 读取音频数据
                with open(full_path, 'rb') as f:
                    audio_data = f.read()
                
                # 获取文件扩展名
                file_ext = os.path.splitext(full_path)[1].lower().replace('.', '')
                
                # 调用百度云 API
                result = client.asr(audio_data, file_ext, 16000, {
                    'dev_pid': 1537,  # 中文普通话
                })
                
                print(f"百度云识别响应: {result}")
                
                if result.get('err_no') == 0 and 'result' in result:
                    return ''.join(result['result'])
                else:
                    raise Exception(f"ASR 识别失败: {result.get('err_msg', '识别失败')}")
            else:
                # 长音频：分段处理
                print(f"长音频，需要分为 {int(duration_seconds // MAX_SEGMENT_DURATION) + 1} 段处理")
                
                full_text = []
                num_segments = int(duration_seconds // MAX_SEGMENT_DURATION) + 1
                
                for i in range(num_segments):
                    # 计算分段起始和结束时间（毫秒）
                    start_time = i * MAX_SEGMENT_DURATION * 1000
                    end_time = min((i + 1) * MAX_SEGMENT_DURATION * 1000, len(audio))
                    
                    # 截取音频段
                    segment = audio[start_time:end_time]
                    segment_duration = len(segment) / 1000.0
                    
                    print(f"正在识别第 {i+1}/{num_segments} 段 (时长: {segment_duration:.2f}秒)...")
                    
                    # 将音频段导出为字节流
                    buffer = io.BytesIO()
                    file_ext = os.path.splitext(full_path)[1].lower().replace('.', '')
                    segment.export(buffer, format=file_ext)
                    audio_data = buffer.getvalue()
                    
                    # 调用百度云 API
                    result = client.asr(audio_data, file_ext, 16000, {
                        'dev_pid': 1537,
                    })
                    
                    print(f"第 {i+1} 段识别响应: {result}")
                    
                    if result.get('err_no') == 0 and 'result' in result:
                        full_text.append(''.join(result['result']))
                        print(f"第 {i+1} 段识别成功")
                    else:
                        print(f"第 {i+1} 段识别失败: {result.get('err_msg', '未知错误')}")
                
                # 合并所有段落的识别结果
                if full_text:
                    return ''.join(full_text)
                else:
                    raise Exception("所有分段识别均失败")
    
    except Exception as e:
        raise Exception(f"语音转文本失败：{e}")
