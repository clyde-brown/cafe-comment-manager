#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 설정 관련 Pydantic 모델들
"""

from typing import Optional
from pydantic import BaseModel, Field


class LLMSettingsRequest(BaseModel):
    """LLM 설정 요청 모델"""

    model: str = Field(..., description="사용할 LLM 모델명")
    api_key: str = Field(..., min_length=1, description="API 키")


class LLMTestConnectionRequest(BaseModel):
    """LLM 연결 테스트 요청 모델"""

    model: str = Field(..., description="테스트할 LLM 모델명")
    api_key: str = Field(..., min_length=1, description="API 키")


class LLMSettingsResponse(BaseModel):
    """LLM 설정 응답 모델"""

    success: bool = Field(..., description="성공 여부")
    message: str = Field("", description="응답 메시지")
    has_api_key: Optional[bool] = Field(None, description="API 키 설정 여부")
    current_model: Optional[str] = Field(None, description="현재 설정된 모델")


class LLMTestConnectionResponse(BaseModel):
    """LLM 연결 테스트 응답 모델"""

    success: bool = Field(..., description="연결 성공 여부")
    message: str = Field("", description="응답 메시지")
    model: str = Field("", description="테스트한 모델명")
    response_time: Optional[float] = Field(None, description="응답 시간 (초)")
    test_response: Optional[str] = Field(None, description="테스트 응답 내용")
