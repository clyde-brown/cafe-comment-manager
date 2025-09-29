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

        # Chrome 버전 풀 (2024년 기준 최신 버전들)
        self.chrome_versions = [
            "131.0.0.0",
            "130.0.0.0",
            "129.0.0.0",
            "128.0.0.0",
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
        """강화된 자동화 탐지 우회 JavaScript"""
        platform_info = self.ua_manager.get_platform_info()
        languages = self.ua_manager.get_navigator_languages()
        screen_info = self.ua_manager.get_screen_info()

        return f"""
        // 1. navigator.webdriver 완전 제거
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
            configurable: true
        }});
        
        // 모든 가능한 webdriver 속성 제거
        ['webdriver', '__webdriver_script_fn', '__webdriver_evaluate', 
         '__selenium_evaluate', '__webdriver_unwrapped', '__driver_evaluate',
         '__selenium_unwrapped', '__fxdriver_evaluate', '__fxdriver_unwrapped'].forEach(prop => {{
            delete Object.getPrototypeOf(navigator)[prop];
            delete navigator[prop];
        }});
        
        // 2. navigator.platform 설정
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{platform_info["platform"]}',
            configurable: true
        }});
        
        // 3. navigator.languages 설정
        Object.defineProperty(navigator, 'languages', {{
            get: () => {languages},
            configurable: true
        }});
        
        // 4. 실제와 유사한 플러그인 배열
        Object.defineProperty(navigator, 'plugins', {{
            get: () => {{
                const plugins = [
                    {{
                        0: {{ name: "Chrome PDF Plugin", filename: "internal-pdf-viewer", description: "Portable Document Format" }},
                        1: {{ name: "Chrome PDF Viewer", filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai", description: "" }},
                        2: {{ name: "Native Client", filename: "internal-nacl-plugin", description: "" }},
                        length: 3,
                        item: function(index) {{ return this[index] || null; }},
                        namedItem: function(name) {{ 
                            for(let i = 0; i < this.length; i++) {{
                                if(this[i] && this[i].name === name) return this[i];
                            }}
                            return null;
                        }}
                    }}
                ];
                return plugins[0];
            }},
            configurable: true
        }});
        
        // 5. screen 정보 설정
        Object.defineProperty(screen, 'width', {{
            get: () => {screen_info["width"]},
            configurable: true
        }});
        Object.defineProperty(screen, 'height', {{
            get: () => {screen_info["height"]},
            configurable: true
        }});
        Object.defineProperty(window, 'devicePixelRatio', {{
            get: () => {screen_info["pixelRatio"]},
            configurable: true
        }});
        
        // 6. permissions 쿼리 결과 조작
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: Notification.permission }}) :
                originalQuery(parameters)
        );
        
        // 7. chrome 객체 재정의
        delete window.chrome;
        window.chrome = {{
            runtime: {{
                onConnect: undefined,
                onMessage: undefined
            }},
            loadTimes: function() {{
                return {{
                    requestTime: Date.now() / 1000 - Math.random(),
                    startLoadTime: Date.now() / 1000 - Math.random(),
                    commitLoadTime: Date.now() / 1000 - Math.random(),
                    finishDocumentLoadTime: Date.now() / 1000 - Math.random(),
                    finishLoadTime: Date.now() / 1000 - Math.random(),
                    firstPaintTime: Date.now() / 1000 - Math.random(),
                    firstPaintAfterLoadTime: 0,
                    navigationType: "Other",
                    wasFetchedViaSpdy: false,
                    wasNpnNegotiated: false,
                    npnNegotiatedProtocol: "unknown",
                    wasAlternateProtocolAvailable: false,
                    connectionInfo: "http/1.1"
                }};
            }},
            csi: function() {{
                return {{
                    pageT: Date.now(),
                    startE: Date.now() - Math.random() * 1000,
                    tran: 15
                }};
            }},
            app: {{
                isInstalled: false,
                InstallState: {{
                    DISABLED: "disabled",
                    INSTALLED: "installed",
                    NOT_INSTALLED: "not_installed"
                }},
                RunningState: {{
                    CANNOT_RUN: "cannot_run",
                    READY_TO_RUN: "ready_to_run",
                    RUNNING: "running"
                }}
            }}
        }};
        
        // 8. Function.prototype.toString 보호
        const originalToString = Function.prototype.toString;
        Function.prototype.toString = function() {{
            if (this === navigator.webdriver) {{
                return 'function webdriver() {{ [native code] }}';
            }}
            return originalToString.apply(this, arguments);
        }};
        
        // 9. Object.getOwnPropertyDescriptor 보호
        const originalGetOwnPropertyDescriptor = Object.getOwnPropertyDescriptor;
        Object.getOwnPropertyDescriptor = function(obj, prop) {{
            if (prop === 'webdriver' && obj === navigator) {{
                return undefined;
            }}
            return originalGetOwnPropertyDescriptor.apply(this, arguments);
        }};
        
        // 10. 콘솔 정리
        console.clear();
        
        // 11. 추가 보호 - Selenium 관련 변수들
        delete window.document.$cdc_asdjflasutopfhvcZLmcfl_;
        delete window.$chrome_asyncScriptInfo;
        delete window.$cdc_asdjflasutopfhvcZLmcfl_;
        
        // 12. 타이밍 공격 방지
        const start = Date.now();
        while (Date.now() - start < Math.random() * 100) {{
            // 랜덤한 지연시간 추가
        }}
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


# 사용 예시
if __name__ == "__main__":
    profile = create_enhanced_browser_profile()
    print("=== 브라우저 프로필 ===")
    for key, value in profile.items():
        if key != "bypass_script":  # 스크립트는 너무 길어서 제외
            print(f"{key}: {value}")
