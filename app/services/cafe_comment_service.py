#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
카페 댓글 자동 생성 서비스
Gemini 2.5 Flash를 사용한 카페 게시글 댓글 생성
"""

import logging
import time
import asyncio
from typing import List, Dict, Any, Optional

from app.models.ai_reaction import (
    ArticleAnalysisRequest,
    CafeCommentResponse,
    CafeComment,
)
from app.services.prompt_loader_service import get_prompt_loader

logger = logging.getLogger(__name__)


class MockCafeCommentProvider:
    """
    카페 댓글 생성을 모의(Mock)하는 클래스.
    실제 AI API 호출 없이 미리 정의된 응답을 반환하여 개발 및 테스트를 용이하게 합니다.
    """

    def __init__(self, model_version: str = "Mock-Gemini-2.5-Flash"):
        self.model_version = model_version
        self.prompt_loader = get_prompt_loader()
        logger.info(
            f"MockCafeCommentProvider 초기화 완료. 모델 버전: {self.model_version}"
        )

    async def analyze_post(self, post_content: str) -> str:
        """카페 게시글 분석"""
        await asyncio.sleep(0.5)  # 비동기 작업 시뮬레이션

        # 게시글 유형 판단
        if any(
            keyword in post_content for keyword in ["고민", "스트레스", "힘들", "걱정"]
        ):
            return "주제: 직장 고민상담\n감정: 스트레스와 고민\n핵심내용: 직장 상사와의 갈등으로 인한 스트레스\n댓글포인트: 공감과 조언이 필요한 상황"
        elif any(
            keyword in post_content for keyword in ["맛집", "추천", "발견", "좋아요"]
        ):
            return "주제: 맛집 정보공유\n감정: 기쁨과 만족\n핵심내용: 새로운 맛집 발견 후 추천\n댓글포인트: 감사 표현과 추가 정보 요청"
        elif any(
            keyword in post_content for keyword in ["질문", "고민", "추천", "어떤"]
        ):
            return "주제: 구매 상담\n감정: 고민과 궁금증\n핵심내용: 제품 구매 관련 조언 요청\n댓글포인트: 구체적인 조언과 경험 공유"
        elif any(
            keyword in post_content for keyword in ["첫", "시작", "새로운", "출근"]
        ):
            return "주제: 일상 공유\n감정: 설렘과 긴장\n핵심내용: 새로운 시작에 대한 소감 공유\n댓글포인트: 축하와 응원이 필요한 상황"
        else:
            return "주제: 일반적인 게시글\n감정: 중립적\n핵심내용: 다양한 내용 포함\n댓글포인트: 상황에 맞는 적절한 반응"

    async def generate_comments(
        self, post_content: str, post_analysis: str
    ) -> List[Dict[str, str]]:
        """카페 댓글 생성"""
        await asyncio.sleep(1.0)  # 비동기 작업 시뮬레이션

        # 게시글 유형에 따른 댓글 생성
        if "고민상담" in post_analysis:
            return [
                {
                    "style": "공감형",
                    "icon": "👍",
                    "content": "정말 힘드시겠어요 ㅠㅠ 저도 비슷한 경험이 있어서 마음이 아프네요. 힘내세요!",
                },
                {
                    "style": "질문형",
                    "icon": "❓",
                    "content": "혹시 HR팀이나 상급자에게 상담을 요청해보신 적은 있나요?",
                },
                {
                    "style": "조언형",
                    "icon": "💡",
                    "content": "상사와의 일대일 대화를 통해 오해를 풀어보시는 것도 좋을 것 같아요. 차분하게 대화해보세요.",
                },
                {
                    "style": "친근형",
                    "icon": "😊",
                    "content": "많이 속상하셨을 것 같아요. 저희가 응원하고 있으니까 너무 스트레스 받지 마세요 💪",
                },
                {
                    "style": "경험공유형",
                    "icon": "🤝",
                    "content": "저도 예전에 비슷한 일이 있었는데, 시간이 지나면서 관계가 개선되더라고요. 포기하지 마세요!",
                },
            ]
        elif "맛집" in post_analysis:
            return [
                {
                    "style": "공감형",
                    "icon": "👍",
                    "content": "와 정말 맛있어 보이네요! 사진만 봐도 군침이 도네요 🤤",
                },
                {
                    "style": "질문형",
                    "icon": "❓",
                    "content": "혹시 가격대는 어느 정도인가요? 그리고 예약이 필요한가요?",
                },
                {
                    "style": "조언형",
                    "icon": "💡",
                    "content": "좋은 정보 감사해요! 다음에 강남 가면 꼭 가봐야겠어요 ⭐",
                },
                {
                    "style": "친근형",
                    "icon": "😊",
                    "content": "맛집 정보 공유해주셔서 감사해요! 데이트 코스로 딱 좋겠네요 💕",
                },
                {
                    "style": "경험공유형",
                    "icon": "🤝",
                    "content": "저도 이탈리안 음식 좋아하는데 꼭 가봐야겠어요! 추천 감사합니다 🍝",
                },
            ]
        elif "구매" in post_analysis or "노트북" in post_content:
            return [
                {
                    "style": "공감형",
                    "icon": "👍",
                    "content": "노트북 선택 정말 어려우시겠어요! 저도 고민 많이 했었는데 이해해요 😅",
                },
                {
                    "style": "질문형",
                    "icon": "❓",
                    "content": "혹시 들고 다니실 일이 많으신가요? 무게도 중요한 고려사항이에요!",
                },
                {
                    "style": "조언형",
                    "icon": "💡",
                    "content": "용도 보시면 맥북보다는 윈도우 노트북이 더 실용적일 것 같아요. 게임도 고려하시니까요!",
                },
                {
                    "style": "친근형",
                    "icon": "😊",
                    "content": "대학생이시면 학생 할인도 알아보세요! 꽤 할인 폭이 커요 💻",
                },
                {
                    "style": "경험공유형",
                    "icon": "🤝",
                    "content": "저는 LG 그램 쓰는데 가볍고 배터리도 오래가서 만족해요! 참고하세요 😊",
                },
            ]
        elif "첫 출근" in post_content or "새로운 시작" in post_analysis:
            return [
                {
                    "style": "공감형",
                    "icon": "👍",
                    "content": "첫 출근 정말 축하드려요! 새로운 시작이라 설레시겠어요 🎉",
                },
                {
                    "style": "질문형",
                    "icon": "❓",
                    "content": "어떤 분야 회사인가요? 첫날 분위기는 어떠셨어요?",
                },
                {
                    "style": "조언형",
                    "icon": "💡",
                    "content": "처음엔 적응하기 어려우실 수 있지만 금방 익숙해지실 거예요! 화이팅!",
                },
                {
                    "style": "친근형",
                    "icon": "😊",
                    "content": "동료분들이 친절하시다니 다행이네요! 좋은 직장 만나신 것 같아요 💪",
                },
                {
                    "style": "경험공유형",
                    "icon": "🤝",
                    "content": "저도 첫 출근 때 떨렸는데 지금은 잘 적응했어요! 응원할게요 화이팅! 🔥",
                },
            ]
        else:
            return [
                {
                    "style": "공감형",
                    "icon": "👍",
                    "content": "좋은 글 잘 읽었어요! 공감되는 부분이 많네요 😊",
                },
                {
                    "style": "질문형",
                    "icon": "❓",
                    "content": "혹시 더 자세한 이야기도 들려주실 수 있나요?",
                },
                {
                    "style": "조언형",
                    "icon": "💡",
                    "content": "좋은 정보 공유해주셔서 감사해요! 도움이 많이 됐어요",
                },
                {
                    "style": "친근형",
                    "icon": "😊",
                    "content": "글 잘 읽었습니다! 좋은 하루 되세요 ✨",
                },
                {
                    "style": "경험공유형",
                    "icon": "🤝",
                    "content": "저도 비슷한 생각을 하고 있었는데 공감이 많이 되네요!",
                },
            ]


class CafeCommentService:
    """
    카페 댓글 자동 생성을 위한 서비스 클래스.
    다양한 카페 댓글 생성 기능을 제공합니다.
    """

    def __init__(self, provider: MockCafeCommentProvider):
        self.provider = provider
        logger.info("CafeCommentService 초기화 완료.")

    async def generate_cafe_comments(
        self, request: ArticleAnalysisRequest
    ) -> CafeCommentResponse:
        """
        주어진 카페 게시글에 대한 댓글을 생성합니다.
        """
        post_content = request.article_text
        logger.info(f"카페 댓글 생성 요청 수신 (길이: {len(post_content)} 글자)")

        start_time = time.time()

        try:
            # 게시글 분석과 댓글 생성을 동시에 실행
            analysis_task = self.provider.analyze_post(post_content)
            comments_task = self.provider.generate_comments(post_content, "")

            post_analysis, comment_data = await asyncio.gather(
                analysis_task, comments_task
            )

            # 댓글 객체 생성
            comments = []
            for comment_info in comment_data:
                comment = CafeComment(
                    style=comment_info["style"],
                    icon=comment_info["icon"],
                    content=comment_info["content"],
                    tone=request.tone_style or "친근한톤",
                )
                comments.append(comment)

            processing_time = time.time() - start_time

            logger.info(
                f"카페 댓글 생성 완료: {len(comments)}개 댓글, 처리시간: {processing_time:.2f}초"
            )

            return CafeCommentResponse(
                success=True,
                post_analysis=post_analysis,
                comments=comments,
                processing_time=processing_time,
                message=f"카페 댓글 {len(comments)}개가 성공적으로 생성되었습니다.",
            )

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"카페 댓글 생성 중 오류 발생: {e}", exc_info=True)

            return CafeCommentResponse(
                success=False,
                post_analysis="",
                comments=[],
                processing_time=processing_time,
                message=f"카페 댓글 생성 중 오류 발생: {e}",
            )


def create_cafe_comment_service() -> CafeCommentService:
    """카페 댓글 생성 서비스를 생성하여 반환합니다."""
    mock_provider = MockCafeCommentProvider()
    return CafeCommentService(mock_provider)
