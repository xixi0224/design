import json
import os
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
    使用百度云短语音识别 API 进行语音转文本
    通过分段处理实现长音频识别
    """
    from aip import AipSpeech
    import subprocess

    # 百度云应用信息
    API_KEY = 'HYPim6GzLxhPjBXIv11DRCt8'
    SECRET_KEY = '6Tiai01NZgTpU5cl4fvJMQBT92F2zuGY'
    APP_ID = '122981257'

    # 初始化百度云语音客户端
    client = AipSpeech(APP_ID, API_KEY, SECRET_KEY)

    # 使用 FFmpeg 将音频转换为 pcm 格式（16kHz, 单声道）
    def convert_to_pcm(input_path: str) -> str:
        """使用 FFmpeg 将音频转换为 16kHz, 单声道的 PCM 文件"""
        # 检查 FFmpeg 是否存在
        ffmpeg_path = r"d:\tingting\xixi\计算机设计大赛\ZhiNote2.0\ffmpeg-2026-04-19-git-de18feb0f0-essentials_build\bin\ffmpeg.exe"
        if not os.path.exists(ffmpeg_path):
            raise RuntimeError(f"FFmpeg 未找到: {ffmpeg_path}")
        
        output_path = input_path.rsplit('.', 1)[0] + '_converted.pcm'

        cmd = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel", "error",
            "-y",
            "-i", input_path,
            "-f", "s16le",
            "-ar", "16000",
            "-ac", "1",
            output_path
        ]

        print(f"开始转换音频为 16kHz PCM 格式...")
        print(f"FFmpeg 路径: {ffmpeg_path}")
        print(f"输入文件: {input_path}")
        print(f"输出文件: {output_path}")
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120, shell=True)
            if result.returncode != 0:
                error_msg = result.stderr.decode('utf-8', errors='replace')
                raise RuntimeError(f"FFmpeg 转换失败: {error_msg}")

            file_size = os.path.getsize(output_path)
            print(f"音频转换完成，输出文件: {output_path}，大小: {file_size} bytes")
            return output_path
        except subprocess.TimeoutExpired:
            raise RuntimeError("FFmpeg 转换超时")
        except Exception as e:
            raise RuntimeError(f"FFmpeg 转换异常：{e}")

    # 获取音频时长
    def get_audio_duration(pcm_path: str) -> float:
        """获取PCM音频时长（秒）"""
        ffmpeg_path = r"d:\tingting\xixi\计算机设计大赛\ZhiNote2.0\ffmpeg-2026-04-19-git-de18feb0f0-essentials_build\bin\ffmpeg.exe"

        cmd = [
            ffmpeg_path,
            "-hide_banner",
            "-loglevel", "error",
            "-i", audio_path,
            "-f", "s16le",
            "-ar", "16000",
            "-ac", "1",
            "-t", "0.01",
            "NUL"
        ]

        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        except:
            pass

        file_size = os.path.getsize(pcm_path)
        # PCM: 16bit = 2 bytes, 16000Hz, 单声道
        # 每秒字节数 = 16000 * 2 = 32000
        bytes_per_second = 16000 * 2
        duration = file_size / bytes_per_second
        return duration

    # 分段识别长音频
    def recognize_segment(client, audio_data: bytes, offset: int = 0):
        """识别单个音频片段"""
        result = client.asr(audio_data, 'pcm', 16000, {
            'dev_pid': 1537,  # 中文普通话
        })
        return result

    try:
        # 1. 转换音频为PCM格式
        pcm_path = convert_to_pcm(audio_path)

        # 2. 读取PCM文件
        with open(pcm_path, 'rb') as f:
            pcm_data = f.read()

        total_size = len(pcm_data)
        print(f"PCM音频数据大小: {total_size} bytes")

        # 3. 获取音频时长
        duration = total_size / (16000 * 2)
        print(f"音频时长: {duration:.2f} 秒")

        # 4. 根据时长决定处理方式
        MAX_SEGMENT_DURATION = 55  # 每次最多55秒，留点余量
        MAX_SEGMENT_SIZE = int(MAX_SEGMENT_DURATION * 16000 * 2)  # 字节数

        if duration > MAX_SEGMENT_DURATION:
            # 长音频：分段处理
            num_segments = int((total_size / MAX_SEGMENT_SIZE) + 0.5)
            if num_segments < 1:
                num_segments = 1

            print(f"音频时长 {duration:.2f} 秒，超过 {MAX_SEGMENT_DURATION} 秒限制，需要分为 {num_segments} 段处理")

            full_text = []
            for i in range(num_segments):
                start = i * MAX_SEGMENT_SIZE
                end = start + MAX_SEGMENT_SIZE if i < num_segments - 1 else total_size
                segment_data = pcm_data[start:end]

                print(f"正在识别第 {i+1}/{num_segments} 段...")

                result = recognize_segment(client, segment_data)

                print(f"第 {i+1} 段识别响应: {result}")

                if 'err_no' in result and result.get('err_no') != 0:
                    print(f"第 {i+1} 段识别失败: {result.get('err_msg', '识别失败')}，继续下一段")
                    continue

                if 'result' in result and len(result['result']) > 0:
                    segment_text = ''.join(result['result'])
                    full_text.append(segment_text)
                    print(f"第 {i+1} 段识别成功，长度: {len(segment_text)}")

            # 清理临时文件
            try:
                if os.path.exists(pcm_path):
                    os.remove(pcm_path)
            except:
                pass

            if full_text:
                final_text = ''.join(full_text)
                print(f"分段识别完成，最终文本长度: {len(final_text)}")
                return final_text
            else:
                raise Exception("所有分段识别均失败")
        else:
            # 短音频：直接识别
            print("短音频，直接识别...")

            result = recognize_segment(client, pcm_data)
            print(f"识别响应: {result}")

            # 清理临时文件
            try:
                if os.path.exists(pcm_path):
                    os.remove(pcm_path)
            except:
                pass

            if 'err_no' in result and result.get('err_no') != 0:
                raise Exception(f"ASR 识别失败: {result.get('err_msg', '识别失败')}")

            if 'result' in result and len(result['result']) > 0:
                text = ''.join(result['result'])
                print(f"识别成功，文本长度: {len(text)}")
                return text

            raise Exception("ASR 识别返回结果格式异常")

    except Exception as e:
        # 清理临时文件
        try:
            if 'pcm_path' in locals() and os.path.exists(pcm_path):
                os.remove(pcm_path)
        except:
            pass
        raise Exception(f"语音转文本失败：{e}")
