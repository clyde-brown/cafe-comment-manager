#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 라우터 통합
"""

from fastapi import APIRouter

from app.api.routes import main, excel, selenium_browser, login

api_router = APIRouter()

# 라우터 등록
api_router.include_router(main.router)
api_router.include_router(excel.router, prefix="/api")
api_router.include_router(selenium_browser.router, prefix="/api")
api_router.include_router(login.router, prefix="/api")
