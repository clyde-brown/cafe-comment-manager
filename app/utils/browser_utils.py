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

# 상수 정의
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 자동화 우회 JavaScript
AUTOMATION_BYPASS_SCRIPT = """
    // navigator.webdriver 완전 제거
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
    });
    
    // chrome 객체 숨기기
    delete window.chrome;
    
    // plugins 배열을 실제처럼 만들기
    Object.defineProperty(navigator, 'plugins', {
        get: () => [1, 2, 3, 4, 5],
    });
    
    // languages 설정
    Object.defineProperty(navigator, 'languages', {
        get: () => ['ko-KR', 'ko', 'en-US', 'en'],
    });
    
    // permissions 쿼리 결과 조작
    const originalQuery = window.navigator.permissions.query;
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
    
    // 자동화 관련 속성들 제거
    delete navigator.__proto__.webdriver;
    delete navigator.webdriver;
    
    // 기타 자동화 감지 우회
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {}
    };
    
    // 콘솔 로그 숨기기
    console.clear();
"""


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

    # User-Agent 설정
    chrome_options.add_argument(f"--user-agent={DEFAULT_USER_AGENT}")

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
    자동화 탐지 우회를 위한 JavaScript 주입

    Args:
        driver: Chrome WebDriver 인스턴스
    """
    try:
        driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": AUTOMATION_BYPASS_SCRIPT},
        )
        logger.info("자동화 탐지 우회 스크립트 주입 완료")
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
