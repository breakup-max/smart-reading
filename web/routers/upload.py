import os

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from web.schemas import UploadResponse
from run import PDFQA

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="只支持 PDF 文件")

    pdf_bytes = await file.read()
    if len(pdf_bytes) == 0:
        raise HTTPException(status_code=400, detail="上传的文件为空")

    api_key = request.app.state.api_key or os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="未配置 DASHSCOPE_API_KEY 环境变量")

    try:
        qa = PDFQA(pdf_bytes, api_key)
        qa._build_index()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"索引构建失败: {str(e)}")

    request.app.state.pdfqa_sessions[qa.file_hash] = qa

    return UploadResponse(
        file_hash=qa.file_hash,
        message=f"索引构建完成，文件名: {file.filename}"
    )