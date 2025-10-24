#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 자동 로그인 테스트 스크립트
FastAPI 브라우저 서비스와 동일한 구현을 사용하는 독립 실행 파일
"""

import logging
import time
import random
import re
import tempfile
import shutil
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import numpy as np

# FastAPI 프로젝트의 유틸리티 모듈들 import
from app.utils.advanced_browser_utils import create_isolated_browser_profile
from app.utils.browser_utils import create_isolated_chrome_options, safe_quit_driver
from app.utils.human_behavior import (
    gaussian_delay,
    human_typing,
    human_page_reading,
    human_thinking_pause,
)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 상수 정의
DEFAULT_WAIT_TIMEOUT = 10
NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"

# 하드코딩된 계정 정보 (여기에 실제 계정 정보를 입력하세요)
USERNAME = "yki2k"  # 실제 네이버 아이디로 변경
PASSWORD = "zmfpdlwl94@"  # 실제 네이버 비밀번호로 변경


class IsolatedBrowserController:
    """완전히 격리된 브라우저 제어 클래스 (계정별 독립적인 세션) - FastAPI와 동일한 구현"""

    def __init__(
        self,
        account_id: str,
        headless: bool = False,
        enable_images: bool = True,
    ):
        self.account_id = account_id
        self.headless = headless
        self.enable_images = enable_images
        self.driver: Optional[webdriver.Chrome] = None
        self.profile_data = None

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self._initialize_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료 및 리소스 정리"""
        self._cleanup()

    def _initialize_driver(self) -> None:
        """완전히 격리된 WebDriver 초기화"""
        try:
            # 계정별 격리된 프로필 생성
            self.profile_data = create_isolated_browser_profile(self.account_id)

            # 격리된 Chrome 옵션 생성
            options = create_isolated_chrome_options(
                self.profile_data, self.headless, self.enable_images
            )

            # Chrome 드라이버 시작
            self.driver = webdriver.Chrome(options=options)

            # 자동화 탐지 우회 스크립트 주입 (최소형)
            self.driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": self.profile_data["bypass_script"]},
            )

            logger.info(f"격리된 브라우저 초기화 완료 - 계정: {self.account_id}")
            logger.info(f"User-Agent: {self.profile_data['user_agent'][:50]}...")
            logger.info(f"프로필 디렉토리: {self.profile_data['temp_profile_dir']}")

        except Exception as e:
            logger.error(f"격리된 브라우저 초기화 실패 (계정: {self.account_id}): {e}")
            self._cleanup()
            raise

    def _cleanup(self):
        """리소스 정리"""
        # 브라우저 종료
        if self.driver:
            try:
                safe_quit_driver(self.driver)
                logger.info(f"브라우저 종료 완료 - 계정: {self.account_id}")
            except Exception as e:
                logger.warning(f"브라우저 종료 중 오류 (계정: {self.account_id}): {e}")

        # 임시 프로필 디렉토리 정리
        if self.profile_data and self.profile_data.get("temp_profile_dir"):
            try:
                shutil.rmtree(self.profile_data["temp_profile_dir"], ignore_errors=True)
                logger.info(f"임시 프로필 정리 완료 - 계정: {self.account_id}")
            except Exception as e:
                logger.warning(f"프로필 정리 중 오류 (계정: {self.account_id}): {e}")

    def navigate_to(self, url: str) -> str:
        """지정된 URL로 이동"""
        if not self.driver:
            raise RuntimeError("WebDriver가 초기화되지 않았습니다.")

        self.driver.get(url)
        title = self.driver.title
        logger.info(f"페이지 이동 완료 (계정: {self.account_id}): {url}")
        return title

    def wait_for_element(self, by, value, timeout: int = 10):
        """요소가 나타날 때까지 대기"""
        if not self.driver:
            raise RuntimeError("WebDriver가 초기화되지 않았습니다.")

        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))

    def get_current_url(self) -> str:
        """현재 URL 반환"""
        if self.driver:
            return self.driver.current_url
        return ""

    def get_page_title(self) -> str:
        """현재 페이지 제목 반환"""
        if self.driver:
            return self.driver.title
        return ""


def save_login_data_to_json(login_data: Dict[str, Any], username: str) -> str:
    """
    로그인 데이터를 JSON 파일로 저장
    
    Args:
        login_data: 저장할 로그인 데이터
        username: 사용자명 (파일명에 포함)
    
    Returns:
        str: 저장된 파일 경로
    """
    # 현재 날짜시간을 로컬 포맷으로 생성 (나노초 제외)
    current_time = datetime.now()
    date_str = current_time.strftime("%Y%m%d_%H%M%S")
    
    # 파일명 생성
    filename = f"naver_login_data_{date_str}.json"
    
    # test 디렉토리에 저장
    test_dir = Path(__file__).parent
    file_path = test_dir / filename
    
    # JSON 파일로 저장
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(login_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"로그인 데이터가 저장되었습니다: {file_path}")
    return str(file_path)


def extract_login_response_data(browser) -> Dict[str, Any]:
    """
    브라우저에서 로그인 후 응답 데이터를 추출
    
    Args:
        browser: 브라우저 컨트롤러 인스턴스
    
    Returns:
        Dict: 추출된 로그인 응답 데이터
    """
    try:
        # 쿠키 정보 추출
        cookies = {}
        important_cookies = {}
        full_cookies_list = []
        
        for cookie in browser.driver.get_cookies():
            cookies[cookie['name']] = cookie['value']
            full_cookies_list.append(cookie)
            
            # 중요한 쿠키들 별도 저장
            if cookie['name'] in ['NID_AUT', 'NID_SES', 'NID_JKL', 'NACT', 'nx_ssl']:
                important_cookies[cookie['name']] = cookie['value']
        
        # User-Agent 추출
        user_agent = browser.driver.execute_script("return navigator.userAgent;")
        
        # Local Storage 추출
        local_storage = {}
        try:
            local_storage = browser.driver.execute_script("""
                var ls = {};
                for (var i = 0; i < localStorage.length; i++) {
                    var key = localStorage.key(i);
                    ls[key] = localStorage.getItem(key);
                }
                return ls;
            """)
        except Exception as e:
            logger.warning(f"Local Storage 추출 실패: {e}")
        
        # Session Storage 추출
        session_storage = {}
        try:
            session_storage = browser.driver.execute_script("""
                var ss = {};
                for (var i = 0; i < sessionStorage.length; i++) {
                    var key = sessionStorage.key(i);
                    ss[key] = sessionStorage.getItem(key);
                }
                return ss;
            """)
        except Exception as e:
            logger.warning(f"Session Storage 추출 실패: {e}")
        
        # 토큰 추출 (추가적인 인증 토큰이 있다면)
        extracted_tokens = {}
        
        return {
            "cookies": cookies,
            "important_cookies": important_cookies,
            "user_agent": user_agent,
            "local_storage": local_storage,
            "session_storage": session_storage,
            "extracted_tokens": extracted_tokens,
            "full_cookies_list": full_cookies_list
        }
        
    except Exception as e:
        logger.error(f"로그인 응답 데이터 추출 중 오류: {e}")
        return {}


def test_naver_login(username: str, password: str) -> Dict[str, Any]:
    """
    네이버 자동 로그인 테스트 함수 - FastAPI BrowserService와 동일한 구현

    Args:
        username: 네이버 아이디
        password: 네이버 비밀번호

    Returns:
        Dict: 로그인 결과
    """
    # 입력값 정리 (FastAPI와 동일)
    username = re.sub(r"[\r\n\t\x00-\x1f\x7f-\x9f]", "", username).strip()
    password = re.sub(r"[\r\n\t\x00-\x1f\x7f-\x9f]", "", password).strip()
    password = re.sub(r"_x[0-9a-fA-F]{4}_", "", password)

    logger.info("=" * 50)
    logger.info("🚀 네이버 자동 로그인 테스트 시작 (FastAPI 구현)")
    logger.info("=" * 50)

    try:
        # 격리된 브라우저 컨트롤러 사용 (계정별 완전 세션 분리)
        with IsolatedBrowserController(
            account_id=username, headless=False, enable_images=True
        ) as browser:  # 캡챠를 위해 이미지 활성화, 헤드리스 비활성화
            # 네이버 로그인 페이지로 이동 (먼저 페이지 로드)
            title = browser.navigate_to(NAVER_LOGIN_URL)

            # --- 쿠키/캐시 정리 비활성화 (캡챠 원인!) --- 자동 로그인 의심
            # 이유: 쿠키를 삭제하면 네이버가 "의심스러운 활동"으로 판단
            # IsolatedBrowserController가 이미 임시 프로필을 사용하므로
            # 추가 정리가 불필요하며, 오히려 캡챠를 유발함
            logger.info("쿠키/캐시 정리 생략 (캡챠 방지)")

            # 🎭 Phase 1: 사람처럼 페이지 읽기 (가우시안 분포)
            human_page_reading(mean=3.5, std=1.2)  # 평균 3.5초, 표준편차 1.2초

            # 로그인 폼 요소 대기
            logger.info("🔍 로그인 폼 찾는 중...")
            username_field = browser.wait_for_element(By.ID, "id")

            # 🎭 Phase 1: 아이디 입력 전 망설임
            human_thinking_pause(mean=0.8, std=0.3)

            # 🎭 Phase 2: 사람처럼 아이디 입력
            username_field.clear()
            human_typing(username_field, username)
            logger.info("✅ 아이디 입력 완료")

            # 🎭 Phase 1: 비밀번호로 이동 전 잠시 대기
            human_thinking_pause(mean=0.6, std=0.2)

            # 비밀번호 필드 찾기
            password_field = browser.driver.find_element(By.ID, "pw")
            password_field.clear()

            # 🎭 Phase 2: 사람처럼 비밀번호 입력
            human_typing(password_field, password)
            logger.info("✅ 패스워드 입력 완료")

            # 🎭 Phase 1: 로그인 버튼 클릭 전 최종 확인 시간
            human_thinking_pause(mean=1.2, std=0.4)

            # 로그인 버튼 클릭
            logger.info("🖱️ 로그인 버튼 클릭")
            login_button = browser.driver.find_element(By.ID, "log.login")
            login_button.click()
            logger.info("로그인 버튼 클릭")

            # 스크린샷 3. 로그인 버튼 클릭 후 (주석 처리)
            time.sleep(2)

            # 로그인 처리 대기 및 캡차 확인
            logger.info("로그인 처리 중... 캡차나 추가 인증 확인")
            time.sleep(5)

            # 캡차 감지
            try:
                browser.driver.find_element(
                    By.CSS_SELECTOR,
                    "img[alt*='캡차'], img[src*='captcha'], .captcha_img img",
                )
                logger.warning(
                    "⚠️  캡차 이미지가 감지되었습니다! 수동 입력이 필요할 수 있습니다."
                )
                logger.info("캡차 해결을 위해 30초 대기합니다...")
                time.sleep(30)
            except:
                logger.info("캡차가 감지되지 않았습니다.")

            # 로그인 성공 확인
            login_success = False
            login_response_data = {}
            saved_file_path = ""
            title = ""
            
            try:
                wait = WebDriverWait(browser.driver, 15)
                wait.until(
                    lambda driver: "naver.com" in driver.current_url
                    and "nid.naver.com" not in driver.current_url
                )
                login_success = True
                title = browser.get_page_title()
                logger.info("네이버 로그인 성공!")

                # 로그인 성공 시 응답 데이터 추출
                logger.info("로그인 응답 데이터 추출 중...")
                login_response_data = extract_login_response_data(browser)
                
                # JSON 파일로 저장
                saved_file_path = save_login_data_to_json(login_response_data, username)
                
                # 성공
                time.sleep(2)

            except Exception as login_error:
                logger.error(f"로그인 확인 중 오류: {login_error}")

                # 현재 상태 확인
                current_url = browser.get_current_url()
                logger.info(f"현재 URL: {current_url}")

                # 오류 메시지 확인
                try:
                    error_msg = browser.driver.find_element(
                        By.CSS_SELECTOR, ".error_msg, .alert_msg, .msg_error"
                    )
                    logger.info(f"오류 메시지: {error_msg.text}")
                except:
                    logger.info("특별한 오류 메시지는 없습니다.")

                # 실패
                time.sleep(2)

            return {
                "success": True,
                "message": (
                    "네이버 로그인이 완료되었습니다."
                    if login_success
                    else "로그인을 시도했습니다. 추가 인증이 필요할 수 있습니다."
                ),
                "login_success": login_success,
                "page_title": title,
                "current_url": browser.get_current_url(),
                "login_response_data": login_response_data,
                "saved_file_path": saved_file_path,
            }

    except Exception as e:
        logger.error(f"❌ 네이버 로그인 중 오류: {e}")
        return {
            "success": False,
            "message": f"네이버 로그인 중 오류가 발생했습니다: {str(e)}",
            "error": str(e),
        }


def main():
    """메인 실행 함수 - FastAPI 구현과 동일한 테스트"""
    print("🤖 네이버 자동 로그인 테스트 스크립트 (FastAPI 구현)")
    print("=" * 50)

    # 계정 정보 확인
    if USERNAME == "your_username_here" or PASSWORD == "your_password_here":
        print("❌ 오류: 계정 정보를 설정해주세요!")
        print("파일 상단의 USERNAME과 PASSWORD 변수를 실제 값으로 변경하세요.")
        return

    print(f"📧 테스트 계정: {USERNAME}")
    print("🔒 비밀번호: ********")
    print()

    # 자동 로그인 실행
    result = test_naver_login(USERNAME, PASSWORD)

    # 결과 출력
    print("\n📊 테스트 결과:")
    print("-" * 50)
    print(f"성공 여부: {result.get('success')}")
    print(f"로그인 성공: {result.get('login_success')}")
    print(f"메시지: {result.get('message')}")
    print(f"페이지 제목: {result.get('page_title')}")
    print(f"현재 URL: {result.get('current_url')}")
    
    # 저장된 파일 경로 출력
    saved_file_path = result.get('saved_file_path')
    if saved_file_path:
        print(f"저장된 파일: {saved_file_path}")
        print(f"로그인 응답 데이터가 JSON 파일로 저장되었습니다.")

    if result.get("login_success"):
        print("\n🎉 로그인 테스트 성공!")
        print("🔧 FastAPI 브라우저 서비스와 동일한 방식으로 작동합니다.")
        print("📁 로그인 데이터가 JSON 파일로 저장되었습니다.")
    else:
        print("\n⚠️  로그인 테스트 완료 (추가 확인 필요)")


if __name__ == "__main__":
    main()