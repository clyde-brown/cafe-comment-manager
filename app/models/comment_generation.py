from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.post_analysis import PostAnalysisResult


class CommentGenerationRequest(BaseModel):
    """댓글 생성 요청 모델"""

    post_content: str = Field(..., description="게시글 내용")
    post_analysis: PostAnalysisResult = Field(..., description="게시글 분석 결과")


class GeneratedComment(BaseModel):
    """생성된 댓글 모델"""

    type: str = Field(
        ..., description="댓글 유형 (공감형, 질문형, 조언형, 친근형, 경험공유형)"
    )
    content: str = Field(..., description="댓글 내용")


class CommentGenerationResult(BaseModel):
    """댓글 생성 결과 모델"""

    comments: List[GeneratedComment] = Field(
        default_factory=list, description="생성된 댓글 목록"
    )


class CommentGenerationResponse(BaseModel):
    """댓글 생성 응답 모델"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    comments: Optional[CommentGenerationResult] = Field(None, description="생성된 댓글")
    processing_time: float = Field(..., description="처리 시간 (초)")

