import json
import time
import logging
from typing import Optional, List
import google.generativeai as genai
from app.core.config import settings
from app.models.comment_generation import (
    CommentGenerationRequest,
    CommentGenerationResponse,
    CommentGenerationResult,
    GeneratedComment,
)
from app.services.prompt_loader_service import get_prompt_loader
from app.services.llm_settings_service import create_llm_settings_service

logger = logging.getLogger(__name__)


class CommentGenerationService:
    """댓글 생성 서비스"""

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

    async def generate_comments(
        self, request: CommentGenerationRequest
    ) -> CommentGenerationResponse:
        """게시글 분석 결과를 기반으로 댓글 생성"""
        start_time = time.time()

        try:
            logger.info("=== 댓글 생성 시작 ===")
            logger.info(f"게시글 내용: {request.post_content[:100]}...")
            logger.info(f"분석 결과: {request.post_analysis}")

            # Mock 모드 처리
            if self.use_mock:
                logger.info("Mock 모드로 댓글 생성")
                comments = self._generate_mock_comments()
            else:
                # 프롬프트 로드 및 포맷팅
                prompt = await self._format_prompt(request)
                logger.info(f"포맷된 프롬프트 길이: {len(prompt)}")

                # Gemini API 호출
                logger.info("Gemini API 호출 시작...")
                response = self.model.generate_content(prompt)
                logger.info("Gemini API 호출 완료")

                if not response.text:
                    raise Exception("Gemini API에서 빈 응답을 받았습니다")

                logger.info(f"AI 응답: {response.text}")

                # 응답 파싱
                comments = self._parse_comments_response(response.text)

            processing_time = time.time() - start_time
            logger.info(f"댓글 생성 완료 - 처리 시간: {processing_time:.2f}초")

            return CommentGenerationResponse(
                success=True,
                message="댓글이 성공적으로 생성되었습니다",
                comments=CommentGenerationResult(comments=comments),
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"댓글 생성 오류: {str(e)}"
            logger.error(error_msg, exc_info=True)

            return CommentGenerationResponse(
                success=False,
                message=error_msg,
                comments=None,
                processing_time=processing_time,
            )

    async def _format_prompt(self, request: CommentGenerationRequest) -> str:
        """프롬프트 포맷팅"""
        try:
            # 분석 결과를 문자열로 변환
            analysis_text = self._format_analysis_for_prompt(request.post_analysis)

            # 시스템 프롬프트와 유저 프롬프트 로드
            system_prompt = self.prompt_loader.get_prompt_template(
                category="comment_generation", prompt_name="system_prompt"
            )
            user_prompt = self.prompt_loader.get_prompt_template(
                category="comment_generation", prompt_name="user_prompt"
            )

            if not system_prompt or not user_prompt:
                raise Exception("프롬프트 템플릿을 로드할 수 없습니다")

            # 유저 프롬프트에 변수 치환
            formatted_user_prompt = self.prompt_loader.format_prompt(
                "comment_generation",
                "user_prompt",
                post_content=request.post_content,
                post_analysis=analysis_text,
            )

            # 시스템 프롬프트와 유저 프롬프트 결합
            formatted_prompt = f"{system_prompt}\n\n{formatted_user_prompt}"

            return formatted_prompt

        except Exception as e:
            logger.error(f"프롬프트 포맷팅 오류: {e}")
            raise

    def _format_analysis_for_prompt(self, analysis) -> str:
        """분석 결과를 프롬프트용 텍스트로 변환"""
        analysis_parts = []

        if hasattr(analysis, "topic") and analysis.topic:
            analysis_parts.append(f"주제: {analysis.topic}")

        if hasattr(analysis, "emotion") and analysis.emotion:
            analysis_parts.append(f"감정: {analysis.emotion}")

        if hasattr(analysis, "summary") and analysis.summary:
            analysis_parts.append(f"핵심내용: {analysis.summary}")

        if hasattr(analysis, "comment_points") and analysis.comment_points:
            analysis_parts.append(f"댓글포인트: {analysis.comment_points}")

        if hasattr(analysis, "comment_type") and analysis.comment_type:
            analysis_parts.append(f"필요댓글유형: {analysis.comment_type}")

        if hasattr(analysis, "product_type") and analysis.product_type:
            analysis_parts.append(f"상품추천유형: {analysis.product_type}")

        return "\n".join(analysis_parts)

    def _parse_comments_response(self, response_text: str) -> List[GeneratedComment]:
        """AI 응답에서 댓글 추출"""
        comments = []

        try:
            # 응답에서 각 댓글 유형별로 파싱
            comment_types = ["공감형", "질문형", "조언형", "친근형", "경험공유형"]

            for comment_type in comment_types:
                # 패턴: "공감형: [댓글 내용]"
                pattern = f"{comment_type}:"
                if pattern in response_text:
                    # 해당 유형의 댓글 추출
                    start_idx = response_text.find(pattern) + len(pattern)

                    # 다음 유형까지 또는 끝까지 추출
                    next_type_idx = len(response_text)
                    for next_type in comment_types:
                        if next_type != comment_type:
                            next_pattern = f"{next_type}:"
                            next_idx = response_text.find(next_pattern, start_idx)
                            if next_idx != -1 and next_idx < next_type_idx:
                                next_type_idx = next_idx

                    comment_content = response_text[start_idx:next_type_idx].strip()

                    # 대괄호 제거 및 정리
                    comment_content = comment_content.strip()
                    if comment_content.startswith("[") and comment_content.endswith(
                        "]"
                    ):
                        comment_content = comment_content[1:-1].strip()

                    # 줄바꿈 제거
                    comment_content = comment_content.replace("\n", " ").strip()

                    if comment_content:
                        # '-형' 제거
                        display_type = comment_type.replace("형", "")
                        comments.append(
                            GeneratedComment(type=display_type, content=comment_content)
                        )

            logger.info(f"파싱된 댓글 수: {len(comments)}")
            for comment in comments:
                logger.info(f"- {comment.type}: {comment.content}")

            return comments

        except Exception as e:
            logger.error(f"댓글 응답 파싱 오류: {e}")
            logger.error(f"원본 응답: {response_text}")

            # 파싱 실패 시 전체 응답을 하나의 댓글로 처리
            return [
                GeneratedComment(
                    type="일반형",
                    content=(
                        response_text[:200] + "..."
                        if len(response_text) > 200
                        else response_text
                    ),
                )
            ]

    def _generate_mock_comments(self) -> List[GeneratedComment]:
        """Mock 댓글 생성 (API 키가 없을 때 사용)"""
        return [
            GeneratedComment(
                type="공감",
                content="정말 공감이 많이 돼요! 저도 비슷한 상황을 겪어봐서 마음이 아프네요 ㅠㅠ",
            ),
            GeneratedComment(
                type="질문",
                content="혹시 어떤 방법을 시도해보셨나요? 궁금해서 여쭤봅니다!",
            ),
            GeneratedComment(
                type="조언",
                content="이런 상황에서는 차근차근 해결해나가시는 게 좋을 것 같아요. 너무 조급해하지 마세요!",
            ),
            GeneratedComment(
                type="친근",
                content="힘내세요! 분명 좋은 결과가 있을 거예요 💪 응원합니다!",
            ),
            GeneratedComment(
                type="경험공유",
                content="저도 예전에 비슷한 일이 있었는데, 시간이 지나니까 해결되더라구요. 너무 걱정 마세요~",
            ),
        ]


def create_comment_generation_service() -> CommentGenerationService:
    """댓글 생성 서비스 팩토리 함수"""
    return CommentGenerationService()
