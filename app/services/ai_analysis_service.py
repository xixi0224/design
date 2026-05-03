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
    使用科大讯飞录音文件转写 API 进行语音转文本
    支持长音频（最长5小时）
    """
    import os
    import io
    import time
    import json
    import base64
    import hashlib
    import hmac
    from datetime import datetime
    from urllib.parse import urlencode
    import requests
    from pydub import AudioSegment
    
    # 科大讯飞应用信息（录音文件转写使用SecretKey）
    XF_APPID = 'aeb3e48c'
    XF_SecretKey = '7d7661435c437720c1fabeae8d028511'
    XF_APISecret = 'YTNINTI0MTA2NTQxNTkxYjM1OTk3NGJh'
    XF_APIKey = '398738e17522920aa9731b3bf2ff4988'
    
    try:
        # 判断输入是 URL 还是本地文件路径
        is_url = audio_path.startswith('http://') or audio_path.startswith('https://')
        full_path = None
        
        if is_url:
            # URL 输入：先下载到临时目录
            print(f"检测到URL: {audio_path}")
            
            # 创建临时目录
            import tempfile
            temp_dir = tempfile.mkdtemp()
            print(f"创建临时目录: {temp_dir}")
            
            # 从URL提取文件名
            import urllib.parse
            parsed_url = urllib.parse.urlparse(audio_path)
            filename = os.path.basename(parsed_url.path)
            full_path = os.path.join(temp_dir, filename)
            print(f"临时文件路径: {full_path}")
            
            # 下载文件
            print("开始下载文件...")
            response = requests.get(audio_path, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(full_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size = os.path.getsize(full_path)
            print(f"文件下载完成，大小: {file_size} bytes")
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
            
            print(f"文件存在,大小: {os.path.getsize(full_path)} bytes")
        
        # 使用科大讯飞录音文件转写 API（使用SecretKey而不是APISecret）
        result = xunfei_lfasr(full_path, XF_APPID, XF_SecretKey)
        
        # 如果是URL下载的临时文件，清理临时文件
        if is_url and os.path.exists(full_path):
            os.remove(full_path)
            print(f"清理临时文件: {full_path}")
        
        return result
    
    except Exception as e:
        raise Exception(f"语音转文本失败：{e}")


def xunfei_lfasr(audio_path: str, appid: str, apisecret: str) -> str:
    """
    使用科大讯飞录音文件转写 API (LFASR - Long Form ASR)
    支持 wav/flac/opus/m4a/mp3 格式,最长5小时
    严格按照官方Python3 demo实现
    """
    import os
    import time
    import json
    import base64
    import hashlib
    import hmac
    import requests
    
    # 获取文件名和大小
    file_name = os.path.basename(audio_path)
    file_size = os.path.getsize(audio_path)
    
    print(f"准备上传文件: {file_name}, 大小: {file_size} bytes")
    
    # 生成签名（严格按照科大讯飞官方Python3 demo实现）
    ts = str(int(time.time()))
    m2 = hashlib.md5()
    m2.update((appid + ts).encode('utf-8'))
    md5 = m2.hexdigest()
    md5 = bytes(md5, encoding='utf-8')
    # 以secret_key为key, 上面的md5为msg， 使用hashlib.sha1加密结果为signa
    signa = hmac.new(apisecret.encode('utf-8'), md5, hashlib.sha1).digest()
    signa = base64.b64encode(signa)
    signa = str(signa, 'utf-8')
    
    # 调试信息
    print(f"APPID: {appid}")
    print(f"时间戳: {ts}")
    print(f"BaseString: {appid + ts}")
    print(f"MD5 hexdigest: {md5.decode('utf-8')}")
    print(f"Signa: {signa}")
    
    # 步骤1: 预处理 - 创建任务
    print("步骤1: 创建转写任务...")
    prepare_url = 'https://raasr.xfyun.cn/api/prepare'
    prepare_data = {
        'app_id': appid,
        'signa': signa,
        'ts': ts,
        'file_len': str(file_size),
        'file_name': file_name,
        'slice_num': '1',  # 不分片,直接上传整个文件
        'language': 'cn',  # 中文
        'has_participle': 'false'
    }
    
    prepare_response = requests.post(prepare_url, data=prepare_data, timeout=30)
    prepare_result = prepare_response.json()
    print(f"预处理响应: {prepare_result}")
    
    if prepare_result.get('ok') != 0:
        raise Exception(f"创建任务失败: {prepare_result.get('failed')}")
    
    task_id = prepare_result.get('data')
    print(f"任务ID: {task_id}")
    
    # 步骤2: 上传文件
    print("步骤2: 上传音频文件...")
    upload_url = 'https://raasr.xfyun.cn/api/upload'
    
    # 重新生成签名（注意：所有接口都用 appid + ts，不用 task_id）
    ts = str(int(time.time()))
    m2 = hashlib.md5()
    m2.update((appid + ts).encode('utf-8'))
    md5 = m2.hexdigest()
    md5 = bytes(md5, encoding='utf-8')
    signa = hmac.new(apisecret.encode('utf-8'), md5, hashlib.sha1).digest()
    signa = base64.b64encode(signa)
    signa = str(signa, 'utf-8')
    
    # 读取文件
    with open(audio_path, 'rb') as f:
        file_content = f.read()
    
    upload_data = {
        'app_id': appid,
        'signa': signa,
        'ts': ts,
        'task_id': task_id,
        'slice_id': '1'  # 修正：切片ID从1开始
    }
    upload_files = {
        'content': (file_name, file_content, 'audio/mpeg')
    }
    
    upload_response = requests.post(upload_url, data=upload_data, files=upload_files, timeout=120)
    upload_result = upload_response.json()
    print(f"上传响应: {upload_result}")
    
    if upload_result.get('ok') != 0:
        raise Exception(f"上传文件失败: {upload_result.get('failed')}")
    
    # 步骤3: 合并文件 (虽然只有一个切片,但仍需调用merge)
    print("步骤3: 合并文件...")
    merge_url = 'https://raasr.xfyun.cn/api/merge'
    
    ts = str(int(time.time()))
    m2 = hashlib.md5()
    m2.update((appid + ts).encode('utf-8'))
    md5 = m2.hexdigest()
    md5 = bytes(md5, encoding='utf-8')
    signa = hmac.new(apisecret.encode('utf-8'), md5, hashlib.sha1).digest()
    signa = base64.b64encode(signa)
    signa = str(signa, 'utf-8')
    
    merge_data = {
        'app_id': appid,
        'signa': signa,
        'ts': ts,
        'task_id': task_id
    }
    
    merge_response = requests.post(merge_url, data=merge_data, timeout=30)
    merge_result = merge_response.json()
    print(f"合并响应: {merge_result}")
    
    if merge_result.get('ok') != 0:
        raise Exception(f"合并文件失败: {merge_result.get('failed')}")
    
    # 步骤4: 轮询查询进度
    print("步骤4: 等待转写完成...")
    get_progress_url = 'https://raasr.xfyun.cn/api/getProgress'
    
    max_wait = 600  # 最多等待10分钟
    wait_time = 0
    poll_interval = 10  # 每10秒查询一次
    
    while wait_time < max_wait:
        time.sleep(poll_interval)
        wait_time += poll_interval
        
        ts = str(int(time.time()))
        m2 = hashlib.md5()
        m2.update((appid + ts).encode('utf-8'))
        md5 = m2.hexdigest()
        md5 = bytes(md5, encoding='utf-8')
        signa = hmac.new(apisecret.encode('utf-8'), md5, hashlib.sha1).digest()
        signa = base64.b64encode(signa)
        signa = str(signa, 'utf-8')
        
        progress_data = {
            'app_id': appid,
            'signa': signa,
            'ts': ts,
            'task_id': task_id
        }
        
        progress_response = requests.post(get_progress_url, data=progress_data, timeout=30)
        progress_result = progress_response.json()
        
        status = progress_result.get('data', {}).get('status', -1)
        desc = progress_result.get('data', {}).get('desc', '')
        print(f"转写进度: status={status}, desc={desc}")
        
        if status == 4:  # 转写完成
            break
        elif status == 5:  # 转写失败
            raise Exception(f"转写失败: {desc}")
        # 其他状态继续等待 (0:排队中, 1:转写中, 2:转写完成, 3:已合并)
    
    if wait_time >= max_wait:
        raise Exception("转写超时,请稍后重试")
    
    # 步骤5: 获取结果
    print("步骤5: 获取转写结果...")
    get_result_url = 'https://raasr.xfyun.cn/api/getResult'
    
    ts = str(int(time.time()))
    m2 = hashlib.md5()
    m2.update((appid + ts).encode('utf-8'))
    md5 = m2.hexdigest()
    md5 = bytes(md5, encoding='utf-8')
    signa = hmac.new(apisecret.encode('utf-8'), md5, hashlib.sha1).digest()
    signa = base64.b64encode(signa)
    signa = str(signa, 'utf-8')
    
    result_data = {
        'app_id': appid,
        'signa': signa,
        'ts': ts,
        'task_id': task_id
    }
    
    result_response = requests.post(get_result_url, data=result_data, timeout=30)
    result_json = result_response.json()
    
    print(f"结果响应: {result_json}")
    
    if result_json.get('ok') != 0:
        raise Exception(f"获取结果失败: {result_json.get('failed')}")
    
    # 解析结果
    data_str = result_json.get('data', '')
    if data_str:
        data_json = json.loads(data_str)
        sentences = data_json.get('utterances', [])
        text = ''.join([s.get('transcript', '') for s in sentences])
        print(f"识别成功,文本长度: {len(text)}")
        return text
    
    raise Exception("识别结果为空")



