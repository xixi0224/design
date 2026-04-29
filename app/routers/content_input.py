from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from app.schemas.content_input import AudioRecordResponse, TextInputCreate, TextInputResponse
from app.services.content_input_service import handle_audio_upload, create_text_input

router = APIRouter(tags=["content_input"])

@router.post("/upload/audio", response_model=AudioRecordResponse)
async def upload_audio(
    file: UploadFile = File(...),
    course_id: int = 1
):
    try:
        return handle_audio_upload(file, course_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"音频上传失败: {str(e)}")

@router.post("/text-input", response_model=TextInputResponse)
async def create_text_input_endpoint(input_data: TextInputCreate):
    try:
        return create_text_input(input_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文本输入失败: {str(e)}")

@router.post("/segment-text")
async def segment_text(data: dict = Body(...)):
    try:
        text = data.get("text", "")
        # 简单的文本分段逻辑
        # 按段落分割
        paragraphs = text.split('\n')
        # 过滤空段落
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        # 重新组合成带换行的文本
        segmented_text = '\n\n'.join(paragraphs)
        
        return {"code": 0, "data": segmented_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文本分段失败: {str(e)}")
