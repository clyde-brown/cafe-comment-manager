#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
게시글 분석 및 댓글 생성 API 라우트
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.models.post_analysis import (
    PostAnalysisRequest,
    PostAnalysisResponse,
    CommentGenerationRequest,
    CommentGenerationResponse,
    PostAnalysisAndCommentRequest,
    PostAnalysisAndCommentResponse,
)
from app.services.post_analysis_service import (
    create_post_analysis_service,
    PostAnalysisService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/post-analysis", tags=["게시글 분석"])


def get_post_analysis_service() -> PostAnalysisService:
    """PostAnalysisService 의존성 주입"""
    return create_post_analysis_service()


@router.post("/analyze", response_model=PostAnalysisResponse)
async def analyze_post(
    request: PostAnalysisRequest,
    service: PostAnalysisService = Depends(get_post_analysis_service),
):
    """
    게시글을 분석하여 심리학적 분석 결과를 반환합니다.

    - **post_title**: 게시글 제목
    - **post_content**: 게시글 본문

    분석 결과로 주제, 감정, 핵심내용, 댓글포인트, 필요댓글유형, 상품추천유형을 반환합니다.
    """
    try:
        logger.info(f"게시글 분석 API 호출: 제목='{request.post_title}'")

        if not request.post_title.strip():
            raise HTTPException(status_code=400, detail="게시글 제목을 입력해주세요.")

        if not request.post_content.strip():
            raise HTTPException(status_code=400, detail="게시글 본문을 입력해주세요.")

        if len(request.post_content) > 5000:
            raise HTTPException(
                status_code=400, detail="게시글 본문은 5000자를 초과할 수 없습니다."
            )

        response = await service.analyze_post(request)

        if not response.success:
            logger.error(f"게시글 분석 실패: {response.message}")
            raise HTTPException(status_code=500, detail=response.message)

        logger.info(f"게시글 분석 성공: 처리시간={response.processing_time:.2f}초")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"게시글 분석 API 오류: {str(e)}")
        raise HTTPException(
            status_code=500, detail="게시글 분석 중 오류가 발생했습니다."
        )


@router.post("/generate-comments", response_model=CommentGenerationResponse)
async def generate_comments(
    request: CommentGenerationRequest,
    service: PostAnalysisService = Depends(get_post_analysis_service),
):
    """
    분석 결과를 바탕으로 5가지 스타일의 댓글을 생성합니다.

    - **post_title**: 게시글 제목
    - **post_content**: 게시글 본문
    - **analysis**: 게시글 분석 결과

    공감형, 질문형, 조언형, 친근형, 경험공유형의 5가지 댓글을 생성합니다.
    """
    try:
        logger.info(f"댓글 생성 API 호출: 제목='{request.post_title}'")

        if not request.post_title.strip():
            raise HTTPException(status_code=400, detail="게시글 제목을 입력해주세요.")

        if not request.post_content.strip():
            raise HTTPException(status_code=400, detail="게시글 본문을 입력해주세요.")

        response = await service.generate_comments(request)

        if not response.success:
            logger.error(f"댓글 생성 실패: {response.message}")
            raise HTTPException(status_code=500, detail=response.message)

        logger.info(
            f"댓글 생성 성공: {len(response.comments)}개 댓글, 처리시간={response.processing_time:.2f}초"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"댓글 생성 API 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="댓글 생성 중 오류가 발생했습니다.")


@router.post("/analyze-and-generate", response_model=PostAnalysisAndCommentResponse)
async def analyze_and_generate_comments(
    request: PostAnalysisAndCommentRequest,
    service: PostAnalysisService = Depends(get_post_analysis_service),
):
    """
    게시글 분석과 댓글 생성을 한 번에 수행합니다.

    - **post_title**: 게시글 제목
    - **post_content**: 게시글 본문

    게시글을 분석한 후, 분석 결과를 바탕으로 5가지 스타일의 댓글을 생성합니다.
    """
    try:
        logger.info(f"통합 분석 및 댓글 생성 API 호출: 제목='{request.post_title}'")

        if not request.post_title.strip():
            raise HTTPException(status_code=400, detail="게시글 제목을 입력해주세요.")

        if not request.post_content.strip():
            raise HTTPException(status_code=400, detail="게시글 본문을 입력해주세요.")

        if len(request.post_content) > 5000:
            raise HTTPException(
                status_code=400, detail="게시글 본문은 5000자를 초과할 수 없습니다."
            )

        response = await service.analyze_and_generate_comments(request)

        if not response.success:
            logger.error(f"통합 처리 실패: {response.message}")
            raise HTTPException(status_code=500, detail=response.message)

        logger.info(
            f"통합 처리 성공: {len(response.comments)}개 댓글, 처리시간={response.processing_time:.2f}초"
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"통합 처리 API 오류: {str(e)}")
        raise HTTPException(
            status_code=500, detail="게시글 분석 및 댓글 생성 중 오류가 발생했습니다."
        )


@router.get("/health")
async def health_check():
    """
    게시글 분석 서비스 상태를 확인합니다.
    """
    try:
        service = get_post_analysis_service()
        return JSONResponse(
            status_code=200,
            content={
                "status": "healthy",
                "service": "post_analysis",
                "message": "게시글 분석 서비스가 정상적으로 작동 중입니다.",
            },
        )
    except Exception as e:
        logger.error(f"헬스체크 오류: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "service": "post_analysis",
                "message": f"서비스 오류: {str(e)}",
            },
        )
