#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
프롬프트 템플릿 로더 서비스
외부 YAML 파일에서 프롬프트를 로드하고 관리합니다.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from string import Template

logger = logging.getLogger(__name__)


class PromptLoaderService:
    """
    프롬프트 템플릿 로더 서비스 클래스
    YAML 파일에서 프롬프트를 로드하고 템플릿 변수를 치환합니다.
    """

    def __init__(self, prompts_dir: str = "app/prompts"):
        """
        Args:
            prompts_dir: 프롬프트 템플릿 디렉토리 경로
        """
        self.prompts_dir = Path(prompts_dir)
        self.prompts_cache: Dict[str, Dict[str, Any]] = {}
        self._load_all_prompts()

    def _load_all_prompts(self) -> None:
        """모든 프롬프트 파일을 로드하여 캐시에 저장"""
        try:
            if not self.prompts_dir.exists():
                logger.warning(
                    f"프롬프트 디렉토리가 존재하지 않습니다: {self.prompts_dir}"
                )
                return

            for yaml_file in self.prompts_dir.glob("*.yaml"):
                try:
                    with open(yaml_file, "r", encoding="utf-8") as f:
                        content = yaml.safe_load(f)

                    file_name = yaml_file.stem
                    self.prompts_cache[file_name] = content
                    logger.info(f"프롬프트 파일 로드 완료: {yaml_file.name}")

                except Exception as e:
                    logger.error(f"프롬프트 파일 로드 실패 {yaml_file}: {e}")

            logger.info(f"총 {len(self.prompts_cache)}개 프롬프트 파일 로드 완료")

        except Exception as e:
            logger.error(f"프롬프트 로드 중 오류 발생: {e}")

    def get_prompt_template(self, category: str, prompt_name: str) -> Optional[str]:
        """
        프롬프트 템플릿 가져오기

        Args:
            category: 프롬프트 카테고리 (파일명)
            prompt_name: 프롬프트 이름

        Returns:
            프롬프트 템플릿 문자열 또는 None
        """
        try:
            if category not in self.prompts_cache:
                logger.error(f"프롬프트 카테고리를 찾을 수 없습니다: {category}")
                return None

            category_data = self.prompts_cache[category]

            # 중첩된 구조 탐색
            if prompt_name in category_data:
                prompt_data = category_data[prompt_name]
                if isinstance(prompt_data, dict) and "template" in prompt_data:
                    return prompt_data["template"]
                elif isinstance(prompt_data, str):
                    return prompt_data

            # 중첩된 구조에서 찾기
            for key, value in category_data.items():
                if isinstance(value, dict) and prompt_name in value:
                    prompt_data = value[prompt_name]
                    if isinstance(prompt_data, dict) and "template" in prompt_data:
                        return prompt_data["template"]
                    elif isinstance(prompt_data, str):
                        return prompt_data

            logger.error(f"프롬프트를 찾을 수 없습니다: {category}.{prompt_name}")
            return None

        except Exception as e:
            logger.error(f"프롬프트 템플릿 가져오기 실패: {e}")
            return None

    def format_prompt(self, category: str, prompt_name: str, **kwargs) -> Optional[str]:
        """
        프롬프트 템플릿에 변수를 치환하여 완성된 프롬프트 반환

        Args:
            category: 프롬프트 카테고리
            prompt_name: 프롬프트 이름
            **kwargs: 템플릿 변수들

        Returns:
            완성된 프롬프트 문자열 또는 None
        """
        try:
            template_str = self.get_prompt_template(category, prompt_name)
            if not template_str:
                return None

            # {variable} 형식의 템플릿 변수 치환 (Python str.format 사용)
            formatted_prompt = template_str.format(**kwargs)

            logger.debug(f"프롬프트 포맷팅 완료: {category}.{prompt_name}")
            return formatted_prompt

        except KeyError as e:
            logger.error(f"프롬프트 변수 누락: {e}")
            return None
        except Exception as e:
            logger.error(f"프롬프트 포맷팅 실패: {e}")
            return None

    def get_prompt_info(
        self, category: str, prompt_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        프롬프트 메타데이터 정보 가져오기

        Args:
            category: 프롬프트 카테고리
            prompt_name: 프롬프트 이름

        Returns:
            프롬프트 메타데이터 또는 None
        """
        try:
            if category not in self.prompts_cache:
                return None

            category_data = self.prompts_cache[category]

            # 직접 찾기
            if prompt_name in category_data:
                return category_data[prompt_name]

            # 중첩된 구조에서 찾기
            for key, value in category_data.items():
                if isinstance(value, dict) and prompt_name in value:
                    return value[prompt_name]

            return None

        except Exception as e:
            logger.error(f"프롬프트 정보 가져오기 실패: {e}")
            return None

    def list_prompts(self) -> Dict[str, list]:
        """
        사용 가능한 모든 프롬프트 목록 반환

        Returns:
            카테고리별 프롬프트 목록
        """
        result = {}

        for category, data in self.prompts_cache.items():
            prompts = []

            def extract_prompts(obj, prefix=""):
                if isinstance(obj, dict):
                    for key, value in obj.items():
                        if isinstance(value, dict):
                            if "template" in value:
                                prompts.append(f"{prefix}{key}")
                            else:
                                extract_prompts(value, f"{prefix}{key}.")
                        elif isinstance(value, str) and key != "template":
                            prompts.append(f"{prefix}{key}")

            extract_prompts(data)
            result[category] = prompts

        return result

    def reload_prompts(self) -> None:
        """프롬프트 캐시를 다시 로드"""
        logger.info("프롬프트 캐시 다시 로드 중...")
        self.prompts_cache.clear()
        self._load_all_prompts()

    def validate_prompt_parameters(
        self, category: str, prompt_name: str, **kwargs
    ) -> tuple[bool, list]:
        """
        프롬프트 파라미터 유효성 검사

        Args:
            category: 프롬프트 카테고리
            prompt_name: 프롬프트 이름
            **kwargs: 검사할 파라미터들

        Returns:
            (유효성 여부, 오류 메시지 목록)
        """
        try:
            prompt_info = self.get_prompt_info(category, prompt_name)
            if not prompt_info or "parameters" not in prompt_info:
                return True, []  # 파라미터 정의가 없으면 통과

            errors = []
            parameters = prompt_info["parameters"]

            for param in parameters:
                param_name = param.get("name")
                param_type = param.get("type", "string")
                required = param.get("required", False)

                if required and param_name not in kwargs:
                    errors.append(f"필수 파라미터 누락: {param_name}")
                    continue

                if param_name in kwargs:
                    value = kwargs[param_name]

                    # 타입 검사
                    if param_type == "integer" and not isinstance(value, int):
                        errors.append(f"파라미터 {param_name}는 정수여야 합니다")
                    elif param_type == "string" and not isinstance(value, str):
                        errors.append(f"파라미터 {param_name}는 문자열이어야 합니다")

                    # 범위 검사
                    if param_type == "integer":
                        min_val = param.get("min")
                        max_val = param.get("max")
                        if min_val is not None and value < min_val:
                            errors.append(
                                f"파라미터 {param_name}는 {min_val} 이상이어야 합니다"
                            )
                        if max_val is not None and value > max_val:
                            errors.append(
                                f"파라미터 {param_name}는 {max_val} 이하여야 합니다"
                            )

            return len(errors) == 0, errors

        except Exception as e:
            logger.error(f"파라미터 유효성 검사 실패: {e}")
            return False, [f"유효성 검사 오류: {str(e)}"]


# 싱글톤 인스턴스
_prompt_loader_instance = None


def get_prompt_loader() -> PromptLoaderService:
    """프롬프트 로더 싱글톤 인스턴스 반환"""
    global _prompt_loader_instance
    if _prompt_loader_instance is None:
        _prompt_loader_instance = PromptLoaderService()
    return _prompt_loader_instance
