from fastapi import APIRouter, Depends, HTTPException
from app.models.comment_generation import (
    CommentGenerationRequest,
    CommentGenerationResponse,
)
from app.services.comment_generation_service import (
    CommentGenerationService,
    create_comment_generation_service,
)

router = APIRouter()


@router.post("/generate", response_model=CommentGenerationResponse)
async def generate_comments(
    request: CommentGenerationRequest,
    service: CommentGenerationService = Depends(create_comment_generation_service),
) -> CommentGenerationResponse:
    """
    게시글 분석 결과를 기반으로 댓글 생성

    Args:
        request: 댓글 생성 요청 (게시글 내용 + 분석 결과)
        service: 댓글 생성 서비스

    Returns:
        CommentGenerationResponse: 생성된 댓글 목록
    """
    try:
        response = await service.generate_comments(request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"댓글 생성 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """댓글 생성 서비스 상태 확인"""
    return {"status": "healthy", "service": "comment_generation"}
