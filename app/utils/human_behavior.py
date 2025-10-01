#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
인간적 행동 시뮬레이션 유틸리티
네이버 캡챠 우회를 위한 자연스러운 사용자 행동 패턴 구현
"""

import time
import random
import numpy as np
import logging

# Selenium imports (조건부 - 실제 사용시에만 import)
try:
    from selenium.webdriver.common.keys import Keys
except ImportError:
    Keys = None

logger = logging.getLogger(__name__)


def gaussian_delay(
    mean: float, std: float, min_val: float = 0.5, max_val: float = 10.0
) -> float:
    """
    가우시안 분포를 따르는 자연스러운 대기시간 생성

    Args:
        mean: 평균 대기시간 (초)
        std: 표준편차 (초)
        min_val: 최소 대기시간 (초)
        max_val: 최대 대기시간 (초)

    Returns:
        float: 생성된 대기시간 (초)
    """
    delay = np.random.normal(mean, std)
    # 최소/최대값으로 클램핑
    clamped_delay = max(min_val, min(max_val, delay))
    logger.debug(
        f"⏱️ 가우시안 대기: {clamped_delay:.2f}초 (평균: {mean}, 표준편차: {std})"
    )
    return clamped_delay


def human_typing(
    element, text: str, base_delay: float = 0.15, error_rate: float = 0.05
):
    """
    사람처럼 천천히 타이핑하는 함수 (Phase 2)

    Args:
        element: Selenium WebElement (입력 필드)
        text: 입력할 텍스트
        base_delay: 기본 타이핑 간격 (초, 기본: 150ms)
        error_rate: 오타 발생률 (0.0-1.0, 기본: 5%)
    """
    logger.debug(f"- 인간적 타이핑 시작: '{text}' (길이: {len(text)})")

    for i, char in enumerate(text):
        # 글자별 랜덤 간격 (100-200ms)
        char_delay = base_delay + random.uniform(-0.05, 0.05)

        # 5% 확률로 오타 발생 (더 인간적)
        if random.random() < error_rate and i > 0 and Keys:
            # 잘못된 글자 입력
            wrong_char = random.choice("abcdefghijklmnopqrstuvwxyz")
            element.send_keys(wrong_char)
            time.sleep(char_delay)

            # 백스페이스로 수정
            element.send_keys(Keys.BACK_SPACE)
            time.sleep(char_delay * 0.5)

            logger.debug(f"🎭 오타 시뮬레이션: '{wrong_char}' → 수정")

        # 실제 글자 입력
        element.send_keys(char)
        time.sleep(char_delay)

    logger.debug(f"- 인간적 타이핑 완료: '{text}'")


def human_page_reading(driver=None, mean: float = 3.0, std: float = 1.0):
    """
    사람처럼 페이지를 읽는 시간 시뮬레이션 (Phase 1)

    Args:
        driver: WebDriver 인스턴스 (선택적, 스크롤 시뮬레이션용)
        mean: 평균 읽기 시간 (초)
        std: 표준편차 (초)
    """
    reading_time = gaussian_delay(mean, std, min_val=1.0, max_val=8.0)

    logger.debug(f"📖 페이지 읽기 시뮬레이션: {reading_time:.2f}초")

    # 선택적으로 스크롤 시뮬레이션 추가
    if driver and random.random() < 0.3:  # 30% 확률로 스크롤
        try:
            # 약간 아래로 스크롤 (페이지 확인하는 것처럼)
            driver.execute_script("window.scrollBy(0, 100);")
            time.sleep(0.5)
            # 다시 위로
            driver.execute_script("window.scrollBy(0, -100);")
            logger.debug("- 자연스러운 스크롤 시뮬레이션")
        except Exception as e:
            logger.debug(f"스크롤 시뮬레이션 건너뜀: {e}")

    time.sleep(reading_time)


def human_thinking_pause(mean: float = 1.0, std: float = 0.3):
    """
    사람이 생각하는 시간 시뮬레이션 (망설임, 고민)

    Args:
        mean: 평균 생각 시간 (초)
        std: 표준편차 (초)
    """
    thinking_time = gaussian_delay(mean, std, min_val=0.3, max_val=3.0)
    logger.debug(f"- 생각하는 시간 시뮬레이션: {thinking_time:.2f}초")
    time.sleep(thinking_time)


def human_mouse_movement(driver, element=None):
    """
    자연스러운 마우스 움직임 시뮬레이션 (선택적)

    Args:
        driver: WebDriver 인스턴스
        element: 목표 요소 (선택적)
    """
    try:
        from selenium.webdriver.common.action_chains import ActionChains

        actions = ActionChains(driver)

        if element:
            # 요소로 천천히 이동
            actions.move_to_element(element)
            actions.pause(random.uniform(0.1, 0.3))
            actions.perform()
            logger.debug("- 자연스러운 마우스 이동")
        else:
            # 랜덤 위치로 약간 이동
            actions.move_by_offset(random.randint(-50, 50), random.randint(-20, 20))
            actions.perform()
            logger.debug("- 랜덤 마우스 움직임")

    except Exception as e:
        logger.debug(f"마우스 움직임 시뮬레이션 건너뜀: {e}")


def simulate_human_focus_change(driver):
    """
    사람처럼 포커스를 변경하는 시뮬레이션
    (탭 키 사용, 클릭 등)

    Args:
        driver: WebDriver 인스턴스
    """
    try:
        # 30% 확률로 탭 키 사용
        if random.random() < 0.3 and Keys:
            active_element = driver.switch_to.active_element
            active_element.send_keys(Keys.TAB)
            time.sleep(random.uniform(0.2, 0.5))
            logger.debug("- 탭 키로 포커스 이동")

    except Exception as e:
        logger.debug(f"포커스 변경 시뮬레이션 건너뜀: {e}")


# 사용 예시 및 테스트
if __name__ == "__main__":
    print("- 인간적 행동 시뮬레이션 유틸리티 테스트")

    # 가우시안 분포 테스트
    print("\n- 가우시안 대기시간 테스트:")
    for i in range(5):
        delay = gaussian_delay(2.0, 0.5)
        print(f"  {i+1}: {delay:.2f}초")

    # 생각하는 시간 테스트
    print("\n- 생각하는 시간 테스트:")
    for i in range(3):
        print(f"  {i+1}: 생각 중...")
        human_thinking_pause(1.0, 0.3)
        print(f"     완료!")

    print("\n- 테스트 완료!")
