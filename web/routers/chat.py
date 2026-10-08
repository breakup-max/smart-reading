import os

from fastapi import APIRouter, Request, HTTPException

from web.schemas import ChatRequest, ChatResponse, EvidenceItem, ErrorResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse, responses={404: {"model": ErrorResponse}})
async def chat(request: Request, body: ChatRequest):
    qa = request.app.state.pdfqa_sessions.get(body.file_hash)
    if qa is None:
        raise HTTPException(status_code=404, detail="未找到对应的文件会话，请先上传 PDF")

    api_key = request.app.state.api_key or os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="未配置 DASHSCOPE_API_KEY 环境变量")

    try:
        result = qa.ask(body.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")

    evidence = [
        EvidenceItem(
            content=e.content,
            source=e.source,
            page=e.page,
            score=e.score,
            vector_score=e.vector_score,
            hybrid_score=e.hybrid_score,
            llm_score=e.llm_score,
        )
        for e in result.get("evidence", [])
    ]

    return ChatResponse(
        answer=result["answer"],
        search_query=result["search_query"],
        rewritten=result["rewritten"],
        evidence=evidence,
    )