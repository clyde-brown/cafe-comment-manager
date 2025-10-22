#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 라우터 통합
"""

from fastapi import APIRouter

from app.api.routes import (
    main,
    excel,
    selenium_browser,
    login,
    cafe_comment,
    keyword_expansion,
    llm_settings,
    post_analysis,
    comment_generation,
)

api_router = APIRouter()

# 라우터 등록
api_router.include_router(main.router)
api_router.include_router(excel.router, prefix="/api")
api_router.include_router(selenium_browser.router, prefix="/api")
api_router.include_router(login.router, prefix="/api")
api_router.include_router(cafe_comment.router, prefix="/api")  # 카페 댓글 생성 API
api_router.include_router(keyword_expansion.router, prefix="/api")  # 키워드 확장 API
api_router.include_router(llm_settings.router, prefix="/api")  # LLM 설정 API
api_router.include_router(post_analysis.router)  # 게시글 분석 API
api_router.include_router(
    comment_generation.router, prefix="/api/comments"
)  # 댓글 생성 API
