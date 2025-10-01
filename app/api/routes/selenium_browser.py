#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selenium 브라우저 제어 API 라우터
"""

import asyncio
import subprocess
from fastapi import APIRouter, HTTPException

from app.services.browser_service import BrowserService

router = APIRouter(prefix="/browser", tags=["Browser"])

@router.post("/naver-login")
async def naver_auto_login():
    """
    시크릿 모드로 네이버에 자동 로그인하는 API

    Returns:
        JSON: 로그인 실행 결과와 상태 정보
    """
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, BrowserService.login_to_naver)

        return {
            "status": "success" if result["success"] else "error",
            "message": result["message"],
            "details": result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"네이버 로그인 실행 중 오류가 발생했습니다: {str(e)}",
        )


@router.get("/status")
async def browser_status():
    """
    브라우저 상태 및 Chrome 드라이버 정보를 확인하는 API

    Returns:
        JSON: 브라우저 상태 정보
    """
    try:
        result = subprocess.run(
            ["which", "chromedriver"], capture_output=True, text=True
        )
        chromedriver_path = result.stdout.strip() if result.returncode == 0 else None

        return {
            "status": "ready",
            "chromedriver_installed": chromedriver_path is not None,
            "chromedriver_path": chromedriver_path,
            "selenium_available": True,
            "supported_actions": [
                "사용자 지정 URL 브라우저 열기",
                "네이버 자동 로그인",
                "자동화 탐지 방지 설정",
                "스크린샷 자동 촬영",
            ],
        }

    except ImportError:
        return {
            "status": "error",
            "message": "Selenium이 설치되지 않았습니다.",
            "selenium_available": False,
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"상태 확인 중 오류가 발생했습니다: {str(e)}",
            "error": str(e),
        }
