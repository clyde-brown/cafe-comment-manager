#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 확장 관련 Pydantic 모델들
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class PromptType(str, Enum):
    """프롬프트 타입 열거형"""

    BASIC = "keyword_expansion"
    CREATIVE = "keyword_expansion_creative"
    SEO = "keyword_expansion_seo"
    COMPETITOR = "keyword_expansion_competitor"
    SIMPLE = "keyword_expansion_simple"


class KeywordExpansionRequest(BaseModel):
    """키워드 확장 요청 모델"""

    target_keyword: str = Field(..., min_length=1, description="확장할 타겟 키워드")
    keyword_count: Optional[int] = Field(
        20, ge=5, le=50, description="생성할 총 키워드 개수 (5-50개)"
    )
    prompt_type: Optional[PromptType] = Field(
        PromptType.BASIC, description="사용할 프롬프트 타입"
    )


class KeywordsByCategory(BaseModel):
    """카테고리별 키워드 모델"""

    직설적: List[str] = Field(default_factory=list, description="직설적 키워드")
    문제_니즈: List[str] = Field(
        default_factory=list, description="문제/니즈 기반 키워드"
    )
    솔루션_혜택: List[str] = Field(
        default_factory=list, description="솔루션/혜택 키워드"
    )
    롱테일: List[str] = Field(default_factory=list, description="롱테일 키워드")
    경쟁_대체: List[str] = Field(default_factory=list, description="경쟁/대체 키워드")


class KeywordExpansionResponse(BaseModel):
    """키워드 확장 응답 모델"""

    success: bool = Field(..., description="성공 여부")
    target_keyword: str = Field(..., description="입력된 타겟 키워드")
    keywords: Optional[KeywordsByCategory] = Field(
        None, description="카테고리별 확장된 키워드"
    )
    total_count: int = Field(0, description="총 생성된 키워드 개수")
    processing_time: float = Field(0.0, description="처리 시간 (초)")
    message: str = Field("", description="응답 메시지")
    raw_response: Optional[str] = Field(None, description="AI의 원본 응답")
