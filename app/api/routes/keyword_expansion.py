#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 확장 API 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.keyword_expansion import (
    KeywordExpansionRequest,
    KeywordExpansionResponse,
    PromptType,
)
from app.services.keyword_expansion_service import (
    KeywordExpansionService,
    create_keyword_expansion_service,
)
from app.services.prompt_loader_service import get_prompt_loader
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# KeywordExpansionService 인스턴스를 의존성 주입으로 제공
def get_keyword_service() -> KeywordExpansionService:
    """
    KeywordExpansionService 인스턴스 생성
    LLM 설정에서 API 키와 모델을 자동으로 가져옵니다.
    """
    # API 키는 서비스 내부에서 LLM 설정으로부터 자동으로 가져옴
    return create_keyword_expansion_service(gemini_api_key=None)


@router.post(
    "/keywords/expand",
    response_model=KeywordExpansionResponse,
    summary="키워드 자동 확장",
)
async def expand_keywords(
    request: KeywordExpansionRequest,
    keyword_service: KeywordExpansionService = Depends(get_keyword_service),
):
    """
    마케팅 키워드를 AI를 사용하여 자동으로 확장합니다.

    - **target_keyword**: 확장할 타겟 키워드
    - **keyword_count**: 생성할 총 키워드 개수 (기본: 20개, 범위: 5-50개)

    **반환값:**
    - 5가지 카테고리별로 분류된 확장 키워드
      - 직설적 키워드
      - 문제/니즈 기반 키워드
      - 솔루션/혜택 키워드
      - 롱테일 키워드
      - 경쟁/대체 키워드
    - 총 생성된 키워드 개수
    - 처리 시간 및 성공 여부
    """
    logger.info(
        f"API 요청 수신: /keywords/expand (키워드: '{request.target_keyword}', 개수: {request.keyword_count})"
    )

    response = await keyword_service.expand_keywords(request)

    if not response.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=response.message,
        )

    logger.info(
        f"API 응답 전송: /keywords/expand (성공: {response.success}, 총 키워드: {response.total_count}개)"
    )
    return response


@router.get("/prompts")
async def get_available_prompts():
    """
    사용 가능한 프롬프트 목록 반환

    Returns:
        dict: 프롬프트 타입별 정보
    """
    try:
        prompt_loader = get_prompt_loader()

        # 키워드 확장 관련 프롬프트만 필터링
        prompts_info = {}

        for prompt_type in PromptType:
            prompt_info = prompt_loader.get_prompt_info(
                "keyword_expansion", prompt_type.value
            )
            if prompt_info:
                prompts_info[prompt_type.value] = {
                    "name": prompt_info.get("name", prompt_type.value),
                    "description": prompt_info.get("description", ""),
                    "version": prompt_info.get("version", "1.0"),
                }

        return {
            "success": True,
            "prompts": prompts_info,
            "total_count": len(prompts_info),
        }

    except Exception as e:
        logger.error(f"프롬프트 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="프롬프트 목록을 불러올 수 없습니다.",
        )
