#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
브라우저 제어 비즈니스 로직 서비스
"""

import logging
import threading
import re
import time
import random
from typing import Dict, Any, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.utils.browser_utils import (
    create_chrome_options,
    create_isolated_chrome_options,
    setup_automation_bypass,
    safe_quit_driver,
    save_screenshot,
    validate_url,
    create_safe_filename,
)
from app.utils.advanced_browser_utils import create_isolated_browser_profile
from app.utils.human_behavior import (
    gaussian_delay,
    human_typing,
    human_page_reading,
    human_thinking_pause,
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 상수 정의
DEFAULT_WAIT_TIMEOUT = 10
NAVER_LOGIN_URL = "https://nid.naver.com/nidlogin.login"


# 🎭 인간적 행동 시뮬레이션은 app.utils.human_behavior 모듈로 분리됨


class BrowserController:
    """브라우저 제어를 위한 클래스"""

    def __init__(self, headless: bool = True, enable_images: bool = False):
        self.headless = headless
        self.enable_images = enable_images
        self.driver: Optional[webdriver.Chrome] = None

    def __enter__(self):
        """컨텍스트 매니저 진입"""
        self._initialize_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        safe_quit_driver(self.driver)

    def _initialize_driver(self) -> None:
        """WebDriver 초기화"""
        options = create_chrome_options(self.headless, self.enable_images)
        self.driver = webdriver.Chrome(options=options)
        setup_automation_bypass(self.driver)
        logger.info(
            f"Chrome 브라우저 초기화 완료 (헤드리스: {self.headless}, 이미지: {self.enable_images})"
        )

    def navigate_to(self, url: str) -> str:
        """
        지정된 URL로 이동

        Args:
            url: 이동할 URL

        Returns:
            str: 페이지 제목
        """
        if not self.driver:
            raise RuntimeError("WebDriver가 초기화되지 않았습니다.")

        self.driver.get(url)
        title = self.driver.title
        logger.info(f"페이지 이동 완료: {url} (제목: {title})")
        return title

    def wait_for_element(self, by: By, value: str, timeout: int = DEFAULT_WAIT_TIMEOUT):
        """
        요소가 나타날 때까지 대기

        Args:
            by: 요소 검색 방법
            value: 요소 검색 값
            timeout: 대기 시간 (초)

        Returns:
            WebElement: 찾은 요소
        """
        if not self.driver:
            raise RuntimeError("WebDriver가 초기화되지 않았습니다.")

        wait = WebDriverWait(self.driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))

    def take_screenshot(self, filename: str, description: str = "") -> None:
        """스크린샷 촬영"""
        if self.driver:
            save_screenshot(self.driver, filename, description)

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


class IsolatedBrowserController:
    """완전히 격리된 브라우저 제어 클래스 (계정별 독립적인 세션)"""

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
                import shutil

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


class BrowserService:
    """브라우저 관련 비즈니스 로직을 처리하는 서비스 클래스"""

    @staticmethod
    def login_to_naver(
        username: str = "yki2k",
        password: str = "zmfpdlwl94@",
        # username: str = "tngus_0314", password: str = "xmslfm123!"
    ) -> Dict[str, Any]:
        """
        네이버 자동 로그인 함수

        Args:
            username: 네이버 아이디
            password: 네이버 비밀번호

        Returns:
            Dict: 로그인 결과
        """
        import re

        # 모든 제어문자와 공백 제거
        username = re.sub(r"[\r\n\t\x00-\x1f\x7f-\x9f]", "", username).strip()
        password = re.sub(r"[\r\n\t\x00-\x1f\x7f-\x9f]", "", password).strip()

        # _x000d_ 같은 특수 문자열도 제거
        password = re.sub(r"_x[0-9a-fA-F]{4}_", "", password)

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

                # try:
                #     # 쿠키만 안전하게 정리
                #     browser.driver.delete_all_cookies()
                #
                #     # localStorage와 sessionStorage는 조건부로 정리
                #     browser.driver.execute_script(
                #         """
                #         try {
                #             if (typeof(Storage) !== "undefined" && window.location.protocol !== 'data:') {
                #                 window.localStorage.clear();
                #                 window.sessionStorage.clear();
                #                 console.log('Storage cleared successfully');
                #             }
                #         } catch (e) {
                #             console.log('Storage clear skipped:', e.message);
                #         }
                #     """
                #     )
                #     logger.info("브라우저 캐시 정리 완료")
                # except Exception as e:
                #     logger.warning(f"캐시 정리 중 오류 (무시됨): {e}")

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
                try:
                    wait = WebDriverWait(browser.driver, 15)
                    wait.until(
                        lambda driver: "naver.com" in driver.current_url
                        and "nid.naver.com" not in driver.current_url
                    )
                    login_success = True
                    title = browser.get_page_title()
                    logger.info("네이버 로그인 성공!")

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
                }

        except Exception as e:
            logger.error(f"네이버 로그인 중 오류: {e}")
            return {
                "success": False,
                "message": f"네이버 로그인 중 오류가 발생했습니다: {str(e)}",
                "error": str(e),
            }
