#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 리액션 분석 관련 Pydantic 모델들 (간소화 버전)
"""

from typing import List, Optional
from pydantic import BaseModel
from enum import Enum


class SentimentType(str, Enum):
    """감정 분석 타입"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ReactionType(str, Enum):
    """리액션 분석 타입"""

    SENTIMENT = "sentiment"
    KEYWORDS = "keywords"
    COMMENTS = "comments"
    SUMMARY = "summary"
    QUESTIONS = "questions"


class ArticleAnalysisRequest(BaseModel):
    """카페 게시글 댓글 생성 요청 모델"""

    article_text: str
    comment_styles: Optional[List[str]] = [
        "공감형",
        "질문형",
        "조언형",
        "친근형",
        "경험공유형",
    ]
    max_comments: Optional[int] = 5
    tone_style: Optional[str] = "친근한톤"


class CafeComment(BaseModel):
    """카페 댓글 모델"""

    style: str  # 공감형, 질문형, 조언형, 친근형, 경험공유형
    icon: str
    content: str
    tone: str = "친근한톤"


class CafeCommentResponse(BaseModel):
    """카페 댓글 생성 응답"""

    success: bool
    post_analysis: str
    comments: List[CafeComment]
    processing_time: float
    message: str = "카페 댓글이 생성되었습니다."
