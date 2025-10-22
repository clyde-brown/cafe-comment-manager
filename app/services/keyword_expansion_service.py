#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
키워드 확장 서비스
Gemini API를 사용한 마케팅 키워드 자동 확장
"""

import logging
import time
import json
import re
import asyncio
from typing import Optional

from app.models.keyword_expansion import (
    KeywordExpansionRequest,
    KeywordExpansionResponse,
    KeywordsByCategory,
    KeywordCategory,
    PromptType,
)
from app.services.llm_settings_service import create_llm_settings_service
from app.services.prompt_loader_service import get_prompt_loader

logger = logging.getLogger(__name__)


class KeywordExpansionService:
    """
    키워드 확장 서비스 클래스
    Gemini API를 사용하여 마케팅 키워드를 자동으로 확장합니다.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        """
        Args:
            gemini_api_key: Gemini API 키 (없으면 설정에서 불러오거나 Mock 모드)
        """
        # LLM 설정 서비스 초기화
        self.llm_settings_service = create_llm_settings_service()

        # 프롬프트 로더 서비스 초기화
        self.prompt_loader = get_prompt_loader()

        # API 키 결정 (매개변수 > 설정 파일 > Mock 모드)
        self.gemini_api_key = (
            gemini_api_key or self.llm_settings_service.get_current_api_key()
        )
        self.current_model = self.llm_settings_service.get_current_model()
        self.use_mock = self.gemini_api_key is None

        if not self.use_mock:
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.gemini_api_key)

                # 설정된 모델 사용 (기본값: gemini-2.0-flash-exp)
                model_name = self.current_model or "gemini-2.0-flash-exp"
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"Gemini API 초기화 완료 (모델: {model_name})")
            except Exception as e:
                logger.warning(f"Gemini API 초기화 실패, Mock 모드로 전환: {e}")
                self.use_mock = True

    def _create_prompt(
        self,
        target_keyword: str,
        keyword_count: int,
        prompt_type: PromptType = PromptType.BASIC,
    ) -> str:
        """키워드 확장 프롬프트 생성"""
        try:
            # 시스템 프롬프트와 유저 프롬프트 로드
            system_prompt = self.prompt_loader.get_prompt_template(
                category="keyword_expansion", prompt_name="system_prompt"
            )
            user_prompt = self.prompt_loader.get_prompt_template(
                category="keyword_expansion", prompt_name="user_prompt"
            )

            if system_prompt and user_prompt:
                # 유저 프롬프트에 변수 치환
                formatted_user_prompt = self.prompt_loader.format_prompt(
                    "keyword_expansion",
                    "user_prompt",
                    target_keyword=target_keyword,
                    keyword_count=keyword_count,
                )

                # 시스템 프롬프트와 유저 프롬프트 결합
                prompt = f"{system_prompt}\n\n{formatted_user_prompt}"
                logger.debug(f"외부 프롬프트 템플릿 사용: {prompt_type.value}")
                return prompt
            else:
                logger.warning(
                    f"외부 프롬프트 로드 실패 ({prompt_type.value}), 기본 프롬프트 사용"
                )

        except Exception as e:
            logger.error(f"프롬프트 로드 중 오류: {e}, 기본 프롬프트 사용")

        # 기본 프롬프트 (fallback)
        return f"""
당신은 20년차 마케터입니다. 특정 키워드를 들었을 때 함께 떠올릴 수 있는 단어나 개념을 연상하고 분류하는 일을 전문으로 합니다.
단순한 유의어를 넘어 잠재 고객들이 '{target_keyword}'와 관련해 겪을 수 있거나 대비하거나 행동으로 연결될 수 있는 단어 {keyword_count}개 만들어주세요.

** 사용자가 입력한 단어: '{target_keyword}'

** 다음 단계로 생각하세요:
- 먼저 '{target_keyword}'의 의미 범위를 파악합니다.
- 그다음, 잠재 고객들이 겪을 수 있는 수 있는 감정, 상황, 행동을 확장합니다.
- 마지막으로, 이 단어들을 5개 카테고리로 분류합니다.

** 카테고리는 다음과 같습니다:
1. 유사어 / 동의어
2. 반의어 / 대비어
3. 상황·감정 연상어 (사람이 느끼는 감정, 상태, 상황)
4. 대응 행동·제품 (관련된 행동, 서비스, 물건)
5. 환경·자연 관련어 (계절, 날씨, 기후 등 맥락적 단어)

** 출력은 아래 예시와 같이 JSON 배열 형식으로 해주세요.

```json
[
  {{
    "key": "유사어",
    "values": ["무더위", "열대야", "찜통더위"]
  }},
  {{
    "key": "반의어", 
    "values": ["시원", "그늘", "서늘한 바람"]
  }},
  {{
    "key": "상황_감정",
    "values": ["짜증", "갈증", "지침"]
  }},
  {{
    "key": "대응_행동",
    "values": ["에어컨", "부채", "아이스커피"]
  }},
  {{
    "key": "환경_자연",
    "values": ["땡볕", "열돔", "기후변화"]
  }}
]
```
"""

    def _parse_json_response(self, response_text: str) -> Optional[list]:
        """AI 응답에서 JSON 추출 및 파싱 (새로운 배열 형식)"""
        try:
            # JSON 부분만 추출 (```json과 ``` 사이의 내용)
            json_match = re.search(r"```json\s*\n(.*?)\n```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # JSON 마커가 없으면 [] 또는 {} 기준으로 찾기
                json_match = re.search(r"[\[\{].*[\]\}]", response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text.strip()

            # JSON 파싱
            keywords_data = json.loads(json_str)

            # 배열 형식인지 확인하고 변환
            if isinstance(keywords_data, list):
                return keywords_data
            elif isinstance(keywords_data, dict):
                # 기존 객체 형식을 배열 형식으로 변환
                return [{"key": k, "values": v} for k, v in keywords_data.items()]
            else:
                logger.error(f"예상하지 못한 JSON 형식: {type(keywords_data)}")
                return None

        except json.JSONDecodeError as e:
            logger.error(f"JSON 파싱 오류: {e}")
            logger.debug(f"원본 텍스트: {response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"응답 파싱 오류: {e}")
            return None

    async def _generate_with_gemini(self, prompt: str) -> str:
        """Gemini API를 사용하여 키워드 생성"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.model.generate_content(prompt)
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini API 호출 오류: {e}")
            raise

    def _generate_mock_keywords(self, target_keyword: str, keyword_count: int) -> list:
        """Mock 키워드 생성 (테스트용) - 새로운 배열 형식"""
        keywords_per_category = keyword_count // 5

        return [
            {
                "key": "유사어",
                "values": [f"{target_keyword}", f"{target_keyword} 관련"][
                    :keywords_per_category
                ],
            },
            {
                "key": "반의어",
                "values": [f"안티 {target_keyword}", f"반대 {target_keyword}"][
                    :keywords_per_category
                ],
            },
            {
                "key": "상황_감정",
                "values": [f"{target_keyword} 스트레스", f"{target_keyword} 고민"][
                    :keywords_per_category
                ],
            },
            {
                "key": "대응_행동",
                "values": [f"{target_keyword} 해결", f"{target_keyword} 대처"][
                    :keywords_per_category
                ],
            },
            {
                "key": "환경_자연",
                "values": [f"{target_keyword} 환경", f"{target_keyword} 상황"][
                    :keywords_per_category
                ],
            },
        ]

    async def expand_keywords(
        self, request: KeywordExpansionRequest
    ) -> KeywordExpansionResponse:
        """
        키워드 확장 메인 함수

        Args:
            request: 키워드 확장 요청

        Returns:
            KeywordExpansionResponse: 확장된 키워드 결과
        """
        start_time = time.time()
        target_keyword = request.target_keyword
        keyword_count = request.keyword_count or 20
        prompt_type = request.prompt_type or PromptType.BASIC

        logger.info(
            f"키워드 확장 시작: '{target_keyword}' ({keyword_count}개, 프롬프트: {prompt_type.value})"
        )

        try:
            if self.use_mock:
                # Mock 모드
                logger.info("Mock 모드로 키워드 생성")
                await asyncio.sleep(0.5)  # 실제 API 호출처럼 보이게
                keywords_data = self._generate_mock_keywords(
                    target_keyword, keyword_count
                )
                raw_response = json.dumps(keywords_data, ensure_ascii=False, indent=2)
            else:
                # Gemini API 사용
                prompt = self._create_prompt(target_keyword, keyword_count, prompt_type)
                raw_response = await self._generate_with_gemini(prompt)
                keywords_data = self._parse_json_response(raw_response)

                if not keywords_data:
                    return KeywordExpansionResponse(
                        success=False,
                        target_keyword=target_keyword,
                        processing_time=time.time() - start_time,
                        message="AI 응답을 파싱하는데 실패했습니다.",
                        raw_response=raw_response,
                    )

            # 새로운 KeywordCategory 리스트로 변환
            keyword_categories = [KeywordCategory(**item) for item in keywords_data]

            # 하위 호환성을 위한 기존 형식도 생성 (가능한 경우)
            keywords_legacy = None
            try:
                legacy_dict = {item["key"]: item["values"] for item in keywords_data}
                # 기존 필드명과 매칭되는 경우만 변환
                if all(
                    key in ["직설적", "문제_니즈", "솔루션_혜택", "롱테일", "경쟁_대체"]
                    for key in legacy_dict.keys()
                ):
                    keywords_legacy = KeywordsByCategory(**legacy_dict)
            except Exception as e:
                logger.debug(f"기존 형식 변환 실패 (정상): {e}")

            # 총 키워드 개수 계산
            total_count = sum(len(category.values) for category in keyword_categories)

            processing_time = time.time() - start_time

            logger.info(
                f"키워드 확장 완료: {total_count}개 생성, {processing_time:.2f}초 소요"
            )

            return KeywordExpansionResponse(
                success=True,
                target_keyword=target_keyword,
                keywords=keyword_categories,
                keywords_legacy=keywords_legacy,
                total_count=total_count,
                processing_time=processing_time,
                message=f"{total_count}개의 키워드가 성공적으로 생성되었습니다.",
                raw_response=raw_response,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"키워드 확장 중 오류 발생: {e}", exc_info=True)

            return KeywordExpansionResponse(
                success=False,
                target_keyword=target_keyword,
                processing_time=processing_time,
                message=f"키워드 확장 중 오류 발생: {str(e)}",
            )


def create_keyword_expansion_service(
    gemini_api_key: Optional[str] = None,
) -> KeywordExpansionService:
    """키워드 확장 서비스 인스턴스 생성"""
    return KeywordExpansionService(gemini_api_key=gemini_api_key)
