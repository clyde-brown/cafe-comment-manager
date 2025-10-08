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
)
from app.services.llm_settings_service import create_llm_settings_service

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

    def _create_prompt(self, target_keyword: str, keyword_count: int) -> str:
        """키워드 확장 프롬프트 생성"""
        return f"""
당신은 마케팅 키워드 추출 전문가입니다.  
주어진 키워드와 관련된 유사 키워드, 연관 검색어, 잠재 고객이 실제로 검색할 법한 변형 키워드 {keyword_count}개를 제안해주세요.
키워드의 유형은 다음과 같이 다양하게 포함해야 합니다:

1. 직설적 키워드 (예: 제품명, 서비스명)  
2. 문제/니즈 기반 키워드 (고객이 불편함이나 필요를 표현하는 방식)  
3. 솔루션/혜택 키워드 (서비스의 장점, 효과, 결과 중심)  
4. 롱테일 키워드 (자연스러운 문장형 검색어, 구체적 상황 포함)  
5. 경쟁/대체 키워드 (비슷한 제품군, 대체제 관련)

- 요구사항  
출력은 반드시 아래 JSON 형식으로 해주세요:

```json
{{{{
  "직설적": [...],
  "문제_니즈": [...],
  "솔루션_혜택": [...],
  "롱테일": [...],
  "경쟁_대체": [...]
}}}}
```

- 입력키워드: {target_keyword}
"""

    def _parse_json_response(self, response_text: str) -> Optional[dict]:
        """AI 응답에서 JSON 추출 및 파싱"""
        try:
            # JSON 부분만 추출 (```json과 ``` 사이의 내용)
            json_match = re.search(r"```json\s*\n(.*?)\n```", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # JSON 마커가 없으면 {} 기준으로 찾기
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    json_str = response_text.strip()

            # JSON 파싱
            keywords_data = json.loads(json_str)
            return keywords_data

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

    def _generate_mock_keywords(self, target_keyword: str, keyword_count: int) -> dict:
        """Mock 키워드 생성 (테스트용)"""
        keywords_per_category = keyword_count // 5

        return {
            "직설적": [
                f"{target_keyword}",
                f"{target_keyword} 추천",
            ][:keywords_per_category],
            "문제_니즈": [
                f"{target_keyword} 문제",
                f"{target_keyword} 고민",
            ][:keywords_per_category],
            "솔루션_혜택": [
                f"{target_keyword} 해결",
                f"{target_keyword} 효과",
            ][:keywords_per_category],
            "롱테일": [
                f"{target_keyword} 어떻게 하나요",
                f"{target_keyword} 가장 좋은 방법",
            ][:keywords_per_category],
            "경쟁_대체": [
                f"{target_keyword} 대신",
                f"{target_keyword} 비슷한",
            ][:keywords_per_category],
        }

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

        logger.info(f"키워드 확장 시작: '{target_keyword}' ({keyword_count}개)")

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
                prompt = self._create_prompt(target_keyword, keyword_count)
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

            # KeywordsByCategory 모델로 변환
            keywords_by_category = KeywordsByCategory(**keywords_data)

            # 총 키워드 개수 계산
            total_count = sum(
                [
                    len(keywords_by_category.직설적),
                    len(keywords_by_category.문제_니즈),
                    len(keywords_by_category.솔루션_혜택),
                    len(keywords_by_category.롱테일),
                    len(keywords_by_category.경쟁_대체),
                ]
            )

            processing_time = time.time() - start_time

            logger.info(
                f"키워드 확장 완료: {total_count}개 생성, {processing_time:.2f}초 소요"
            )

            return KeywordExpansionResponse(
                success=True,
                target_keyword=target_keyword,
                keywords=keywords_by_category,
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
