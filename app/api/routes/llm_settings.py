#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 설정 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.llm_settings import (
    LLMSettingsRequest,
    LLMTestConnectionRequest,
    LLMSettingsResponse,
    LLMTestConnectionResponse,
)
from app.services.llm_settings_service import (
    LLMSettingsService,
    create_llm_settings_service,
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# LLMSettingsService 인스턴스를 의존성 주입으로 제공
def get_llm_settings_service() -> LLMSettingsService:
    return create_llm_settings_service()


@router.post(
    "/llm/test-connection",
    response_model=LLMTestConnectionResponse,
    summary="LLM API 연결 테스트",
)
async def test_llm_connection(
    request: LLMTestConnectionRequest,
    llm_service: LLMSettingsService = Depends(get_llm_settings_service),
):
    """
    LLM API 연결을 테스트합니다.

    - **model**: 테스트할 LLM 모델명
    - **api_key**: API 키

    **지원하는 모델:**
    - Gemini: gemini-2.0-flash-exp, gemini-1.5-pro, gemini-1.5-flash
    - OpenAI: gpt-4, gpt-3.5-turbo (구현 예정)
    - Claude: claude-3-sonnet (구현 예정)

    **반환값:**
    - 연결 성공 여부
    - 응답 시간
    - 테스트 응답 내용
    """
    logger.info(f"API 요청 수신: /llm/test-connection (모델: {request.model})")

    response = await llm_service.test_connection(request)

    logger.info(
        f"API 응답 전송: /llm/test-connection (성공: {response.success}, 모델: {response.model})"
    )
    return response


@router.post(
    "/llm/settings",
    response_model=LLMSettingsResponse,
    summary="LLM 설정 저장",
)
async def save_llm_settings(
    request: LLMSettingsRequest,
    llm_service: LLMSettingsService = Depends(get_llm_settings_service),
):
    """
    LLM 모델과 API 키 설정을 저장합니다.

    - **model**: 사용할 LLM 모델명
    - **api_key**: API 키

    **주의사항:**
    - API 키는 서버에 저장됩니다 (실제 환경에서는 암호화 필요)
    - 기존 설정을 덮어씁니다

    **반환값:**
    - 저장 성공 여부
    - 현재 설정된 모델
    - API 키 설정 여부
    """
    logger.info(f"API 요청 수신: /llm/settings (모델: {request.model})")

    response = await llm_service.save_settings(request)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message,
        )

    logger.info(f"API 응답 전송: /llm/settings (성공: {response.success})")
    return response


@router.get(
    "/llm/settings",
    response_model=LLMSettingsResponse,
    summary="LLM 설정 조회",
)
async def get_llm_settings(
    llm_service: LLMSettingsService = Depends(get_llm_settings_service),
):
    """
    현재 LLM 설정을 조회합니다.

    **반환값:**
    - 현재 설정된 모델
    - API 키 설정 여부 (실제 키 값은 반환하지 않음)
    - 조회 성공 여부
    """
    logger.info("API 요청 수신: GET /llm/settings")

    response = await llm_service.get_settings()

    logger.info(f"API 응답 전송: GET /llm/settings (성공: {response.success})")
    return response
