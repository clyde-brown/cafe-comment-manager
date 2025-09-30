#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
고급 브라우저 유틸리티 - User-Agent 및 브라우저 지문 방지
"""

import platform
import random
import logging
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class UserAgentManager:
    """OS 기반 동적 User-Agent 관리 클래스"""

    def __init__(self):
        self.current_os = platform.system()
        self.os_version = platform.release()
        self.architecture = platform.machine()

        # Chrome 버전 풀 (확장된 버전 리스트 - User-Agent 로테이션용)
        self.chrome_versions = [
            "131.0.0.0",
            "130.0.0.0",
            "129.0.0.0",
            "128.0.0.0",
            "127.0.0.0",
            "126.0.0.0",
            "125.0.0.0",
            "124.0.0.0",
            "131.0.6778.85",
            "130.0.6723.117",
            "129.0.6668.100",
            "128.0.6613.137",
        ]

        # 각 OS별 세부 버전 정보
        self.os_details = self._get_os_details()

    def _get_os_details(self) -> Dict:
        """현재 OS에 맞는 세부 정보 반환"""
        if self.current_os == "Darwin":  # macOS
            return {
                "platform": "Macintosh",
                "versions": [
                    "10_15_7",  # Catalina
                    "11_7_10",  # Big Sur
                    "12_7_6",  # Monterey
                    "13_6_9",  # Ventura
                    "14_6_1",  # Sonoma
                    "15_0_1",  # Sequoia
                ],
                "webkit_version": "537.36",
            }
        elif self.current_os == "Windows":
            return {
                "platform": "Windows NT",
                "versions": [
                    "10.0; Win64; x64",
                    "10.0; WOW64",
                ],
                "webkit_version": "537.36",
            }
        elif self.current_os == "Linux":
            return {
                "platform": "X11; Linux x86_64",
                "versions": [""],
                "webkit_version": "537.36",
            }
        else:
            # 기본값으로 Windows 사용
            return {
                "platform": "Windows NT",
                "versions": ["10.0; Win64; x64"],
                "webkit_version": "537.36",
            }

    def generate_user_agent(self, randomize: bool = True) -> str:
        """
        현재 OS에 맞는 User-Agent 생성

        Args:
            randomize: 버전 정보를 랜덤화할지 여부

        Returns:
            str: 생성된 User-Agent 문자열
        """
        chrome_version = (
            random.choice(self.chrome_versions)
            if randomize
            else self.chrome_versions[0]
        )

        if self.current_os == "Darwin":  # macOS
            os_version = (
                random.choice(self.os_details["versions"])
                if randomize
                else self.os_details["versions"][-1]
            )
            return (
                f"Mozilla/5.0 ({self.os_details['platform']}; Intel Mac OS X {os_version}) "
                f"AppleWebKit/{self.os_details['webkit_version']} (KHTML, like Gecko) "
                f"Chrome/{chrome_version} Safari/{self.os_details['webkit_version']}"
            )

        elif self.current_os == "Windows":
            os_version = (
                random.choice(self.os_details["versions"])
                if randomize
                else self.os_details["versions"][0]
            )
            return (
                f"Mozilla/5.0 ({self.os_details['platform']} {os_version}) "
                f"AppleWebKit/{self.os_details['webkit_version']} (KHTML, like Gecko) "
                f"Chrome/{chrome_version} Safari/{self.os_details['webkit_version']}"
            )

        else:  # Linux or others
            return (
                f"Mozilla/5.0 ({self.os_details['platform']}) "
                f"AppleWebKit/{self.os_details['webkit_version']} (KHTML, like Gecko) "
                f"Chrome/{chrome_version} Safari/{self.os_details['webkit_version']}"
            )

    def get_navigator_languages(self) -> List[str]:
        """OS에 맞는 navigator.languages 반환"""
        if self.current_os == "Darwin":  # macOS
            return ["ko-KR", "ko", "en-US", "en"]
        elif self.current_os == "Windows":
            return ["ko-KR", "ko", "en-US", "en"]
        else:  # Linux
            return ["ko-KR", "ko", "en-US", "en"]

    def get_platform_info(self) -> Dict[str, str]:
        """플랫폼 정보 반환 (navigator.platform 용)"""
        if self.current_os == "Darwin":
            return {"platform": "MacIntel", "oscpu": "Intel Mac OS X 10_15_7"}
        elif self.current_os == "Windows":
            return {"platform": "Win32", "oscpu": "Windows NT 10.0; Win64; x64"}
        else:  # Linux
            return {"platform": "Linux x86_64", "oscpu": "Linux x86_64"}

    def get_screen_info(self) -> Dict[str, int]:
        """OS에 맞는 화면 정보 반환"""
        if self.current_os == "Darwin":  # macOS 일반적인 해상도
            resolutions = [
                {"width": 1440, "height": 900, "pixelRatio": 2},  # MacBook Air
                {"width": 1680, "height": 1050, "pixelRatio": 2},  # MacBook Pro 16"
                {"width": 1920, "height": 1080, "pixelRatio": 2},  # iMac
                {"width": 2560, "height": 1440, "pixelRatio": 2},  # 27" iMac
            ]
        elif self.current_os == "Windows":
            resolutions = [
                {"width": 1920, "height": 1080, "pixelRatio": 1},
                {"width": 1366, "height": 768, "pixelRatio": 1},
                {"width": 2560, "height": 1440, "pixelRatio": 1.25},
                {"width": 3840, "height": 2160, "pixelRatio": 1.5},
            ]
        else:  # Linux
            resolutions = [
                {"width": 1920, "height": 1080, "pixelRatio": 1},
                {"width": 1366, "height": 768, "pixelRatio": 1},
                {"width": 2560, "height": 1440, "pixelRatio": 1},
            ]

        return random.choice(resolutions)


class BrowserFingerprintManager:
    """브라우저 지문 방지 관리 클래스"""

    def __init__(self, ua_manager: UserAgentManager):
        self.ua_manager = ua_manager

    def get_enhanced_bypass_script(self) -> str:
        """강화된 자동화 탐지 우회 JavaScript - 과도한 조작 제거"""
        platform_info = self.ua_manager.get_platform_info()
        languages = self.ua_manager.get_navigator_languages()

        return f"""
        (function() {{
            'use strict';
            
            try {{
                // 1. 핵심: navigator.webdriver 제거 (가장 중요!)
                Object.defineProperty(navigator, 'webdriver', {{
                    get: () => undefined,
                    configurable: true
                }});
        
                // 2. 주요 Selenium 속성들만 제거
                ['webdriver', '__webdriver_script_fn', '__selenium_evaluate', 
                 '__webdriver_unwrapped'].forEach(prop => {{
                    delete Object.getPrototypeOf(navigator)[prop];
                    delete navigator[prop];
                }});
        
                // 3. 기본 플랫폼 정보만 설정 (너무 상세하지 않게)
                Object.defineProperty(navigator, 'platform', {{
                    get: () => '{platform_info["platform"]}',
                    configurable: true
                }});
        
                Object.defineProperty(navigator, 'languages', {{
                    get: () => {languages},
                    configurable: true
                }});
        
                // 4. 기본적인 chrome 객체만 (너무 복잡하지 않게)
                if (!window.chrome) {{
                    window.chrome = {{
                        runtime: {{}}
                    }};
                }}
        
                // 5. Selenium 관련 변수들만 제거
                delete window.document.$cdc_asdjflasutopfhvcZLmcfl_;
                delete window.$chrome_asyncScriptInfo;
                delete window.$cdc_asdjflasutopfhvcZLmcfl_;
        
                // 6. 가벼운 타이밍 지연만 (과도하지 않게)
                setTimeout(() => {{}}, Math.random() * 50);
        
            }} catch (error) {{
                // 조용히 무시 (로그도 남기지 않음)
            }}
        }})();
        """

    def get_minimal_bypass_script(self) -> str:
        """최소한의 핵심 우회 기능만 - 카페 댓글 관리용"""
        return """
        (function() {
            try {
                // 1. 가장 중요한 것만: navigator.webdriver 제거
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });
                
                // 2. 기본 Selenium 변수들만 제거
                delete window.document.$cdc_asdjflasutopfhvcZLmcfl_;
                delete window.$chrome_asyncScriptInfo;
                
                // 3. 기본 chrome 객체 (있으면 자연스럽게)
                if (!window.chrome) {
                    window.chrome = { runtime: {} };
                }
                
            } catch (e) {
                // 조용히 무시
            }
        })();
        """

    def get_client_hints_headers(self) -> Dict[str, str]:
        """Client Hints 헤더 생성"""
        platform_info = self.ua_manager.get_platform_info()
        chrome_version = self.ua_manager.chrome_versions[0]

        major_version = chrome_version.split(".")[0]

        headers = {
            "Sec-CH-UA": f'"Chromium";v="{major_version}", "Google Chrome";v="{major_version}", "Not=A?Brand";v="99"',
            "Sec-CH-UA-Mobile": "?0",
            "Sec-CH-UA-Platform": f'"{self._get_platform_name()}"',
            "Sec-CH-UA-Platform-Version": self._get_platform_version(),
        }

        return headers

    def _get_platform_name(self) -> str:
        """Client Hints용 플랫폼 이름"""
        if self.ua_manager.current_os == "Darwin":
            return "macOS"
        elif self.ua_manager.current_os == "Windows":
            return "Windows"
        else:
            return "Linux"

    def _get_platform_version(self) -> str:
        """Client Hints용 플랫폼 버전"""
        if self.ua_manager.current_os == "Darwin":
            return '"15.0.0"'  # macOS Sequoia
        elif self.ua_manager.current_os == "Windows":
            return '"10.0.0"'  # Windows 10/11
        else:
            return '"6.5.0"'  # Linux kernel version


def create_minimal_browser_profile() -> Dict:
    """최소한의 브라우저 프로필 생성 - 카페 댓글 관리용"""
    ua_manager = UserAgentManager()
    fingerprint_manager = BrowserFingerprintManager(ua_manager)

    user_agent = ua_manager.generate_user_agent(randomize=False)  # 고정된 UA 사용
    bypass_script = fingerprint_manager.get_minimal_bypass_script()  # 간단한 우회만

    logger.info(f"간단한 User-Agent: {user_agent}")
    logger.info(f"현재 OS: {ua_manager.current_os}")

    return {
        "user_agent": user_agent,
        "bypass_script": bypass_script,
        "navigator_languages": ua_manager.get_navigator_languages(),
        "platform_info": ua_manager.get_platform_info(),
    }


def create_enhanced_browser_profile() -> Dict:
    """강화된 브라우저 프로필 생성"""
    ua_manager = UserAgentManager()
    fingerprint_manager = BrowserFingerprintManager(ua_manager)

    user_agent = ua_manager.generate_user_agent(randomize=True)
    bypass_script = fingerprint_manager.get_enhanced_bypass_script()
    client_hints = fingerprint_manager.get_client_hints_headers()

    logger.info(f"생성된 User-Agent: {user_agent}")
    logger.info(f"현재 OS: {ua_manager.current_os}")
    logger.info(f"플랫폼 정보: {ua_manager.get_platform_info()}")

    return {
        "user_agent": user_agent,
        "bypass_script": bypass_script,
        "client_hints": client_hints,
        "navigator_languages": ua_manager.get_navigator_languages(),
        "platform_info": ua_manager.get_platform_info(),
        "screen_info": ua_manager.get_screen_info(),
    }


def create_isolated_browser_profile(account_id: str = None) -> Dict:
    """
    완전히 격리된 브라우저 프로필 생성 (계정별 고유)

    Args:
        account_id: 계정 ID (User-Agent 시드로 사용)

    Returns:
        Dict: 격리된 브라우저 프로필
    """
    import tempfile
    import uuid
    import hashlib

    ua_manager = UserAgentManager()
    fingerprint_manager = BrowserFingerprintManager(ua_manager)

    # 계정 ID 기반으로 일관된 User-Agent 생성 (하지만 매번 다름)
    if account_id:
        # 계정 ID를 해시하여 시드로 사용
        seed = int(hashlib.md5(account_id.encode()).hexdigest()[:8], 16)
        import random

        random.seed(seed)
        user_agent = ua_manager.generate_user_agent(randomize=True)
        random.seed()  # 시드 초기화
    else:
        user_agent = ua_manager.generate_user_agent(randomize=True)

    bypass_script = fingerprint_manager.get_minimal_bypass_script()  # 최소형 사용

    # 임시 프로필 디렉토리 생성
    temp_profile_dir = tempfile.mkdtemp(
        prefix=f"chrome_profile_{account_id or uuid.uuid4().hex[:8]}_"
    )

    # 디버깅 포트 랜덤 생성
    import random

    debugging_port = random.randint(9222, 9999)

    logger.info(
        f"격리된 프로필 생성 - 계정: {account_id}, User-Agent: {user_agent[:50]}..."
    )
    logger.info(f"임시 프로필 디렉토리: {temp_profile_dir}")

    return {
        "user_agent": user_agent,
        "bypass_script": bypass_script,
        "navigator_languages": ua_manager.get_navigator_languages(),
        "platform_info": ua_manager.get_platform_info(),
        "screen_info": ua_manager.get_screen_info(),
        "temp_profile_dir": temp_profile_dir,
        "debugging_port": debugging_port,
        "account_id": account_id or "anonymous",
    }


# 사용 예시
if __name__ == "__main__":
    print("=== 간단한 브라우저 프로필 (권장) ===")
    minimal_profile = create_minimal_browser_profile()
    for key, value in minimal_profile.items():
        if key != "bypass_script":
            print(f"{key}: {value}")

    print("\n=== 고급 브라우저 프로필 (과도할 수 있음) ===")
    enhanced_profile = create_enhanced_browser_profile()
    for key, value in enhanced_profile.items():
        if key != "bypass_script":  # 스크립트는 너무 길어서 제외
            print(f"{key}: {value}")
