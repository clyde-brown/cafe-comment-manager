// 메인 JavaScript 파일

document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Cafe Comment Manager 로드 완료!');
    
    // 페이지 로드 애니메이션
    initializeAnimations();
    
    // 기능 카드 인터랙션
    initializeFeatureCards();
    
    // API 링크 클릭 추적
    initializeApiLinks();
    
    // 키보드 단축키
    initializeKeyboardShortcuts();
});

function initializeAnimations() {
    // 스크롤 시 요소들이 나타나는 애니메이션
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // 애니메이션 대상 요소들 관찰
    document.querySelectorAll('.feature-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(card);
    });
}

function initializeFeatureCards() {
    const featureCards = document.querySelectorAll('.feature-card');
    
    featureCards.forEach(card => {
        // 마우스 호버 효과 강화
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
        
        // 클릭 시 펄스 효과
        card.addEventListener('click', function() {
            this.style.animation = 'pulse 0.3s ease';
            setTimeout(() => {
                this.style.animation = '';
            }, 300);
        });
    });
}

function initializeApiLinks() {
    const apiLinks = document.querySelectorAll('.api-link');
    
    apiLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // 외부 링크가 아닌 경우에만 로딩 효과 적용
            if (!this.href.startsWith('http://') && !this.href.startsWith('https://')) {
                showLoadingEffect(this);
            }
            
            // 클릭 이벤트 로깅
            console.log(`🔗 API 링크 클릭: ${this.href}`);
            
            // Google Analytics 또는 다른 추적 도구가 있다면 여기에 추가
            trackLinkClick(this.href, this.textContent);
        });
        
        // 링크 호버 시 미리보기 정보 표시 (향후 확장 가능)
        link.addEventListener('mouseenter', function() {
            showLinkPreview(this);
        });
        
        link.addEventListener('mouseleave', function() {
            hideLinkPreview();
        });
    });
}

function showLoadingEffect(element) {
    const originalText = element.textContent;
    element.textContent = '로딩중...';
    element.style.opacity = '0.7';
    
    setTimeout(() => {
        element.textContent = originalText;
        element.style.opacity = '1';
    }, 1000);
}

function trackLinkClick(url, linkText) {
    // 실제 환경에서는 Google Analytics, Mixpanel 등 사용
    const clickData = {
        url: url,
        text: linkText,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent
    };
    
    // 로컬 스토리지에 클릭 데이터 저장 (개발용)
    const existingData = JSON.parse(localStorage.getItem('linkClicks') || '[]');
    existingData.push(clickData);
    localStorage.setItem('linkClicks', JSON.stringify(existingData));
}

function showLinkPreview(linkElement) {
    // 향후 API 문서 미리보기나 툴팁 기능 추가 가능
    const href = linkElement.href;
    if (href.includes('/docs')) {
        linkElement.title = 'FastAPI 자동 생성 API 문서를 확인하세요';
    } else if (href.includes('/api/info')) {
        linkElement.title = '시스템 정보와 사용 가능한 기능을 확인하세요';
    }
}

function hideLinkPreview() {
    // 미리보기 숨기기 (향후 구현)
}

function initializeKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K: API 문서로 바로가기
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            window.open('/docs', '_blank');
            console.log('⌨️ 키보드 단축키: API 문서 열기');
        }
        
        // Ctrl/Cmd + I: 시스템 정보로 바로가기
        if ((e.ctrlKey || e.metaKey) && e.key === 'i') {
            e.preventDefault();
            window.open('/api/info', '_blank');
            console.log('⌨️ 키보드 단축키: 시스템 정보 열기');
        }
        
        // 개발자를 위한 이스터 에그
        if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
            console.log(`
🎉 개발자 모드 환영합니다!

사용 가능한 기능:
- localStorage에서 'linkClicks' 확인으로 클릭 데이터 조회
- Ctrl/Cmd + K: API 문서 열기
- Ctrl/Cmd + I: 시스템 정보 열기

FastAPI + Selenium 환경이 준비되어 있습니다!
            `);
        }
    });
}

// 페이지 성능 모니터링
window.addEventListener('load', function() {
    const loadTime = performance.now();
    console.log(`⚡ 페이지 로드 시간: ${Math.round(loadTime)}ms`);
    
    // 성능 데이터 수집 (실제 환경에서는 모니터링 서비스로 전송)
    const performanceData = {
        loadTime: loadTime,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent,
        viewport: `${window.innerWidth}x${window.innerHeight}`
    };
    
    localStorage.setItem('lastPageLoad', JSON.stringify(performanceData));
});

// CSS 애니메이션 지원을 위한 펄스 효과 정의
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(style);

// 전역 유틸리티 함수들
window.CafeCommentManager = {
    // API 호출 헬퍼
    async callAPI(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            return await response.json();
        } catch (error) {
            console.error('API 호출 오류:', error);
            throw error;
        }
    },
    
    // 시스템 정보 가져오기
    async getSystemInfo() {
        return await this.callAPI('/api/info');
    },
    
    // 클릭 통계 조회
    getClickStats() {
        return JSON.parse(localStorage.getItem('linkClicks') || '[]');
    },
    
    // 성능 데이터 조회
    getPerformanceData() {
        return JSON.parse(localStorage.getItem('lastPageLoad') || '{}');
    }
};
