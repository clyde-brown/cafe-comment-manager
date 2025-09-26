#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
메인 페이지 및 기본 API 라우터
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.core.config import settings

templates = Jinja2Templates(directory="app/templates")

router = APIRouter(tags=["Main"])


@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """메인 페이지 - 간단한 Hello 메시지"""
    context = {"request": request, "title": "Hello Page"}
    return templates.TemplateResponse("index.html", context)


@router.get("/hello")
async def hello():
    """간단한 JSON Hello 메시지"""
    return {
        "message": "Hello, World!",
        "status": "success",
        "description": "FastAPI와 Selenium이 함께 동작하는 환경입니다.",
    }


@router.get("/hello/{name}")
async def hello_name(name: str):
    """이름을 포함한 개인화된 Hello 메시지"""
    return {"message": f"Hello, {name}!", "status": "success", "name": name}


@router.get("/api/info")
async def get_info():
    """API 정보 반환"""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "description": settings.app_description,
        "features": [
            "Selenium 브라우저 자동화",
            "FastAPI 웹 서버",
            "댓글 관리 시스템",
            "엑셀 파일 처리",
        ],
        "endpoints": {
            "main": "/",
            "docs": "/docs",
            "hello": "/hello",
            "excel_upload": "/api/excel/upload",
            "excel_analyze": "/api/excel/analyze",
        },
    }
