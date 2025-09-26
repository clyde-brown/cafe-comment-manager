#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chrome Selenium 자동화 스크립트
시크릿 모드로 크롬 브라우저를 열고 구글에 접속합니다.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time


def open_chrome_incognito():
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

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        print("ChromeDriver가 설치되어 있는지 확인해주세요.")
        print("설치 방법:")
        print("1. Homebrew 사용: brew install chromedriver")
        print("2. 또는 https://chromedriver.chromium.org/ 에서 다운로드")


if __name__ == "__main__":
    print("=== Chrome Selenium 자동화 시작 ===")
    open_chrome_incognito()
    print("=== 프로그램 종료 ===")
