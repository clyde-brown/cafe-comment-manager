# 배치 로그인 전략 문서

## 개요

이 문서는 네이버 카페 댓글 관리 시스템의 배치 로그인 전략과 구현 방식을 설명합니다. 배치 로그인은 여러 계정을 순차적으로 자동 로그인하는 기능으로, 캡챠 우회 및 탐지 방지를 위한 다양한 전략을 사용합니다.

## 목차

1. [배치 로그인 아키텍처](#배치-로그인-아키텍처)
2. [백그라운드 처리 전략](#백그라운드-처리-전략)
3. [계정 격리 전략](#계정-격리-전략)
4. [캡챠 방지 전략](#캡챠-방지-전략)
5. [인간적 행동 시뮬레이션](#인간적-행동-시뮬레이션)
6. [시간 지연 전략](#시간-지연-전략)
7. [에러 처리 및 상태 관리](#에러-처리-및-상태-관리)
8. [API 엔드포인트](#api-엔드포인트)

---

## 배치 로그인 아키텍처

### 전체 흐름도

```
클라이언트 요청
    ↓
POST /api/login/batch
    ↓
작업 ID 생성 및 상태 초기화
    ↓
백그라운드 작업 시작 (process_batch_login)
    ↓
각 계정별 순차 처리:
    ├─ 계정별 지연 시간 적용
    ├─ IsolatedBrowserController 생성
    ├─ 네이버 로그인 실행
    ├─ 결과 저장 및 상태 업데이트
    └─ 계정 간 간격 대기
    ↓
작업 완료 및 상태 업데이트
```

### 핵심 컴포넌트

1. **Login API Router** (`app/api/routes/login.py`)
   - 배치 로그인 요청 수신 및 백그라운드 작업 시작
   - 작업 상태 조회 및 관리

2. **BrowserService** (`app/services/browser_service.py`)
   - 실제 네이버 로그인 로직 수행
   - IsolatedBrowserController를 통한 브라우저 제어

3. **IsolatedBrowserController** (`app/services/browser_service.py`)
   - 계정별 완전히 격리된 브라우저 세션 관리
   - 임시 프로필 생성 및 정리

---

## 백그라운드 처리 전략

### FastAPI BackgroundTasks 활용

배치 로그인은 FastAPI의 `BackgroundTasks`를 사용하여 비동기로 처리됩니다. 이를 통해 클라이언트는 즉시 응답을 받고, 작업은 백그라운드에서 진행됩니다.

```95:145:app/api/routes/login.py
@router.post("/batch", response_model=BatchLoginResponse)
async def login_batch_accounts(
    request: BatchLoginRequest, background_tasks: BackgroundTasks
):
    """
    일괄 로그인 시작 (백그라운드 처리)

    Args:
        request: 일괄 로그인 요청
        background_tasks: 백그라운드 작업 관리자

    Returns:
        BatchLoginResponse: 작업 시작 정보
    """
    try:
        # 고유 작업 ID 생성
        task_id = str(uuid.uuid4())

        # 계정 ID 할당 (없는 경우)
        accounts = []
        for i, account in enumerate(request.accounts):
            if account.id is None:
                account.id = i + 1
            accounts.append(account)

        # 작업 상태 초기화
        login_tasks[task_id] = {
            "task_id": task_id,
            "total_accounts": len(accounts),
            "completed_accounts": 0,
            "success_count": 0,
            "error_count": 0,
            "in_progress": True,
            "accounts": accounts,
            "start_time": datetime.now(),
        }

        # 백그라운드에서 일괄 로그인 실행
        background_tasks.add_task(process_batch_login, task_id, accounts)

        logger.info(f"일괄 로그인 작업 시작: {task_id}, 계정 수: {len(accounts)}")

        return BatchLoginResponse(
            task_id=task_id,
            total_accounts=len(accounts),
            message=f"{len(accounts)}개 계정의 일괄 로그인을 시작합니다.",
        )

    except Exception as e:
        logger.error(f"일괄 로그인 시작 오류: {e}")
        raise HTTPException(status_code=500, detail=f"일괄 로그인 시작 실패: {str(e)}")
```

### 전역 상태 저장소

작업 상태는 메모리 내 딕셔너리(`login_tasks`)에 저장됩니다. 실제 운영 환경에서는 Redis 등의 외부 저장소를 사용하는 것을 권장합니다.

```31:32:app/api/routes/login.py
# 전역 상태 저장소 (실제 운영에서는 Redis 등 사용)
login_tasks: Dict[str, Dict] = {}
```

---

## 계정 격리 전략

### IsolatedBrowserController

각 계정은 완전히 격리된 브라우저 프로필을 사용합니다. 이를 통해 계정 간 세션 충돌을 방지하고, 네이버의 의심스러운 활동 탐지를 피합니다.

```129:231:app/services/browser_service.py
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
```

### 격리된 브라우저 프로필 생성

각 계정마다 고유한 임시 프로필 디렉토리와 User-Agent가 생성됩니다.

```336:391:app/utils/advanced_browser_utils.py
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
```

### 격리된 Chrome 옵션 설정

계정별로 독립적인 프로필 디렉토리와 디버깅 포트를 사용합니다.

```126:224:app/utils/browser_utils.py
def create_isolated_chrome_options(
    profile_data: dict,
    headless: bool = False,
    enable_images: bool = True,
) -> Options:
    """
    완전히 격리된 Chrome 옵션 생성 (계정별 독립적인 프로필)

    Args:
        profile_data: create_isolated_browser_profile()에서 생성된 프로필 데이터
        headless: 헤드리스 모드 (기본: False - 캡챠 방지)
        enable_images: 이미지 로딩 활성화 (기본: True - 캡챠 표시)

    Returns:
        Options: 격리된 Chrome 옵션 객체
    """
    chrome_options = Options()

    # 임시 프로필 디렉토리 설정 (완전한 세션 분리)
    chrome_options.add_argument(f"--user-data-dir={profile_data['temp_profile_dir']}")

    # 각 인스턴스마다 다른 디버깅 포트 사용 (충돌 방지)
    chrome_options.add_argument(
        f"--remote-debugging-port={profile_data['debugging_port']}"
    )

    # 기본 브라우저 설정
    chrome_options.add_argument("--incognito")  # 시크릿 모드
    chrome_options.add_argument("--start-maximized")  # 창 최대화
    chrome_options.add_argument("--no-first-run")  # 첫 실행 설정 건너뛰기
    chrome_options.add_argument(
        "--no-default-browser-check"
    )  # 기본 브라우저 체크 건너뛰기

    # 헤드리스 모드 설정 (기본적으로 비활성화)
    if headless:
        chrome_options.add_argument("--headless")

    # 안정성 및 보안 옵션
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-running-insecure-content")
    chrome_options.add_argument("--allow-file-access-from-files")

    # 세션 완전 분리를 위한 추가 옵션
    chrome_options.add_argument("--disable-background-timer-throttling")
    chrome_options.add_argument("--disable-renderer-backgrounding")
    chrome_options.add_argument("--disable-backgrounding-occluded-windows")
    chrome_options.add_argument("--disable-sync")
    chrome_options.add_argument("--disable-translate")

    # 불필요한 기능 비활성화
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins")
    chrome_options.add_argument("--disable-plugins-discovery")
    chrome_options.add_argument("--disable-preconnect")
    chrome_options.add_argument("--disable-prefetch")

    # 이미지 로딩 제어 (캡챠를 위해 기본적으로 활성화)
    if not enable_images:
        chrome_options.add_argument("--disable-images")

    # 자동화 탐지 방지
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-automation")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-browser-side-navigation")
    chrome_options.add_argument("--disable-features=TranslateUI")
    chrome_options.add_argument("--disable-ipc-flooding-protection")
    chrome_options.add_argument("--disable-features=VizDisplayCompositor")

    # 계정별 고유 User-Agent 설정
    chrome_options.add_argument(f"--user-agent={profile_data['user_agent']}")

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
```

---

## 캡챠 방지 전략

### 쿠키/캐시 정리 비활성화

쿠키와 캐시를 삭제하면 네이버가 "의심스러운 활동"으로 판단할 수 있으므로, 격리된 프로필을 사용하는 경우 추가 정리를 생략합니다.

```267:298:app/services/browser_service.py
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
```

### 헤드리스 모드 비활성화

캡챠 이미지를 표시하기 위해 헤드리스 모드를 비활성화하고 이미지 로딩을 활성화합니다.

```262:265:app/services/browser_service.py
            # 격리된 브라우저 컨트롤러 사용 (계정별 완전 세션 분리)
            with IsolatedBrowserController(
                account_id=username, headless=False, enable_images=True
            ) as browser:  # 캡챠를 위해 이미지 활성화, 헤드리스 비활성화
```

### 자동화 탐지 우회 스크립트

최소한의 핵심 우회 기능만 사용하여 과도한 조작을 피합니다.

```233:257:app/utils/advanced_browser_utils.py
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
```

---

## 인간적 행동 시뮬레이션

### 페이지 읽기 시뮬레이션

로그인 페이지에 접속한 후, 사람처럼 페이지를 읽는 시간을 시뮬레이션합니다.

```84:110:app/utils/human_behavior.py
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
```

### 인간적 타이핑

자연스러운 타이핑 속도와 간헐적인 오타 수정을 시뮬레이션합니다.

```46:81:app/utils/human_behavior.py
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
```

### 생각하는 시간 시뮬레이션

입력 전후에 자연스러운 망설임을 시뮬레이션합니다.

```112:122:app/utils/human_behavior.py
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
```

### 로그인 프로세스에서의 적용

```300:333:app/services/browser_service.py
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
```

---

## 시간 지연 전략

### 계정별 추가 지연

배치 로그인 시 각 계정마다 점진적으로 증가하는 지연 시간을 적용합니다. 첫 번째 계정은 3초, 두 번째는 5초, 세 번째는 7초 등으로 증가합니다.

```202:205:app/api/routes/login.py
                # 계정별 추가 지연 (캡챠 방지 - 더 긴 간격)
                await asyncio.sleep(
                    3 + (i * 2)
                )  # 첫 번째: 3초, 두 번째: 5초, 세 번째: 7초...
```

### 계정 간 간격

각 계정 로그인 완료 후 5초 대기하여 서버 부하를 방지합니다.

```230:231:app/api/routes/login.py
                # 계정 간 간격 (서버 부하 방지 - 더 긴 간격)
                await asyncio.sleep(5)
```

### 가우시안 분포를 이용한 자연스러운 대기

가우시안 분포를 사용하여 인간의 자연스러운 행동 패턴을 시뮬레이션합니다.

```22:43:app/utils/human_behavior.py
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
```

---

## 에러 처리 및 상태 관리

### 배치 로그인 처리 함수

각 계정의 로그인 결과를 추적하고 상태를 업데이트합니다.

```183:255:app/api/routes/login.py
async def process_batch_login(task_id: str, accounts: List[AccountInfo]):
    """
    백그라운드에서 일괄 로그인 처리

    Args:
        task_id: 작업 ID
        accounts: 로그인할 계정 목록
    """
    try:
        logger.info(f"일괄 로그인 처리 시작: {task_id}")

        for i, account in enumerate(accounts):
            try:
                # 상태를 '로그인 중'으로 변경
                account.status = LoginStatus.LOADING
                login_tasks[task_id]["accounts"][i] = account

                logger.info(f"계정 {account.username} 로그인 시작")

                # 계정별 추가 지연 (캡챠 방지 - 더 긴 간격)
                await asyncio.sleep(
                    3 + (i * 2)
                )  # 첫 번째: 3초, 두 번째: 5초, 세 번째: 7초...

                # 네이버 로그인 실행 (동기 함수로 직접 호출)
                result = BrowserService.login_to_naver(
                    username=account.username, password=account.password
                )

                # 결과에 따라 상태 업데이트
                if result.get("success", False):
                    account.status = LoginStatus.SUCCESS
                    account.error_message = None
                    login_tasks[task_id]["success_count"] += 1
                    logger.info(f"계정 {account.username} 로그인 성공")
                else:
                    account.status = LoginStatus.ERROR
                    account.error_message = result.get("error", "알 수 없는 오류")
                    login_tasks[task_id]["error_count"] += 1
                    logger.error(
                        f"계정 {account.username} 로그인 실패: {account.error_message}"
                    )

                account.login_time = datetime.now()
                login_tasks[task_id]["accounts"][i] = account
                login_tasks[task_id]["completed_accounts"] += 1

                # 계정 간 간격 (서버 부하 방지 - 더 긴 간격)
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"계정 {account.username} 처리 중 오류: {e}")
                account.status = LoginStatus.ERROR
                account.error_message = str(e)
                account.login_time = datetime.now()
                login_tasks[task_id]["accounts"][i] = account
                login_tasks[task_id]["error_count"] += 1
                login_tasks[task_id]["completed_accounts"] += 1

        # 작업 완료
        login_tasks[task_id]["in_progress"] = False
        login_tasks[task_id]["end_time"] = datetime.now()

        logger.info(
            f"일괄 로그인 완료: {task_id}, "
            f"성공: {login_tasks[task_id]['success_count']}, "
            f"실패: {login_tasks[task_id]['error_count']}"
        )

    except Exception as e:
        logger.error(f"일괄 로그인 처리 중 치명적 오류: {e}")
        login_tasks[task_id]["in_progress"] = False
        login_tasks[task_id]["error"] = str(e)
```

### 상태 조회 API

클라이언트는 작업 ID를 통해 실시간으로 진행 상황을 확인할 수 있습니다.

```148:180:app/api/routes/login.py
@router.get("/status/{task_id}", response_model=LoginStatusResponse)
async def get_login_status(task_id: str):
    """
    로그인 작업 상태 조회

    Args:
        task_id: 작업 ID

    Returns:
        LoginStatusResponse: 작업 상태 정보
    """
    if task_id not in login_tasks:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    task_data = login_tasks[task_id]

    # 진행률 계산
    progress_percentage = 0.0
    if task_data["total_accounts"] > 0:
        progress_percentage = (
            task_data["completed_accounts"] / task_data["total_accounts"]
        ) * 100

    return LoginStatusResponse(
        task_id=task_id,
        total_accounts=task_data["total_accounts"],
        completed_accounts=task_data["completed_accounts"],
        success_count=task_data["success_count"],
        error_count=task_data["error_count"],
        in_progress=task_data["in_progress"],
        accounts=task_data["accounts"],
        progress_percentage=round(progress_percentage, 1),
    )
```

### 로그인 상태 열거형

```python
class LoginStatus(str, Enum):
    PENDING = "pending"       # 대기 중
    LOADING = "loading"      # 로그인 진행 중
    SUCCESS = "success"      # 로그인 성공
    ERROR = "error"          # 로그인 실패
```

---

## API 엔드포인트

### 1. 배치 로그인 시작

**엔드포인트:** `POST /api/login/batch`

**요청 본문:**
```json
{
  "accounts": [
    {
      "id": 1,
      "username": "user1",
      "password": "pass1"
    },
    {
      "id": 2,
      "username": "user2",
      "password": "pass2"
    }
  ]
}
```

**응답:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_accounts": 2,
  "message": "2개 계정의 일괄 로그인을 시작합니다."
}
```

### 2. 로그인 상태 조회

**엔드포인트:** `GET /api/login/status/{task_id}`

**응답:**
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "total_accounts": 2,
  "completed_accounts": 1,
  "success_count": 1,
  "error_count": 0,
  "in_progress": true,
  "progress_percentage": 50.0,
  "accounts": [
    {
      "id": 1,
      "username": "user1",
      "status": "success",
      "login_time": "2024-01-01T12:00:00",
      "error_message": null
    },
    {
      "id": 2,
      "username": "user2",
      "status": "loading",
      "login_time": null,
      "error_message": null
    }
  ]
}
```

### 3. 작업 목록 조회

**엔드포인트:** `GET /api/login/tasks`

**응답:**
```json
{
  "tasks": [
    {
      "task_id": "550e8400-e29b-41d4-a716-446655440000",
      "total_accounts": 2,
      "completed_accounts": 1,
      "in_progress": true,
      "start_time": "2024-01-01T12:00:00"
    }
  ]
}
```

### 4. 작업 삭제

**엔드포인트:** `DELETE /api/login/task/{task_id}`

**응답:**
```json
{
  "message": "작업 550e8400-e29b-41d4-a716-446655440000가 삭제되었습니다."
}
```

---

## 주요 전략 요약

### 1. 완전한 계정 격리
- 각 계정마다 독립적인 브라우저 프로필과 임시 디렉토리 사용
- 계정별 고유 User-Agent 생성
- 서로 다른 디버깅 포트 사용

### 2. 캡챠 방지
- 쿠키/캐시 정리 생략
- 헤드리스 모드 비활성화
- 최소한의 자동화 탐지 우회 스크립트 사용

### 3. 인간적 행동 시뮬레이션
- 가우시안 분포를 이용한 자연스러운 대기 시간
- 페이지 읽기 시뮬레이션
- 인간적 타이핑 속도 및 오타 수정
- 입력 전후 망설임 시뮬레이션

### 4. 시간 지연 전략
- 계정별 점진적 증가 지연 (3초, 5초, 7초...)
- 계정 간 5초 간격 대기
- 가우시안 분포를 이용한 자연스러운 타이밍

### 5. 안정적인 에러 처리
- 각 계정의 실패가 전체 작업에 영향을 주지 않도록 처리
- 상세한 상태 추적 및 로깅
- 작업 완료 후 자동 정리

---

## 주의사항

1. **메모리 사용**: 전역 상태 저장소(`login_tasks`)는 메모리에 저장되므로, 실제 운영 환경에서는 Redis 등의 외부 저장소를 사용하는 것을 권장합니다.

2. **동시성 제한**: 너무 많은 계정을 동시에 처리하면 네이버의 탐지 시스템에 걸릴 수 있으므로, 배치 크기를 적절히 조절하세요.

3. **캡챠 처리**: 캡챠가 발생하면 현재는 30초 대기만 하므로, 수동 개입이 필요할 수 있습니다. 향후 자동 해결 기능 추가를 고려해볼 수 있습니다.

4. **리소스 정리**: 각 계정의 브라우저 프로필은 작업 완료 후 자동으로 정리되지만, 예외 상황에서 누적될 수 있으므로 주기적인 정리가 필요합니다.

---

## 향후 개선 방향

1. **Redis 기반 상태 관리**: 메모리 기반 상태 저장소를 Redis로 전환하여 서버 재시작 후에도 상태 유지
2. **병렬 처리 옵션**: 선택적으로 여러 계정을 병렬로 처리할 수 있는 옵션 추가
3. **캡챠 자동 해결**: 캡챠 이미지 인식 및 자동 해결 기능 추가
4. **재시도 로직**: 실패한 계정에 대한 자동 재시도 기능 추가
5. **통계 및 리포트**: 배치 로그인 작업에 대한 상세 통계 및 리포트 기능 추가

