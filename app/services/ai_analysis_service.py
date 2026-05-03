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
    使用语音识别 API 进行语音转文本
    优先使用科大讯飞，如果失败则使用百度云
    支持长音频自动分段识别（超过60秒）
    """
    import os
    import io
    from pydub import AudioSegment
    
    # 科大讯飞应用信息（请替换为你的密钥）
    XF_APPID = 'aeb3e48c'
    XF_APISecret = 'YTNINTI0MTA2NTQxNTkxYjM1OTk3NGJh'
    XF_APIKey = '398738e17522920aa9731b3bf2ff4988'
    
    # 百度云应用信息（备用）
    BAIDU_API_KEY = '2PaExHSADS0FsN0vjEKG4sTE'
    BAIDU_SECRET_KEY = 'XKt0lLx3ElKzVbwxGwXXKg1DoFpS23Pb'
    BAIDU_APP_ID = '7695620'
    
    try:
        # 判断输入是 URL 还是本地文件路径
        is_url = audio_path.startswith('http://') or audio_path.startswith('https://')
        
        if is_url:
            # URL 识别：使用百度云
            print(f"使用 URL 进行语音识别: {audio_path}")
            from aip import AipSpeech
            client = AipSpeech(BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)
            
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
            
            # 尝试使用科大讯飞 API
            if XF_APPID != 'YOUR_XF_APPID':
                print("使用科大讯飞 API 进行识别...")
                try:
                    return xunfei_asr(full_path, XF_APPID, XF_APISecret, XF_APIKey)
                except Exception as e:
                    print(f"科大讯飞 API 调用失败: {e}，尝试使用百度云...")
            
            # 使用百度云 API（备用）
            print("使用百度云 API 进行识别...")
            return baidu_asr(full_path, audio, duration_seconds, BAIDU_APP_ID, BAIDU_API_KEY, BAIDU_SECRET_KEY)
    
    except Exception as e:
        raise Exception(f"语音转文本失败：{e}")


def xunfei_asr(audio_path: str, appid: str, apisecret: str, apikey: str) -> str:
    """
    使用科大讯飞语音识别 API
    """
    import base64
    import hashlib
    import hmac
    import json
    import time
    from urllib.parse import urlencode
    import websocket
    
    # 读取音频文件
    with open(audio_path, 'rb') as f:
        audio_data = f.read()
    
    # 转换为 base64
    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
    
    # 构建请求参数
    business_args = {
        "aue": "raw",
        "auf": "audio/L16;rate=16000",
        "vcn": "xiaoyan",
        "tte": "utf8",
        "dwa": "wpgs"
    }
    
    common_args = {
        "app_id": appid
    }
    
    # 构建 WebSocket URL
    url = "wss://iat-api.xfyun.cn/v2/iat"
    host = "iat-api.xfyun.cn"
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())
    
    # 生成签名
    signature_origin = "host: " + host + "\n"
    signature_origin += "date: " + date + "\n"
    signature_origin += "GET /v2/iat HTTP/1.1"
    
    signature_sha = hmac.new(
        apisecret.encode('utf-8'), 
        signature_origin.encode('utf-8'), 
        digestmod=hashlib.sha256
    ).digest()
    signature_sha_base64 = base64.b64encode(signature_sha).decode('utf-8')
    
    authorization_origin = 'api_key="' + apikey + '", algorithm="hmac-sha256", headers="host date request-line", signature="' + signature_sha_base64 + '"'
    authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode('utf-8')
    
    # 构建完整 URL
    v = {
        "authorization": authorization,
        "date": date,
        "host": host
    }
    url = url + "?" + urlencode(v)
    
    # WebSocket 回调
    result = []
    error_msg = None
    
    def on_message(ws, message):
        nonlocal error_msg
        try:
            data = json.loads(message)
            if data.get('code') != 0:
                error_msg = f"识别错误: {data.get('message')}"
                ws.close()
                return
            
            if 'result' in data and 'ws' in data['result']:
                for item in data['result']['ws']:
                    if 'cw' in item:
                        for cw in item['cw']:
                            result.append(cw['w'])
        except Exception as e:
            error_msg = f"解析消息失败: {e}"
            ws.close()
    
    def on_error(ws, error):
        nonlocal error_msg
        error_msg = f"WebSocket 错误: {error}"
    
    def on_close(ws, close_status_code, close_msg):
        pass
    
    def on_open(ws):
        # 发送第一帧
        frame = {
            "common": common_args,
            "business": business_args,
            "data": {
                "status": 0,
                "format": "audio/L16;rate=16000",
                "encoding": "raw",
                "audio": audio_base64
            }
        }
        ws.send(json.dumps(frame))
        
        # 发送最后一帧
        frame["data"]["status"] = 2
        frame["data"]["audio"] = ""
        ws.send(json.dumps(frame))
    
    # 建立 WebSocket 连接
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    ws.run_forever()
    
    if error_msg:
        raise Exception(error_msg)
    
    if not result:
        raise Exception("科大讯飞识别结果为空")
    
    return ''.join(result)


def baidu_asr(full_path: str, audio, duration_seconds: float, app_id: str, api_key: str, secret_key: str) -> str:
    """
    使用百度云语音识别 API（备用）
    """
    from aip import AipSpeech
    
    # 初始化百度云语音客户端，设置超时时间
    client = AipSpeech(app_id, api_key, secret_key)
    client.setConnectionTimeoutInMillis(60000)  # 60秒连接超时
    client.setSocketTimeoutInMillis(60000)  # 60秒读取超时
    
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
        
        # 调用百度云 API，增加重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"调用百度云 API（尝试 {attempt + 1}/{max_retries}）...")
                result = client.asr(audio_data, file_ext, 16000, {
                    'dev_pid': 1537,  # 中文普通话
                })
                            
                print(f"百度云识别响应: {result}")
                            
                if result.get('err_no') == 0 and 'result' in result:
                    return ''.join(result['result'])
                else:
                    # 如果是限流错误，等待后重试
                    if result.get('err_no') == 3302:
                        print(f"API 限流，等待 2 秒后重试...")
                        import time
                        time.sleep(2)
                        continue
                    raise Exception(f"ASR 识别失败: {result.get('err_msg', '识别失败')}")
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"调用失败: {e}，等待 2 秒后重试...")
                    import time
                    time.sleep(2)
                else:
                    raise Exception(f"ASR 识别失败: {e}")
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
            
            # 调用百度云 API，增加重试机制
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    print(f"调用百度云 API（第 {i+1} 段，尝试 {attempt + 1}/{max_retries}）...")
                    result = client.asr(audio_data, file_ext, 16000, {
                        'dev_pid': 1537,
                    })
                    
                    print(f"第 {i+1} 段识别响应: {result}")
                    
                    if result.get('err_no') == 0 and 'result' in result:
                        full_text.append(''.join(result['result']))
                        print(f"第 {i+1} 段识别成功")
                        break
                    else:
                        # 如果是限流错误，等待后重试
                        if result.get('err_no') == 3302:
                            print(f"API 限流，等待 2 秒后重试...")
                            import time
                            time.sleep(2)
                            continue
                        print(f"第 {i+1} 段识别失败: {result.get('err_msg', '未知错误')}")
                        break
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"第 {i+1} 段调用失败: {e}，等待 2 秒后重试...")
                        import time
                        time.sleep(2)
                    else:
                        print(f"第 {i+1} 段所有重试失败: {e}")
        
        # 合并所有段落的识别结果
        if full_text:
            return ''.join(full_text)
        else:
            raise Exception("所有分段识别均失败")
