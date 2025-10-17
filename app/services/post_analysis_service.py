#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
게시글 분석 및 댓글 생성 서비스
Gemini 2.5 Flash를 사용한 게시글 분석 및 댓글 생성
"""

import json
import logging
import re
import time
import asyncio
from typing import List, Dict, Any, Optional

from app.models.post_analysis import (
    PostAnalysisRequest,
    PostAnalysisResult,
    PostAnalysisResponse,
    CommentGenerationRequest,
    GeneratedComment,
    CommentGenerationResponse,
    PostAnalysisAndCommentRequest,
    PostAnalysisAndCommentResponse,
)
from app.services.prompt_loader_service import get_prompt_loader
from app.services.llm_settings_service import create_llm_settings_service

logger = logging.getLogger(__name__)


class GeminiPostAnalysisProvider:
    """
    Gemini API를 사용한 게시글 분석 및 댓글 생성 클래스.
    실제 AI API를 호출하여 게시글 분석과 댓글 생성을 수행합니다.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.prompt_loader = get_prompt_loader()

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

                # 설정된 모델 사용 (기본값: gemini-2.5-flash)
                model_name = self.current_model or "gemini-2.5-flash"
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"Gemini API 초기화 완료 (모델: {model_name})")
            except Exception as e:
                logger.warning(f"Gemini API 초기화 실패, Mock 모드로 전환: {e}")
                self.use_mock = True

        if self.use_mock:
            logger.info("Mock 모드로 실행됩니다. API 키를 설정해주세요.")

    async def analyze_post(
        self, post_title: str, post_content: str
    ) -> PostAnalysisResult:
        """게시글을 분석하여 심리학적 분석 결과를 반환합니다."""

        if self.use_mock:
            return await self._mock_analyze_post(post_title, post_content)

        try:
            # 프롬프트 생성
            system_prompt = self.prompt_loader.get_prompt_template(
                category="post_analysis", prompt_name="system_prompt"
            )
            user_prompt = self.prompt_loader.format_prompt(
                category="post_analysis",
                prompt_name="user_prompt",
                post_title=post_title,
                post_content=post_content,
            )

            if not system_prompt or not user_prompt:
                logger.error("게시글 분석 프롬프트를 로드할 수 없습니다.")
                return await self._mock_analyze_post(post_title, post_content)

            # 시스템 프롬프트와 사용자 프롬프트 결합
            prompt = f"{system_prompt}\n\n{user_prompt}"

            # Gemini API 호출
            response = await asyncio.to_thread(self.model.generate_content, prompt)

            # JSON 응답 파싱
            response_text = response.text.strip()

            # ```json ... ``` 코드블록 제거
            cleaned_response = re.sub(r"^```json\n|\n```$", "", response_text.strip())

            try:
                parsed_data = json.loads(cleaned_response)

                # 리스트 형태의 응답을 문자열로 변환하는 헬퍼 함수
                def convert_to_string(value):
                    if isinstance(value, list):
                        return ", ".join(str(item) for item in value)
                    return str(value) if value is not None else ""

                return PostAnalysisResult(
                    **{
                        "주제": convert_to_string(parsed_data.get("주제", "")),
                        "감정": convert_to_string(parsed_data.get("감정", "")),
                        "핵심내용": convert_to_string(parsed_data.get("핵심내용", "")),
                        "댓글포인트": convert_to_string(
                            parsed_data.get("댓글포인트", "")
                        ),
                        "필요댓글유형": convert_to_string(
                            parsed_data.get("필요댓글유형", "일반")
                        ),
                        "상품추천유형": convert_to_string(
                            parsed_data.get("상품추천유형", "")
                        ),
                    }
                )

            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {e}, 응답: {cleaned_response}")
                return await self._mock_analyze_post(post_title, post_content)

        except Exception as e:
            logger.error(f"Gemini API 호출 오류: {e}")
            return await self._mock_analyze_post(post_title, post_content)

    async def _mock_analyze_post(
        self, post_title: str, post_content: str
    ) -> PostAnalysisResult:
        """Mock 분석 결과 생성 (API 실패 시 fallback)"""

        # 시뮬레이션을 위한 지연
        await asyncio.sleep(1.0)

        # 게시글 내용에 따른 분석 결과 생성
        if any(
            keyword in post_content.lower()
            for keyword in ["고민", "스트레스", "힘들", "우울", "불안"]
        ):
            return PostAnalysisResult(
                **{
                    "주제": "개인적 고민 및 감정 상담",
                    "감정": "스트레스, 불안, 도움 요청",
                    "핵심내용": "개인적인 어려움을 겪고 있으며 공감과 조언을 구하는 상황",
                    "댓글포인트": "감정적 지지, 경험 공유, 실질적 조언 제공",
                    "필요댓글유형": "공감",
                    "상품추천유형": "",
                }
            )
        elif any(
            keyword in post_content.lower()
            for keyword in ["추천", "구매", "선택", "고르기"]
        ):
            return PostAnalysisResult(
                **{
                    "주제": "제품 구매 추천 및 상담",
                    "감정": "선택 고민, 기대감, 정보 갈증",
                    "핵심내용": "제품 구매를 위한 정보 수집 및 추천 요청",
                    "댓글포인트": "제품 비교, 사용 경험, 구체적 추천",
                    "필요댓글유형": "상품추천",
                    "상품추천유형": "일반적 추천",
                }
            )
        elif any(
            keyword in post_content.lower()
            for keyword in ["후기", "리뷰", "사용", "경험"]
        ):
            return PostAnalysisResult(
                **{
                    "주제": "제품 후기 및 경험 공부",
                    "감정": "만족감, 정보 공유 욕구",
                    "핵심내용": "제품 사용 경험을 공유하며 다른 사용자들과 소통하고자 함",
                    "댓글포인트": "경험 공감, 추가 질문, 비슷한 경험 공유",
                    "필요댓글유형": "일반",
                    "상품추천유형": "",
                }
            )
        else:
            return PostAnalysisResult(
                **{
                    "주제": "일반적 정보 공유 및 소통",
                    "감정": "정보 공유, 소통 욕구",
                    "핵심내용": "일반적인 정보나 생각을 공유하며 커뮤니티와 소통하고자 함",
                    "댓글포인트": "공감 표현, 관련 경험 공유, 추가 정보 제공",
                    "필요댓글유형": "일반",
                    "상품추천유형": "",
                }
            )

    async def generate_comments(
        self, post_title: str, post_content: str, analysis: PostAnalysisResult
    ) -> List[GeneratedComment]:
        """분석 결과를 바탕으로 5가지 스타일의 댓글을 생성합니다."""

        if self.use_mock:
            return await self._mock_generate_comments(
                post_title, post_content, analysis
            )

        try:
            # 프롬프트 생성
            system_prompt = self.prompt_loader.get_prompt_template(
                category="comment_generation", prompt_name="system_prompt"
            )
            user_prompt = self.prompt_loader.format_prompt(
                category="comment_generation",
                prompt_name="user_prompt",
                post_title=post_title,
                post_content=post_content,
                analysis_topic=analysis.topic,
                analysis_emotion=analysis.emotion,
                analysis_summary=analysis.summary,
                analysis_points=analysis.comment_points,
                analysis_comment_type=analysis.comment_type,
                analysis_product_type=analysis.product_type or "",
            )

            if not system_prompt or not user_prompt:
                logger.error("댓글 생성 프롬프트를 로드할 수 없습니다.")
                return await self._mock_generate_comments(
                    post_title, post_content, analysis
                )

            # 시스템 프롬프트와 사용자 프롬프트 결합
            prompt = f"{system_prompt}\n\n{user_prompt}"

            # Gemini API 호출
            response = await asyncio.to_thread(self.model.generate_content, prompt)

            # JSON 응답 파싱
            response_text = response.text.strip()

            # ```json ... ``` 코드블록 제거
            cleaned_response = re.sub(r"^```json\n|\n```$", "", response_text.strip())

            try:
                parsed_data = json.loads(cleaned_response)

                comments = []
                for comment_data in parsed_data:
                    comments.append(
                        GeneratedComment(
                            style=comment_data.get("style", ""),
                            icon=comment_data.get("icon", "💬"),
                            content=comment_data.get("content", ""),
                        )
                    )

                return comments

            except json.JSONDecodeError as e:
                logger.error(f"JSON 파싱 오류: {e}, 응답: {cleaned_response}")
                return await self._mock_generate_comments(
                    post_title, post_content, analysis
                )

        except Exception as e:
            logger.error(f"Gemini API 호출 오류: {e}")
            return await self._mock_generate_comments(
                post_title, post_content, analysis
            )

    async def _mock_generate_comments(
        self, post_title: str, post_content: str, analysis: PostAnalysisResult
    ) -> List[GeneratedComment]:
        """Mock 댓글 생성 (API 실패 시 fallback)"""

        # 시뮬레이션을 위한 지연
        await asyncio.sleep(1.5)

        # 분석 결과에 따른 댓글 생성
        if analysis.comment_type == "공감":
            return [
                GeneratedComment(
                    style="공감형",
                    icon="👍",
                    content="정말 힘드시겠어요 ㅠㅠ 저도 비슷한 경험이 있어서 마음이 너무 아픕니다. 이런 상황에서는 혼자 견디기가 정말 어려우실 것 같아요.",
                ),
                GeneratedComment(
                    style="질문형",
                    icon="❓",
                    content="혹시 주변에 이야기할 수 있는 분이 계신가요? 전문가의 도움을 받아보시는 것도 좋을 것 같은데 어떠세요?",
                ),
                GeneratedComment(
                    style="조언형",
                    icon="💡",
                    content="우선 본인의 감정을 인정하고 받아들이는 것이 중요해요. 작은 것부터 하나씩 해결해 나가시면 분명 좋아질 거예요.",
                ),
                GeneratedComment(
                    style="친근형",
                    icon="😊",
                    content="힘내세요! 지금은 어렵겠지만 이 시간도 지나갈 거예요. 저희가 응원하고 있으니까 너무 혼자 견디려 하지 마세요 💪",
                ),
                GeneratedComment(
                    style="경험공유형",
                    icon="🤝",
                    content="저도 예전에 비슷한 일을 겪었는데, 시간이 지나고 나니 그때의 경험이 저를 더 강하게 만들어준 것 같아요. 지금은 힘들어도 분명 좋은 날이 올 거예요.",
                ),
            ]
        elif analysis.comment_type == "상품추천":
            return [
                GeneratedComment(
                    style="공감형",
                    icon="👍",
                    content="선택하기 정말 어려우시겠어요! 저도 비슷한 고민을 했었는데 정말 많이 고민했던 기억이 나네요.",
                ),
                GeneratedComment(
                    style="질문형",
                    icon="❓",
                    content="혹시 주로 어떤 용도로 사용하실 예정인가요? 예산은 어느 정도로 생각하고 계신지도 궁금해요!",
                ),
                GeneratedComment(
                    style="조언형",
                    icon="💡",
                    content="용도와 예산을 먼저 명확히 하시고, 리뷰를 꼼꼼히 확인해보시는 것을 추천드려요. A/S나 보증 기간도 중요한 고려사항이에요.",
                ),
                GeneratedComment(
                    style="친근형",
                    icon="😊",
                    content="좋은 선택하시길 바라요! 충분히 고민하신 만큼 만족스러운 구매가 되실 거예요 ✨",
                ),
                GeneratedComment(
                    style="경험공유형",
                    icon="🤝",
                    content="저는 비슷한 제품을 사용해봤는데 정말 만족스러웠어요. 특히 내구성이 좋아서 오래 사용할 수 있을 것 같아요!",
                ),
            ]
        else:  # 일반
            return [
                GeneratedComment(
                    style="공감형",
                    icon="👍",
                    content="좋은 정보 감사해요! 정말 유용한 내용이네요 😊",
                ),
                GeneratedComment(
                    style="질문형",
                    icon="❓",
                    content="혹시 더 자세한 이야기도 들려주실 수 있나요? 정말 흥미로운 내용이에요!",
                ),
                GeneratedComment(
                    style="조언형",
                    icon="💡",
                    content="이런 정보를 공유해주셔서 정말 도움이 많이 됐어요. 다른 분들에게도 유용할 것 같아요.",
                ),
                GeneratedComment(
                    style="친근형",
                    icon="😊",
                    content="글 잘 읽었습니다! 덕분에 새로운 것을 알게 되었네요. 좋은 하루 되세요 ✨",
                ),
                GeneratedComment(
                    style="경험공유형",
                    icon="🤝",
                    content="저도 비슷한 생각을 하고 있었는데 공감이 많이 되네요! 좋은 글 공유해주셔서 감사해요.",
                ),
            ]


class PostAnalysisService:
    """
    게시글 분석 및 댓글 생성을 위한 서비스 클래스.
    다양한 게시글 분석 및 댓글 생성 기능을 제공합니다.
    """

    def __init__(self, provider: GeminiPostAnalysisProvider):
        self.provider = provider
        logger.info("PostAnalysisService 초기화 완료.")

    async def analyze_post(self, request: PostAnalysisRequest) -> PostAnalysisResponse:
        """
        게시글을 분석합니다.
        """
        logger.info(
            f"게시글 분석 요청 수신: 제목='{request.post_title}', 내용 길이={len(request.post_content)} 글자"
        )

        start_time = time.time()

        try:
            analysis = await self.provider.analyze_post(
                request.post_title, request.post_content
            )

            processing_time = time.time() - start_time

            logger.info(
                f"게시글 분석 완료: 주제='{analysis.topic}', 처리시간={processing_time:.2f}초"
            )

            return PostAnalysisResponse(
                success=True,
                analysis=analysis,
                processing_time=processing_time,
                message="게시글 분석이 성공적으로 완료되었습니다.",
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"게시글 분석 중 오류가 발생했습니다: {str(e)}"

            logger.error(
                f"게시글 분석 오류: {error_message}, 처리시간: {processing_time:.2f}초"
            )

            return PostAnalysisResponse(
                success=False,
                analysis=None,
                processing_time=processing_time,
                message=error_message,
            )

    async def generate_comments(
        self, request: CommentGenerationRequest
    ) -> CommentGenerationResponse:
        """
        분석 결과를 바탕으로 댓글을 생성합니다.
        """
        logger.info(
            f"댓글 생성 요청 수신: 제목='{request.post_title}', 댓글 유형='{request.analysis.comment_type}'"
        )

        start_time = time.time()

        try:
            comments = await self.provider.generate_comments(
                request.post_title, request.post_content, request.analysis
            )

            processing_time = time.time() - start_time

            logger.info(
                f"댓글 생성 완료: {len(comments)}개 댓글, 처리시간={processing_time:.2f}초"
            )

            return CommentGenerationResponse(
                success=True,
                comments=comments,
                processing_time=processing_time,
                message=f"{len(comments)}개의 댓글이 성공적으로 생성되었습니다.",
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"댓글 생성 중 오류가 발생했습니다: {str(e)}"

            logger.error(
                f"댓글 생성 오류: {error_message}, 처리시간: {processing_time:.2f}초"
            )

            return CommentGenerationResponse(
                success=False,
                comments=[],
                processing_time=processing_time,
                message=error_message,
            )

    async def analyze_and_generate_comments(
        self, request: PostAnalysisAndCommentRequest
    ) -> PostAnalysisAndCommentResponse:
        """
        게시글 분석과 댓글 생성을 한 번에 수행합니다.
        """
        logger.info(f"통합 분석 및 댓글 생성 요청 수신: 제목='{request.post_title}'")

        start_time = time.time()

        try:
            # 게시글 분석과 댓글 생성을 병렬로 실행
            analysis_task = self.provider.analyze_post(
                request.post_title, request.post_content
            )

            # 분석 결과를 기다린 후 댓글 생성
            analysis = await analysis_task
            comments = await self.provider.generate_comments(
                request.post_title, request.post_content, analysis
            )

            processing_time = time.time() - start_time

            logger.info(
                f"통합 처리 완료: 분석 주제='{analysis.topic}', 댓글 {len(comments)}개, 처리시간={processing_time:.2f}초"
            )

            return PostAnalysisAndCommentResponse(
                success=True,
                analysis=analysis,
                comments=comments,
                processing_time=processing_time,
                message=f"게시글 분석 및 {len(comments)}개 댓글 생성이 성공적으로 완료되었습니다.",
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_message = f"게시글 분석 및 댓글 생성 중 오류가 발생했습니다: {str(e)}"

            logger.error(
                f"통합 처리 오류: {error_message}, 처리시간: {processing_time:.2f}초"
            )

            return PostAnalysisAndCommentResponse(
                success=False,
                analysis=None,
                comments=[],
                processing_time=processing_time,
                message=error_message,
            )


def create_post_analysis_service() -> PostAnalysisService:
    """PostAnalysisService 인스턴스를 생성합니다."""
    provider = GeminiPostAnalysisProvider()
    return PostAnalysisService(provider)
