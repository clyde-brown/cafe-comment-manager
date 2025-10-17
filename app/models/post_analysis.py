#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
게시글 분석 및 댓글 생성을 위한 데이터 모델
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PostAnalysisRequest(BaseModel):
    """게시글 분석 요청 모델"""

    post_title: str = Field(..., description="게시글 제목")
    post_content: str = Field(..., description="게시글 본문")


class PostAnalysisResult(BaseModel):
    """게시글 분석 결과 모델"""

    topic: str = Field(..., description="게시글의 주요 주제와 목적", alias="주제")
    emotion: str = Field(
        ..., description="작성자의 감정 상태와 심리 동기", alias="감정"
    )
    summary: str = Field(
        ..., description="게시글의 가장 중요한 내용 요약", alias="핵심내용"
    )
    comment_points: str = Field(
        ..., description="댓글로 반응하기 좋은 부분들", alias="댓글포인트"
    )
    comment_type: str = Field(
        ..., description="필요한 댓글 유형 (일반/공감/상품추천)", alias="필요댓글유형"
    )
    product_type: Optional[str] = Field(
        None, description="상품 추천 유형", alias="상품추천유형"
    )


class PostAnalysisResponse(BaseModel):
    """게시글 분석 응답 모델"""

    success: bool = Field(default=True, description="분석 성공 여부")
    analysis: Optional[PostAnalysisResult] = Field(None, description="분석 결과")
    processing_time: float = Field(..., description="처리 시간 (초)")
    message: str = Field(..., description="응답 메시지")


class CommentGenerationRequest(BaseModel):
    """댓글 생성 요청 모델"""

    post_title: str = Field(..., description="게시글 제목")
    post_content: str = Field(..., description="게시글 본문")
    analysis: PostAnalysisResult = Field(..., description="게시글 분석 결과")


class GeneratedComment(BaseModel):
    """생성된 댓글 모델"""

    style: str = Field(
        ..., description="댓글 스타일 (공감형, 질문형, 조언형, 친근형, 경험공유형)"
    )
    icon: str = Field(..., description="댓글 스타일 아이콘")
    content: str = Field(..., description="댓글 내용")


class CommentGenerationResponse(BaseModel):
    """댓글 생성 응답 모델"""

    success: bool = Field(default=True, description="생성 성공 여부")
    comments: List[GeneratedComment] = Field(
        default_factory=list, description="생성된 댓글 목록"
    )
    processing_time: float = Field(..., description="처리 시간 (초)")
    message: str = Field(..., description="응답 메시지")


class PostAnalysisAndCommentRequest(BaseModel):
    """게시글 분석 및 댓글 생성 통합 요청 모델"""

    post_title: str = Field(..., description="게시글 제목")
    post_content: str = Field(..., description="게시글 본문")


class PostAnalysisAndCommentResponse(BaseModel):
    """게시글 분석 및 댓글 생성 통합 응답 모델"""

    success: bool = Field(default=True, description="처리 성공 여부")
    analysis: Optional[PostAnalysisResult] = Field(None, description="분석 결과")
    comments: List[GeneratedComment] = Field(
        default_factory=list, description="생성된 댓글 목록"
    )
    processing_time: float = Field(..., description="총 처리 시간 (초)")
    message: str = Field(..., description="응답 메시지")
