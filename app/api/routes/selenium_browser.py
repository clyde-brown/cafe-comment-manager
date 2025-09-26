#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Selenium 브라우저 제어 API 라우터
"""

from fastapi import APIRouter, HTTPException
import asyncio
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

router = APIRouter(prefix="/browser", tags=["Browser"])


def run_chrome_selenium():
    """시크릿 모드로 크롬 브라우저를 열고 구글에 접속하는 함수"""

    # Chrome 옵션 설정
    chrome_options = Options()

    # 시크릿 모드 설정
    chrome_options.add_argument("--incognito")

    # 추가 유용한 옵션들
    chrome_options.add_argument("--start-maximized")  # 창 최대화
    chrome_options.add_argument(
        "--disable-blink-features=AutomationControlled"
    )  # 자동화 탐지 방지
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    try:
        # ChromeDriver 초기화 (시스템에 설치된 ChromeDriver 사용)
        driver = webdriver.Chrome(options=chrome_options)

        # User-Agent 설정으로 자동화 탐지 추가 방지
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        print("크롬 브라우저가 시크릿 모드로 실행되었습니다!")

        # 구글 홈페이지로 이동
        driver.get("https://www.google.com")
        print("구글 홈페이지에 접속했습니다!")

        # 페이지 제목 출력
        print(f"페이지 제목: {driver.title}")

        # 10초 대기 (브라우저 확인용)
        print("10초 후 브라우저가 자동으로 닫힙니다...")
        time.sleep(10)

        # 브라우저 종료
        driver.quit()
        print("브라우저가 종료되었습니다.")

        return {
            "success": True,
            "message": "브라우저가 성공적으로 실행되었습니다.",
            "page_title": driver.title if "driver" in locals() else None,
        }

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return {
            "success": False,
            "message": f"브라우저 실행 중 오류가 발생했습니다: {str(e)}",
            "error": str(e),
        }


@router.post("/open-google")
async def open_google_browser():
    """
    시크릿 모드로 크롬 브라우저를 열고 구글에 접속하는 API

    Returns:
        JSON: 실행 결과와 상태 정보
    """
    try:
        # 백그라운드에서 브라우저 실행
        def run_browser():
            return run_chrome_selenium()

        # 비동기로 브라우저 실행
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_browser)

        return {
            "status": "success" if result["success"] else "error",
            "message": "브라우저 실행이 시작되었습니다. 10초 후 자동으로 닫힙니다.",
            "details": result,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"브라우저 실행 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/status")
async def browser_status():
    """
    브라우저 상태 및 Chrome 드라이버 정보를 확인하는 API
    """
    try:
        # Chrome 드라이버 존재 여부 확인
        import subprocess

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
                "구글 브라우저 열기 (시크릿 모드)",
                "자동화 탐지 방지 설정",
                "10초 자동 종료",
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


@router.post("/open-custom")
async def open_custom_url(url: str = "https://www.google.com", duration: int = 10):
    """
    사용자 지정 URL로 브라우저를 여는 API

    Args:
        url: 접속할 URL (기본값: 구글)
        duration: 브라우저를 열어둘 시간(초, 기본값: 10초)

    Returns:
        JSON: 실행 결과
    """
    try:

        def run_custom_browser():
            chrome_options = Options()
            chrome_options.add_argument("--incognito")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option(
                "excludeSwitches", ["enable-automation"]
            )
            chrome_options.add_experimental_option("useAutomationExtension", False)

            try:
                driver = webdriver.Chrome(options=chrome_options)
                driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

                driver.get(url)
                page_title = driver.title
                print(f"사용자 지정 URL에 접속했습니다: {url}")
                print(f"페이지 제목: {page_title}")

                time.sleep(duration)
                driver.quit()

                return {
                    "success": True,
                    "url": url,
                    "page_title": page_title,
                    "duration": duration,
                }

            except Exception as e:
                return {"success": False, "error": str(e)}

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_custom_browser)

        if result["success"]:
            return {
                "status": "success",
                "message": f"{url}에 {duration}초간 접속했습니다.",
                "details": result,
            }
        else:
            raise HTTPException(
                status_code=500, detail=f"브라우저 실행 중 오류: {result['error']}"
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"사용자 지정 브라우저 실행 중 오류가 발생했습니다: {str(e)}",
        )
