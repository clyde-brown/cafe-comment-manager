#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM 설정 관리 서비스
"""

import os
import time
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from app.models.llm_settings import (
    LLMSettingsRequest,
    LLMTestConnectionRequest,
    LLMSettingsResponse,
    LLMTestConnectionResponse,
)

logger = logging.getLogger(__name__)


class LLMSettingsService:
    """
    LLM 설정 관리 서비스 클래스
    API 키와 모델 설정을 안전하게 저장하고 관리합니다.
    """

    def __init__(self, settings_file: str = "llm_settings.json"):
        """
        Args:
            settings_file: 설정 파일 경로
        """
        self.settings_file = Path(settings_file)
        self.current_settings = self._load_settings()

    def _load_settings(self) -> Dict[str, Any]:
        """설정 파일에서 설정 불러오기"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"설정 파일 로드 실패: {e}")

        return {}

    def _save_settings(self) -> bool:
        """설정을 파일에 저장"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.current_settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"설정 파일 저장 실패: {e}")
            return False

    def _test_gemini_connection(self, api_key: str, model: str) -> Dict[str, Any]:
        """Gemini API 연결 테스트"""
        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)

            # 모델명 매핑
            model_mapping = {
                "gemini-2.5-flash": "gemini-2.5-flash",  # 2.5 Flash는 아직 2.0 Flash 사용
                "gemini-2.0-flash-exp": "gemini-2.0-flash-exp",
                "gemini-1.5-pro": "gemini-1.5-pro",
                "gemini-1.5-flash": "gemini-1.5-flash",
            }

            actual_model = model_mapping.get(model, model)
            gemini_model = genai.GenerativeModel(actual_model)

            start_time = time.time()
            response = gemini_model.generate_content(
                "안녕하세요! 간단한 연결 테스트입니다."
            )
            response_time = time.time() - start_time

            return {
                "success": True,
                "message": "연결 성공",
                "response_time": response_time,
                "test_response": (
                    response.text[:100] + "..."
                    if len(response.text) > 100
                    else response.text
                ),
            }

        except Exception as e:
            logger.error(f"Gemini API 테스트 실패: {e}")
            return {
                "success": False,
                "message": f"Gemini API 연결 실패: {str(e)}",
                "response_time": None,
                "test_response": None,
            }

    def _test_openai_connection(self, api_key: str, model: str) -> Dict[str, Any]:
        """OpenAI API 연결 테스트 (구현 예정)"""
        return {
            "success": False,
            "message": "OpenAI API 연결 테스트는 아직 구현되지 않았습니다.",
            "response_time": None,
            "test_response": None,
        }

    def _test_claude_connection(self, api_key: str, model: str) -> Dict[str, Any]:
        """Claude API 연결 테스트 (구현 예정)"""
        return {
            "success": False,
            "message": "Claude API 연결 테스트는 아직 구현되지 않았습니다.",
            "response_time": None,
            "test_response": None,
        }

    async def test_connection(
        self, request: LLMTestConnectionRequest
    ) -> LLMTestConnectionResponse:
        """
        LLM API 연결 테스트

        Args:
            request: 연결 테스트 요청

        Returns:
            LLMTestConnectionResponse: 연결 테스트 결과
        """
        logger.info(f"LLM 연결 테스트 시작: {request.model}")

        try:
            # 모델별 연결 테스트
            if request.model.startswith("gemini"):
                result = self._test_gemini_connection(request.api_key, request.model)
            elif request.model.startswith("gpt"):
                result = self._test_openai_connection(request.api_key, request.model)
            elif request.model.startswith("claude"):
                result = self._test_claude_connection(request.api_key, request.model)
            else:
                result = {
                    "success": False,
                    "message": f"지원하지 않는 모델입니다: {request.model}",
                    "response_time": None,
                    "test_response": None,
                }

            logger.info(f"연결 테스트 완료: {request.model}, 성공: {result['success']}")

            return LLMTestConnectionResponse(
                success=result["success"],
                message=result["message"],
                model=request.model,
                response_time=result["response_time"],
                test_response=result["test_response"],
            )

        except Exception as e:
            logger.error(f"연결 테스트 중 오류 발생: {e}", exc_info=True)

            return LLMTestConnectionResponse(
                success=False,
                message=f"연결 테스트 중 오류 발생: {str(e)}",
                model=request.model,
                response_time=None,
                test_response=None,
            )

    async def save_settings(self, request: LLMSettingsRequest) -> LLMSettingsResponse:
        """
        LLM 설정 저장

        Args:
            request: 설정 저장 요청

        Returns:
            LLMSettingsResponse: 저장 결과
        """
        logger.info(f"LLM 설정 저장: {request.model}")

        try:
            # 설정 업데이트
            self.current_settings.update(
                {
                    "model": request.model,
                    "api_key": request.api_key,  # 실제 환경에서는 암호화 필요
                    "updated_at": time.time(),
                }
            )

            # 파일에 저장
            if self._save_settings():
                logger.info("LLM 설정 저장 완료")
                return LLMSettingsResponse(
                    success=True,
                    message="설정이 성공적으로 저장되었습니다.",
                    has_api_key=True,
                    current_model=request.model,
                )
            else:
                return LLMSettingsResponse(
                    success=False,
                    message="설정 저장에 실패했습니다.",
                    has_api_key=False,
                    current_model=None,
                )

        except Exception as e:
            logger.error(f"설정 저장 중 오류 발생: {e}", exc_info=True)

            return LLMSettingsResponse(
                success=False,
                message=f"설정 저장 중 오류 발생: {str(e)}",
                has_api_key=False,
                current_model=None,
            )

    async def get_settings(self) -> LLMSettingsResponse:
        """
        현재 LLM 설정 조회

        Returns:
            LLMSettingsResponse: 현재 설정 정보
        """
        try:
            has_api_key = bool(self.current_settings.get("api_key"))
            current_model = self.current_settings.get("model")

            return LLMSettingsResponse(
                success=True,
                message="설정 조회 성공",
                has_api_key=has_api_key,
                current_model=current_model,
            )

        except Exception as e:
            logger.error(f"설정 조회 중 오류 발생: {e}", exc_info=True)

            return LLMSettingsResponse(
                success=False,
                message=f"설정 조회 중 오류 발생: {str(e)}",
                has_api_key=False,
                current_model=None,
            )

    def get_current_api_key(self) -> Optional[str]:
        """현재 설정된 API 키 반환"""
        return self.current_settings.get("api_key")

    def get_current_model(self) -> Optional[str]:
        """현재 설정된 모델 반환"""
        return self.current_settings.get("model", "gemini-2.5-flash")


def create_llm_settings_service() -> LLMSettingsService:
    """LLM 설정 서비스 인스턴스 생성"""
    return LLMSettingsService()
