#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카페 댓글 자동 생성 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.ai_reaction import ArticleAnalysisRequest, CafeCommentResponse
from app.services.cafe_comment_service import (
    CafeCommentService,
    create_cafe_comment_service,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# CafeCommentService 인스턴스를 의존성 주입으로 제공
def get_cafe_comment_service() -> CafeCommentService:
    return create_cafe_comment_service()


@router.post(
    "/cafe/comments", response_model=CafeCommentResponse, summary="카페 댓글 자동 생성"
)
async def generate_cafe_comments(
    request: ArticleAnalysisRequest,
    comment_service: CafeCommentService = Depends(get_cafe_comment_service),
):
    """
    주어진 카페 게시글 내용을 AI를 사용하여 분석하고 자연스러운 댓글을 자동으로 생성합니다.

    - **article_text**: 댓글을 생성할 카페 게시글 내용
    - **comment_styles**: 생성할 댓글 스타일 (기본: 공감형, 질문형, 조언형, 친근형, 경험공유형)
    - **max_comments**: 최대 댓글 개수 (기본: 5개)
    - **tone_style**: 댓글 톤 (기본: 친근한톤)

    **반환값:**
    - 게시글 분석 결과
    - 5가지 스타일의 자연스러운 댓글
    - 처리 시간 및 성공 여부
    """
    logger.info(
        f"API 요청 수신: /cafe/comments (게시글 길이: {len(request.article_text)} 글자)"
    )

    response = await comment_service.generate_cafe_comments(request)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.message
        )

    logger.info(
        f"API 응답 전송: /cafe/comments (성공: {response.success}, 댓글 수: {len(response.comments)})"
    )
    return response
