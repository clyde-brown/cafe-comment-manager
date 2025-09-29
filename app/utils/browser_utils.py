#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브라우저 관련 유틸리티 함수들
"""

import logging
import time
from typing import Optional
from urllib.parse import urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 로깅 설정
logger = logging.getLogger(__name__)

# 고급 브라우저 유틸리티 임포트
from .advanced_browser_utils import create_enhanced_browser_profile

# 글로벌 브라우저 프로필 (한 번만 생성)
_browser_profile = None


def get_browser_profile():
    """브라우저 프로필 싱글톤 패턴으로 반환"""
    global _browser_profile
    if _browser_profile is None:
        _browser_profile = create_enhanced_browser_profile()
        logger.info("새로운 브라우저 프로필 생성됨")
    return _browser_profile


# 하위 호환성을 위한 상수들
DEFAULT_USER_AGENT = get_browser_profile()["user_agent"]
AUTOMATION_BYPASS_SCRIPT = get_browser_profile()["bypass_script"]


def create_chrome_options(
    headless: bool = True, enable_images: bool = False
) -> Options:
    """
    Chrome 브라우저 옵션을 생성하는 함수

    Args:
        headless: 헤드리스 모드 활성화 여부
        enable_images: 이미지 로딩 활성화 여부 (캡차 등을 위해)

    Returns:
        Options: 설정된 Chrome 옵션 객체
    """
    chrome_options = Options()

    # 기본 브라우저 설정
    chrome_options.add_argument("--incognito")  # 시크릿 모드
    chrome_options.add_argument("--start-maximized")  # 창 최대화

    if headless:
        chrome_options.add_argument("--headless")

    # 안정성 및 보안 옵션
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")

    # 불필요한 기능 비활성화
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--disable-preconnect")
    chrome_options.add_argument("--disable-prefetch")

    # 이미지 로딩 제어
    if not enable_images:
        chrome_options.add_argument("--disable-images")
        chrome_options.add_argument("--disable-javascript")

    # 자동화 탐지 방지
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-automation")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")

    # 동적 User-Agent 설정 (현재 OS 기반)
    browser_profile = get_browser_profile()
    chrome_options.add_argument(f"--user-agent={browser_profile['user_agent']}")

    # 실험적 옵션들
    chrome_options.add_experimental_option(
        "excludeSwitches", ["enable-automation", "enable-logging"]
    )
    chrome_options.add_experimental_option("useAutomationExtension", False)
    chrome_options.add_experimental_option("detach", True)

    # 브라우저 프로필 설정
    prefs = {
        "profile.default_content_setting_values.notifications": 2,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.plugins": 1,
        "profile.content_settings.plugin_whitelist.adobe-flash-player": 1,
        "profile.content_settings.exceptions.plugins.*,*.per_resource.adobe-flash-player": 1,
    }

    # 이미지 설정
    if not enable_images:
        prefs["profile.managed_default_content_settings.images"] = 2

    chrome_options.add_experimental_option("prefs", prefs)

    return chrome_options


def setup_automation_bypass(driver: webdriver.Chrome) -> None:
    """
    강화된 자동화 탐지 우회를 위한 JavaScript 주입

    Args:
        driver: Chrome WebDriver 인스턴스
    """
    try:
        browser_profile = get_browser_profile()

        # 강화된 우회 스크립트 주입
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": browser_profile["bypass_script"]},
        )

        # Client Hints 헤더 설정
        client_hints = browser_profile["client_hints"]
        for header, value in client_hints.items():
            try:
                driver.execute_cdp_cmd(
                    "Network.setUserAgentOverride",
                    {
                        "userAgent": browser_profile["user_agent"],
                        "acceptLanguage": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                        "platform": browser_profile["platform_info"]["platform"],
                    },
                )
                break  # 첫 번째 성공하면 중단
            except:
                continue

        logger.info("강화된 자동화 탐지 우회 스크립트 주입 완료")
        logger.info(f"플랫폼: {browser_profile['platform_info']['platform']}")
        logger.info(f"언어: {browser_profile['navigator_languages']}")

    except Exception as e:
        logger.warning(f"자동화 탐지 우회 스크립트 주입 실패: {e}")


def safe_quit_driver(driver: Optional[webdriver.Chrome]) -> None:
    """
    WebDriver를 안전하게 종료하는 함수

    Args:
        driver: 종료할 WebDriver 인스턴스
    """
    if driver:
        try:
            driver.quit()
            logger.info("브라우저가 정상적으로 종료되었습니다.")
        except Exception as e:
            logger.warning(f"브라우저 종료 중 오류 (무시됨): {e}")


def save_screenshot(
    driver: webdriver.Chrome, filename: str, description: str = ""
) -> None:
    """
    스크린샷을 저장하는 함수

    Args:
        driver: WebDriver 인스턴스
        filename: 저장할 파일명
        description: 스크린샷 설명 (로그용)
    """
    try:
        driver.save_screenshot(filename)
        if description:
            logger.info(f"스크린샷 저장: {filename} - {description}")
        else:
            logger.info(f"스크린샷 저장: {filename}")
    except Exception as e:
        logger.error(f"스크린샷 저장 실패: {filename} - {e}")


def validate_url(url: str) -> bool:
    """
    URL 유효성 검사

    Args:
        url: 검사할 URL

    Returns:
        bool: URL이 유효하면 True, 아니면 False
    """
    try:
        parsed_url = urlparse(url)
        return bool(parsed_url.scheme and parsed_url.netloc)
    except Exception:
        return False


def create_safe_filename(url: str) -> str:
    """
    URL을 파일명으로 사용할 수 있도록 안전한 문자열로 변환

    Args:
        url: 변환할 URL

    Returns:
        str: 파일명으로 사용 가능한 안전한 문자열
    """
    return url.replace("://", "_").replace("/", "_").replace("?", "_").replace("&", "_")
