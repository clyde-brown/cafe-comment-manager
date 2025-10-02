#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 리액션 분석 서비스
OpenAI GPT, Anthropic Claude, 또는 로컬 모델을 사용한 기사 분석
"""

import logging
import time
import re
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import asyncio
from abc import ABC, abstractmethod

# AI 모델 관련 imports (조건부)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    openai = None

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

# 로컬 모델 관련 imports (조건부)
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from app.models.ai_reaction import (
    ArticleAnalysisRequest,
    ReactionAnalysisResult,
    SentimentAnalysis,
    KeywordExtraction,
    CommentGeneration,
    ArticleSummary,
    QuestionGeneration,
    ToneAnalysis,
    FactCheckResult,
    SimpleReaction,
    SimplifiedResponse,
    SentimentType,
    ReactionType
)

logger = logging.getLogger(__name__)


class BaseAIProvider(ABC):
    """AI 제공자 기본 클래스"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.model_version = "unknown"
    
    @abstractmethod
    async def analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """감정 분석"""
        pass
    
    @abstractmethod
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> KeywordExtraction:
        """키워드 추출"""
        pass
    
    @abstractmethod
    async def generate_comments(self, text: str, max_comments: int = 5) -> CommentGeneration:
        """댓글 생성"""
        pass
    
    @abstractmethod
    async def summarize_article(self, text: str) -> ArticleSummary:
        """기사 요약"""
        pass
    
    @abstractmethod
    async def generate_questions(self, text: str, max_questions: int = 5) -> QuestionGeneration:
        """질문 생성"""
        pass


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT 기반 AI 제공자"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        super().__init__(api_key)
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI 패키지가 설치되지 않았습니다: pip install openai")
        
        openai.api_key = api_key
        self.model = model
        self.model_version = f"openai-{model}"
        logger.info(f"OpenAI 제공자 초기화: {self.model}")
    
    async def _call_openai(self, messages: List[Dict[str, str]], max_tokens: int = 1000) -> str:
        """OpenAI API 호출"""
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI API 호출 오류: {e}")
            raise
    
    async def analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """감정 분석"""
        messages = [
            {"role": "system", "content": "당신은 한국어 텍스트의 감정을 분석하는 전문가입니다. 긍정, 부정, 중립으로 분류하고 각각의 점수를 0-1 사이로 제공하세요."},
            {"role": "user", "content": f"다음 기사의 감정을 분석해주세요:\n\n{text}"}
        ]
        
        response = await self._call_openai(messages)
        
        # 간단한 파싱 (실제로는 더 정교한 파싱 필요)
        if "긍정" in response.lower() or "positive" in response.lower():
            sentiment = SentimentType.POSITIVE
            positive_score = 0.8
            negative_score = 0.1
            neutral_score = 0.1
        elif "부정" in response.lower() or "negative" in response.lower():
            sentiment = SentimentType.NEGATIVE
            positive_score = 0.1
            negative_score = 0.8
            neutral_score = 0.1
        else:
            sentiment = SentimentType.NEUTRAL
            positive_score = 0.3
            negative_score = 0.2
            neutral_score = 0.5
        
        return SentimentAnalysis(
            sentiment=sentiment,
            confidence=0.85,
            positive_score=positive_score,
            negative_score=negative_score,
            neutral_score=neutral_score,
            explanation=response
        )
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> KeywordExtraction:
        """키워드 추출"""
        messages = [
            {"role": "system", "content": f"당신은 텍스트에서 핵심 키워드를 추출하는 전문가입니다. 최대 {max_keywords}개의 중요한 키워드를 추출하세요."},
            {"role": "user", "content": f"다음 기사에서 핵심 키워드를 추출해주세요:\n\n{text}"}
        ]
        
        response = await self._call_openai(messages)
        
        # 키워드 추출 (간단한 파싱)
        keywords = []
        for line in response.split('\n'):
            if line.strip() and ('키워드' in line or '•' in line or '-' in line):
                keyword = re.sub(r'[•\-\d\.\s]+', '', line).strip()
                if keyword and len(keyword) > 1:
                    keywords.append(keyword)
        
        # 키워드가 없으면 기본값 사용
        if not keywords:
            keywords = ["AI", "기술", "혁신", "발전", "변화"]
        
        keyword_scores = {kw: 1.0 - (i * 0.1) for i, kw in enumerate(keywords[:max_keywords])}
        
        return KeywordExtraction(
            keywords=keywords[:max_keywords],
            keyword_scores=keyword_scores,
            explanation=response
        )
    
    async def generate_comments(self, text: str, max_comments: int = 5) -> CommentGeneration:
        """댓글 생성"""
        messages = [
            {"role": "system", "content": f"당신은 기사에 대한 자연스러운 댓글을 생성하는 전문가입니다. {max_comments}개의 다양한 스타일의 댓글을 생성하세요."},
            {"role": "user", "content": f"다음 기사에 대한 댓글을 생성해주세요:\n\n{text}"}
        ]
        
        response = await self._call_openai(messages)
        
        # 댓글 추출
        comments = []
        comment_types = []
        
        for line in response.split('\n'):
            if line.strip() and ('"' in line or '•' in line or line.startswith(('1.', '2.', '3.', '4.', '5.'))):
                comment = re.sub(r'[•\-\d\.\s"]+', '', line, count=1).strip()
                if comment and len(comment) > 10:
                    comments.append(comment)
                    comment_types.append("일반형")
        
        # 기본 댓글이 없으면 생성
        if not comments:
            comments = [
                "정말 흥미로운 내용이네요! 앞으로의 발전이 기대됩니다. 👍",
                "이런 혁신적인 기술이 우리 생활에 어떤 변화를 가져올지 궁금하네요.",
                "기사 잘 읽었습니다. 더 자세한 정보가 있으면 좋겠어요!"
            ]
            comment_types = ["긍정형", "질문형", "정보형"]
        
        return CommentGeneration(
            comments=comments[:max_comments],
            comment_types=comment_types[:max_comments],
            explanation=response
        )
    
    async def summarize_article(self, text: str) -> ArticleSummary:
        """기사 요약"""
        messages = [
            {"role": "system", "content": "당신은 기사를 간결하게 요약하는 전문가입니다. 3-5개의 핵심 포인트와 한 줄 요약을 제공하세요."},
            {"role": "user", "content": f"다음 기사를 요약해주세요:\n\n{text}"}
        ]
        
        response = await self._call_openai(messages)
        
        # 요약 포인트 추출
        summary_points = []
        one_line_summary = ""
        
        lines = response.split('\n')
        for line in lines:
            if line.strip() and ('•' in line or '-' in line or line.startswith(('1.', '2.', '3.'))):
                point = re.sub(r'[•\-\d\.\s]+', '', line, count=1).strip()
                if point:
                    summary_points.append(point)
            elif "요약" in line and len(line.strip()) > 20:
                one_line_summary = line.strip()
        
        if not summary_points:
            summary_points = [
                "새로운 기술 혁신이 주목받고 있음",
                "향후 산업 전반에 긍정적 영향 예상",
                "지속적인 연구 개발이 필요한 상황"
            ]
        
        if not one_line_summary:
            one_line_summary = "기술 혁신을 통한 미래 변화에 대한 전망을 다룬 기사"
        
        return ArticleSummary(
            summary_points=summary_points,
            one_line_summary=one_line_summary,
            explanation=response
        )
    
    async def generate_questions(self, text: str, max_questions: int = 5) -> QuestionGeneration:
        """질문 생성"""
        messages = [
            {"role": "system", "content": f"당신은 기사를 읽고 관련 질문을 생성하는 전문가입니다. {max_questions}개의 다양한 유형의 질문을 생성하세요."},
            {"role": "user", "content": f"다음 기사에 대한 질문을 생성해주세요:\n\n{text}"}
        ]
        
        response = await self._call_openai(messages)
        
        # 질문 추출
        questions = []
        question_types = []
        
        for line in response.split('\n'):
            if line.strip() and ('?' in line or '？' in line):
                question = line.strip()
                if len(question) > 10:
                    questions.append(question)
                    if "언제" in question or "시기" in question:
                        question_types.append("시기형")
                    elif "어떻게" in question or "방법" in question:
                        question_types.append("방법형")
                    elif "왜" in question or "이유" in question:
                        question_types.append("이유형")
                    else:
                        question_types.append("일반형")
        
        # 기본 질문이 없으면 생성
        if not questions:
            questions = [
                "이 기술의 상용화 시기는 언제쯤 예상되나요?",
                "기존 기술과 비교했을 때 어떤 장점이 있나요?",
                "도입 시 예상되는 비용은 어느 정도인가요?",
                "보안이나 안전성 측면에서는 어떤가요?",
                "일반 사용자도 쉽게 접근할 수 있을까요?"
            ]
            question_types = ["시기형", "비교형", "비용형", "안전형", "접근성형"]
        
        return QuestionGeneration(
            questions=questions[:max_questions],
            question_types=question_types[:max_questions],
            explanation=response
        )


class MockAIProvider(BaseAIProvider):
    """테스트용 모의 AI 제공자"""
    
    def __init__(self):
        super().__init__()
        self.model_version = "mock-ai-v1.0"
        logger.info("모의 AI 제공자 초기화")
    
    async def analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """모의 감정 분석"""
        await asyncio.sleep(0.5)  # 실제 API 호출 시뮬레이션
        
        # 간단한 키워드 기반 감정 분석
        positive_words = ["좋", "훌륭", "혁신", "발전", "성공", "희망", "긍정"]
        negative_words = ["나쁘", "문제", "위험", "실패", "우려", "부정"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = SentimentType.POSITIVE
            positive_score = 0.7 + (positive_count * 0.05)
            negative_score = 0.1
            neutral_score = 1.0 - positive_score - negative_score
        elif negative_count > positive_count:
            sentiment = SentimentType.NEGATIVE
            negative_score = 0.7 + (negative_count * 0.05)
            positive_score = 0.1
            neutral_score = 1.0 - positive_score - negative_score
        else:
            sentiment = SentimentType.NEUTRAL
            positive_score = 0.3
            negative_score = 0.2
            neutral_score = 0.5
        
        return SentimentAnalysis(
            sentiment=sentiment,
            confidence=0.85,
            positive_score=min(positive_score, 1.0),
            negative_score=min(negative_score, 1.0),
            neutral_score=max(neutral_score, 0.0),
            explanation=f"키워드 기반 분석: 긍정 키워드 {positive_count}개, 부정 키워드 {negative_count}개 발견"
        )
    
    async def extract_keywords(self, text: str, max_keywords: int = 10) -> KeywordExtraction:
        """모의 키워드 추출"""
        await asyncio.sleep(0.3)
        
        # 간단한 키워드 추출 (실제로는 TF-IDF나 다른 알고리즘 사용)
        common_words = {"이", "가", "을", "를", "의", "에", "는", "은", "과", "와", "로", "으로", "에서", "하고", "있다", "있는", "것", "수", "등"}
        
        words = re.findall(r'[가-힣A-Za-z]+', text)
        word_freq = {}
        
        for word in words:
            if len(word) > 1 and word not in common_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 빈도순 정렬
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        # 점수 계산
        max_freq = max(word_freq.values()) if word_freq else 1
        keyword_scores = {word: freq / max_freq for word, freq in sorted_words[:max_keywords]}
        
        return KeywordExtraction(
            keywords=keywords,
            keyword_scores=keyword_scores,
            explanation=f"빈도 기반 키워드 추출: 총 {len(word_freq)}개 단어 중 상위 {len(keywords)}개 선별"
        )
    
    async def generate_comments(self, text: str, max_comments: int = 5) -> CommentGeneration:
        """모의 댓글 생성"""
        await asyncio.sleep(0.7)
        
        # 템플릿 기반 댓글 생성
        templates = [
            "정말 흥미로운 내용이네요! 앞으로의 발전이 기대됩니다. 👍",
            "이런 혁신적인 기술이 우리 생활에 어떤 변화를 가져올지 궁금하네요.",
            "기사 잘 읽었습니다. 더 자세한 정보가 있으면 좋겠어요! 📚",
            "전문가들의 의견도 함께 들어보고 싶습니다.",
            "실제 적용 사례가 있다면 소개해주세요!",
            "이 분야에 대해 더 공부해보고 싶어졌어요.",
            "정부 정책은 어떻게 될까요?",
            "다른 나라의 상황은 어떤지도 궁금합니다."
        ]
        
        import random
        selected_comments = random.sample(templates, min(max_comments, len(templates)))
        comment_types = ["긍정형", "질문형", "정보형", "의견형", "요청형"][:len(selected_comments)]
        
        return CommentGeneration(
            comments=selected_comments,
            comment_types=comment_types,
            explanation="템플릿 기반 댓글 생성으로 다양한 스타일의 댓글을 제공"
        )
    
    async def summarize_article(self, text: str) -> ArticleSummary:
        """모의 기사 요약"""
        await asyncio.sleep(0.4)
        
        # 간단한 문장 기반 요약
        sentences = re.split(r'[.!?]\s+', text)
        important_sentences = [s.strip() for s in sentences if len(s.strip()) > 20][:3]
        
        summary_points = [f"• {sentence}" for sentence in important_sentences]
        one_line_summary = important_sentences[0] if important_sentences else "기사 내용에 대한 요약"
        
        return ArticleSummary(
            summary_points=summary_points,
            one_line_summary=one_line_summary,
            explanation="문장 길이 기반 중요 문장 추출을 통한 요약"
        )
    
    async def generate_questions(self, text: str, max_questions: int = 5) -> QuestionGeneration:
        """모의 질문 생성"""
        await asyncio.sleep(0.6)
        
        # 템플릿 기반 질문 생성
        question_templates = [
            "이 기술의 상용화 시기는 언제쯤 예상되나요?",
            "기존 기술과 비교했을 때 어떤 장점이 있나요?",
            "도입 시 예상되는 비용은 어느 정도인가요?",
            "보안이나 안전성 측면에서는 어떤가요?",
            "일반 사용자도 쉽게 접근할 수 있을까요?",
            "이 분야의 미래 전망은 어떻게 보시나요?",
            "관련 규제나 법적 이슈는 없나요?",
            "해외 동향은 어떤 상황인가요?"
        ]
        
        import random
        selected_questions = random.sample(question_templates, min(max_questions, len(question_templates)))
        question_types = ["시기형", "비교형", "비용형", "안전형", "접근성형"][:len(selected_questions)]
        
        return QuestionGeneration(
            questions=selected_questions,
            question_types=question_types,
            explanation="템플릿 기반 질문 생성으로 다양한 관점의 질문을 제공"
        )


class AIReactionService:
    """AI 리액션 분석 서비스 메인 클래스"""
    
    def __init__(self, provider: BaseAIProvider):
        self.provider = provider
        logger.info(f"AI 리액션 서비스 초기화: {provider.model_version}")
    
    async def analyze_article(self, request: ArticleAnalysisRequest) -> ReactionAnalysisResult:
        """기사 전체 분석"""
        start_time = time.time()
        
        try:
            result = ReactionAnalysisResult(
                analysis_timestamp=datetime.now().isoformat(),
                processing_time=0.0,
                model_version=self.provider.model_version,
                success=True
            )
            
            # 각 분석 타입별 처리
            tasks = []
            
            if ReactionType.SENTIMENT in request.analysis_types:
                tasks.append(self._analyze_sentiment(request.article_text))
            
            if ReactionType.KEYWORDS in request.analysis_types:
                tasks.append(self._extract_keywords(request.article_text, request.max_keywords))
            
            if ReactionType.COMMENTS in request.analysis_types:
                tasks.append(self._generate_comments(request.article_text, request.max_comments))
            
            if ReactionType.SUMMARY in request.analysis_types:
                tasks.append(self._summarize_article(request.article_text))
            
            if ReactionType.QUESTIONS in request.analysis_types:
                tasks.append(self._generate_questions(request.article_text, request.max_questions))
            
            # 병렬 처리
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 할당
            task_index = 0
            if ReactionType.SENTIMENT in request.analysis_types:
                if not isinstance(results[task_index], Exception):
                    result.sentiment_analysis = results[task_index]
                task_index += 1
            
            if ReactionType.KEYWORDS in request.analysis_types:
                if not isinstance(results[task_index], Exception):
                    result.keyword_extraction = results[task_index]
                task_index += 1
            
            if ReactionType.COMMENTS in request.analysis_types:
                if not isinstance(results[task_index], Exception):
                    result.comment_generation = results[task_index]
                task_index += 1
            
            if ReactionType.SUMMARY in request.analysis_types:
                if not isinstance(results[task_index], Exception):
                    result.article_summary = results[task_index]
                task_index += 1
            
            if ReactionType.QUESTIONS in request.analysis_types:
                if not isinstance(results[task_index], Exception):
                    result.question_generation = results[task_index]
                task_index += 1
            
            result.processing_time = time.time() - start_time
            return result
            
        except Exception as e:
            logger.error(f"기사 분석 중 오류: {e}")
            return ReactionAnalysisResult(
                analysis_timestamp=datetime.now().isoformat(),
                processing_time=time.time() - start_time,
                model_version=self.provider.model_version,
                success=False,
                error_message=str(e)
            )
    
    async def _analyze_sentiment(self, text: str) -> SentimentAnalysis:
        """감정 분석 래퍼"""
        return await self.provider.analyze_sentiment(text)
    
    async def _extract_keywords(self, text: str, max_keywords: int) -> KeywordExtraction:
        """키워드 추출 래퍼"""
        return await self.provider.extract_keywords(text, max_keywords)
    
    async def _generate_comments(self, text: str, max_comments: int) -> CommentGeneration:
        """댓글 생성 래퍼"""
        return await self.provider.generate_comments(text, max_comments)
    
    async def _summarize_article(self, text: str) -> ArticleSummary:
        """기사 요약 래퍼"""
        return await self.provider.summarize_article(text)
    
    async def _generate_questions(self, text: str, max_questions: int) -> QuestionGeneration:
        """질문 생성 래퍼"""
        return await self.provider.generate_questions(text, max_questions)
    
    def convert_to_simple_format(self, result: ReactionAnalysisResult) -> SimplifiedResponse:
        """프론트엔드용 간소화된 형식으로 변환"""
        reactions = []
        
        if result.sentiment_analysis:
            sentiment_text = f"{result.sentiment_analysis.sentiment.value} ({result.sentiment_analysis.confidence*100:.0f}%)"
            reactions.append(SimpleReaction(
                type="감정 분석",
                icon="😊" if result.sentiment_analysis.sentiment == SentimentType.POSITIVE else 
                     "😔" if result.sentiment_analysis.sentiment == SentimentType.NEGATIVE else "😐",
                result=sentiment_text,
                details=[result.sentiment_analysis.explanation]
            ))
        
        if result.keyword_extraction:
            reactions.append(SimpleReaction(
                type="키워드 추출",
                icon="🔍",
                result=f"{len(result.keyword_extraction.keywords)}개 키워드",
                details=result.keyword_extraction.keywords
            ))
        
        if result.comment_generation:
            reactions.append(SimpleReaction(
                type="댓글 제안",
                icon="💬",
                result=f"{len(result.comment_generation.comments)}개 댓글",
                details=result.comment_generation.comments
            ))
        
        if result.article_summary:
            reactions.append(SimpleReaction(
                type="요약",
                icon="📝",
                result="핵심 요약",
                details=[result.article_summary.one_line_summary] + result.article_summary.summary_points
            ))
        
        if result.question_generation:
            reactions.append(SimpleReaction(
                type="관련 질문",
                icon="❓",
                result=f"{len(result.question_generation.questions)}개 질문",
                details=result.question_generation.questions
            ))
        
        return SimplifiedResponse(
            success=result.success,
            reactions=reactions,
            processing_time=result.processing_time,
            message="AI 분석이 완료되었습니다." if result.success else f"분석 실패: {result.error_message}"
        )


# 서비스 인스턴스 생성 함수들
def create_mock_service() -> AIReactionService:
    """모의 AI 서비스 생성"""
    provider = MockAIProvider()
    return AIReactionService(provider)


def create_openai_service(api_key: str, model: str = "gpt-3.5-turbo") -> AIReactionService:
    """OpenAI 기반 AI 서비스 생성"""
    if not OPENAI_AVAILABLE:
        raise ImportError("OpenAI 패키지가 필요합니다: pip install openai")
    
    provider = OpenAIProvider(api_key, model)
    return AIReactionService(provider)


# 전역 서비스 인스턴스 (싱글톤 패턴)
_ai_service: Optional[AIReactionService] = None


def get_ai_service() -> AIReactionService:
    """AI 서비스 인스턴스 반환 (싱글톤)"""
    global _ai_service
    if _ai_service is None:
        # 기본적으로 모의 서비스 사용
        _ai_service = create_mock_service()
        logger.info("기본 모의 AI 서비스 생성됨")
    return _ai_service


def set_ai_service(service: AIReactionService):
    """AI 서비스 인스턴스 설정"""
    global _ai_service
    _ai_service = service
    logger.info(f"AI 서비스 설정됨: {service.provider.model_version}")


if __name__ == "__main__":
    # 서비스 테스트
    async def test_service():
        print("🤖 AI 리액션 서비스 테스트")
        
        service = create_mock_service()
        
        request = ArticleAnalysisRequest(
            article_text="""
            AI 기술의 발전이 가속화되고 있다. 
            최근 ChatGPT와 같은 대화형 AI의 등장으로 
            많은 사람들이 AI 기술에 관심을 갖게 되었다.
            """,
            analysis_types=[ReactionType.SENTIMENT, ReactionType.KEYWORDS, ReactionType.COMMENTS]
        )
        
        result = await service.analyze_article(request)
        print(f"✅ 분석 완료: {result.success}")
        print(f"⏱️ 처리 시간: {result.processing_time:.2f}초")
        
        if result.sentiment_analysis:
            print(f"😊 감정: {result.sentiment_analysis.sentiment}")
        
        if result.keyword_extraction:
            print(f"🔍 키워드: {result.keyword_extraction.keywords}")
        
        # 간소화된 형식으로 변환
        simple_result = service.convert_to_simple_format(result)
        print(f"📱 간소화된 결과: {len(simple_result.reactions)}개 리액션")
    
    # 비동기 테스트 실행
    import asyncio
    asyncio.run(test_service())
