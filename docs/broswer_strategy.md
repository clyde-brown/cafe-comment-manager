
## User Agent 설정 가이드라인

### 요구사항

* 현재 PC가 Windows냐 Mac이냐에 따라 설정이 자동으로 달라져야함
* 현재 OS에 맞지 않게 User-Agent를 할 필요는 없다. OS 버젼, 최신 버젼들로 크롬 버젼 변화가 필요하다.
* 브라우저 변경은 실제 브라우저를 다양화 할때 필요

### **필수 준수 사항 : 1.HTTP/네트워크 레벨**

* **Accept-Language 헤더 vs navigator.languages** 가 일치해야함.
  * 요청 헤더의 로캘(예: `Accept-Language: ko-KR`)과 브라우저 JS가 보고하는 `navigator.languages`가 일치하지 않으면 안됌.
* ~~**TLS/JA3 fingerprint** : 브라우저가 만드는 TLS ClientHello의 암호스위트/확장 정보는 브라우저 구현마다 특징이 있다. 단순 UA 변경으론 TLS 지문이 바뀌지 않아 불일치가 드러남.~~
* ~~**HTTP 버전/세션 특성** : HTTP/2 사용 유무, 전송 옵션, TCP/IP 패킷 특성(타임스탬프, TTL 간접 신호) 등.~~

### **필수 준수 사항 : 2. 브라우저(JS) 레벨**

* **navigator.userAgent 와 서버에 보낸 UA가 일치** : 서버는 요청 헤더에 UA를 받고, 브라우저에서 `navigator.userAgent`를 읽어 비교할 수 있기 때문에 같아야함.
* **navigator.platform / devicePixelRatio / screen size / touch support** : User-Agent가 Mac을 주장하는데 DPR·해상도·platform이 Windows형이면 안됌.
* ~~**WebGL / canvas fingerprint** : `UNMASKED_RENDERER_WEBGL`, 캔버스 toDataURL 해시 등으로 하드웨어/드라이버 특성 확인 — UA와 논리적으로 맞지 않으면 의심.~~
* **폰트 목록 / 플러그인 / codec 지원** : 특정 OS/브라우저 조합에서 기대되는 폰트·코덱이 존재해야함.
* **Client Hints** : `Sec-CH-UA`, `Sec-CH-UA-Platform` 같은 최신 Client Hints 헤더와 JS의 값 비교할 수 있으니 필요 시 있어야함
* **navigator.webdriver / 자동화 흔적** : 자동화 툴이 남기는 흔적(이전 답변의 toString/descriptor 검사 등)과 교차검증을 최대한 피할 수 있어야함.
  * `Function.prototype.toString` 검사와 `Object.getOwnPropertyDescriptor` 검사를 적당히 회피할 수 있으면 좋음.

### 우선 준수 사항

* 서버에 보낸 UA 헤더와 클라이언트 `navigator.userAgent`가 다르지 않아야함.
* UA가 특정 OS/브라우저를 주장하는데 WebGL 렌더러·폰트·플러그인·클라이언트힌트 등 다른 신호가 이를 뒷받침하지 않을 때를 대비하여, OS는 현재 PC에 따라서 User-Agent를 설정해야함.
* TLS 지문(또는 네트워크 특성)이 특정 브라우저/버전과 상충하지 않아야함.
* headless 관련 플래그가 없어야하고, 자동화 흔적(특정 JS 패치 흔적)이 최대한 존재하지 않아야함.
