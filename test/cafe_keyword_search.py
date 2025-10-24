#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 카페 게시글 키워드 검색 스크립트
10초 + 오차 주기로 카페 게시글을 조회하여 키워드가 포함된 게시글을 찾습니다.
"""

import logging
import time
import random
import json
import sys
import os
import requests
import argparse
from datetime import datetime
from typing import Dict, Any, List, Set
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 상수 정의
CAFE_ARTICLE_LIST_API_URL = "https://apis.naver.com/cafe-web/cafe-boardlist-api/v1/cafes/{cafe_id}/menus/{menu_id}/articles"


class CafeKeywordSearcher:
    """네이버 카페 게시글 키워드 검색 클래스"""
    
    def __init__(self, json_file_path: str):
        """
        초기화
        
        Args:
            json_file_path: 로그인 세션 데이터가 담긴 JSON 파일 경로
        """
        self.json_file_path = json_file_path
        self.session_data = self._load_session_data()
        self.session = requests.Session()
        self.found_articles = set()  # 이미 찾은 게시글 ID 저장
        
    def _load_session_data(self) -> Dict[str, Any]:
        """JSON 파일에서 세션 데이터 로드"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"세션 데이터 로드 완료: {self.json_file_path}")
            return data
        except Exception as e:
            logger.error(f"세션 데이터 로드 실패: {e}")
            raise
    
    def _setup_requests_session(self) -> None:
        """requests 세션 설정 (쿠키 및 헤더)"""
        try:
            # 쿠키 설정
            cookies_dict = self.session_data.get('cookies', {})
            for name, value in cookies_dict.items():
                self.session.cookies.set(name, value)
            
            # User-Agent 설정
            user_agent = self.session_data.get('user_agent', '')
            
            # 자동화 탐지 우회를 위한 헤더 설정
            self.session.headers.update({
                'User-Agent': user_agent,
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://cafe.naver.com',
                'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
                'Sec-Ch-Ua-Mobile': '?0',
                'Sec-Ch-Ua-Platform': '"macOS"',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site',
                'X-Cafe-Product': 'pc',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache'
            })
            
            logger.info("✅ requests 세션 설정 완료")
            
        except Exception as e:
            logger.error(f"requests 세션 설정 실패: {e}")
            raise
    
    def _prepare_referer_url(self, cafe_id: str, menu_id: str) -> str:
        """Referer URL 생성"""
        referer_url = f"https://cafe.naver.com/f-e/cafes/{cafe_id}/menus/{menu_id}?viewType=L"
        return referer_url
    
    def _simulate_human_behavior(self) -> None:
        """인간적인 행동 시뮬레이션 (대기 시간)"""
        # 랜덤한 대기 시간 (1-3초)
        wait_time = random.uniform(1.0, 3.0)
        logger.info(f"⏳ 자연스러운 대기 시간: {wait_time:.2f}초")
        time.sleep(wait_time)
    
    def search_articles(self, cafe_id: str, menu_id: str, keywords: List[str]) -> Dict[str, Any]:
        """
        카페 게시글 검색
        
        Args:
            cafe_id: 카페 ID
            menu_id: 메뉴 ID
            keywords: 검색할 키워드 리스트
        
        Returns:
            Dict: 검색 결과
        """
        try:
            logger.info("=" * 50)
            logger.info("🔍 네이버 카페 게시글 키워드 검색 시작")
            logger.info("=" * 50)
            
            # 1단계: requests 세션 설정
            self._setup_requests_session()
            
            # 2단계: Referer URL 설정
            referer_url = self._prepare_referer_url(cafe_id, menu_id)
            self.session.headers.update({
                'Referer': referer_url
            })
            logger.info(f"📍 Referer URL 설정: {referer_url}")
            
            # 3단계: 인간적인 행동 시뮬레이션
            self._simulate_human_behavior()
            
            # 4단계: API 요청 데이터 준비
            logger.info("📤 게시글 목록 API 호출 중...")
            
            # 올바른 API URL 구성
            api_url = CAFE_ARTICLE_LIST_API_URL.format(cafe_id=cafe_id, menu_id=menu_id)
            
            # GET 요청 파라미터
            params = {
                'page': 1,
                'pageSize': 15,
                'sortBy': 'TIME',
                'viewType': 'L'
            }
            
            # 5단계: API 호출 (GET 요청)
            response = self.session.get(api_url, params=params, timeout=30)
            
            logger.info(f"API 응답 상태: {response.status_code}")
            
            # 6단계: 결과 처리
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    return self._process_search_results(response_json, keywords)
                except json.JSONDecodeError:
                    logger.warning("JSON 파싱 실패")
                    return {
                        "success": False,
                        "message": "JSON 파싱 실패",
                        "matched_articles": [],
                        "total_matched": 0
                    }
            else:
                logger.error(f"API 호출 실패: {response.status_code}")
                return {
                    "success": False,
                    "message": f"API 호출 실패 (상태코드: {response.status_code})",
                    "matched_articles": [],
                    "total_matched": 0
                }
                
        except requests.exceptions.Timeout:
            logger.error("❌ API 호출 타임아웃")
            return {
                "success": False,
                "message": "API 호출 타임아웃",
                "matched_articles": [],
                "total_matched": 0
            }
        except requests.exceptions.ConnectionError:
            logger.error("❌ 네트워크 연결 오류")
            return {
                "success": False,
                "message": "네트워크 연결 오류",
                "matched_articles": [],
                "total_matched": 0
            }
        except Exception as e:
            logger.error(f"❌ 게시글 검색 중 오류: {e}")
            return {
                "success": False,
                "message": f"게시글 검색 중 오류가 발생했습니다: {str(e)}",
                "matched_articles": [],
                "total_matched": 0
            }
    
    def _process_search_results(self, response_json: Dict[str, Any], keywords: List[str]) -> Dict[str, Any]:
        """검색 결과 처리 및 키워드 매칭"""
        try:
            # 새로운 API 응답 구조에 맞게 수정
            article_list = response_json.get('result', {}).get('articleList', [])
            matched_articles = []
            new_articles = []
            
            logger.info(f"📋 총 {len(article_list)}개 게시글 조회됨")
            
            for article_data in article_list:
                if article_data.get('type') != 'ARTICLE':
                    continue
                    
                item = article_data.get('item', {})
                article_id = item.get('articleId')
                subject = item.get('subject', '')
                summary = item.get('summary', '')
                
                # 이미 찾은 게시글인지 확인
                if article_id in self.found_articles:
                    continue
                
                # 키워드 매칭 검사
                matched_keywords = []
                for keyword in keywords:
                    if keyword.lower() in subject.lower() or keyword.lower() in summary.lower():
                        matched_keywords.append(keyword)
                
                if matched_keywords:
                    matched_article = {
                        'articleId': article_id,
                        'subject': subject,
                        'summary': summary[:100] + '...' if len(summary) > 100 else summary,
                        'matched_keywords': matched_keywords,
                        'writerInfo': item.get('writerInfo', {}),
                        'commentCount': item.get('commentCount', 0),
                        'readCount': item.get('readCount', 0),
                        'writeDateTimestamp': item.get('writeDateTimestamp', 0)
                    }
                    matched_articles.append(matched_article)
                    new_articles.append(article_id)
                    self.found_articles.add(article_id)
            
            # 새로 찾은 게시글만 로그 출력
            if new_articles:
                logger.info(f"🎯 키워드 매칭 게시글 발견: {len(new_articles)}개")
                logger.info(f"📝 새로 발견된 게시글 ID: {new_articles}")
                
                for article in matched_articles:
                    logger.info(f"  - ID: {article['articleId']}")
                    logger.info(f"    제목: {article['subject']}")
                    logger.info(f"    매칭 키워드: {', '.join(article['matched_keywords'])}")
                    logger.info(f"    작성자: {article['writerInfo'].get('nickName', 'Unknown')}")
                    logger.info(f"    댓글수: {article['commentCount']}, 조회수: {article['readCount']}")
                    logger.info("    " + "-" * 40)
            else:
                logger.info("🔍 키워드 매칭 게시글 없음")
            
            return {
                "success": True,
                "message": f"검색 완료 - 새로 발견된 게시글: {len(new_articles)}개",
                "matched_articles": matched_articles,
                "total_matched": len(matched_articles),
                "new_articles": new_articles
            }
            
        except Exception as e:
            logger.error(f"검색 결과 처리 중 오류: {e}")
            return {
                "success": False,
                "message": f"검색 결과 처리 중 오류: {str(e)}",
                "matched_articles": [],
                "total_matched": 0
            }
    
    def start_periodic_search(self, cafe_id: str, menu_id: str, keywords: List[str], duration_minutes: int = 60):
        """
        주기적 검색 시작
        
        Args:
            cafe_id: 카페 ID
            menu_id: 메뉴 ID
            keywords: 검색할 키워드 리스트
            duration_minutes: 검색 지속 시간 (분)
        """
        logger.info("🚀 주기적 키워드 검색 시작")
        logger.info(f"📊 검색 설정:")
        logger.info(f"  - 카페 ID: {cafe_id}")
        logger.info(f"  - 메뉴 ID: {menu_id}")
        logger.info(f"  - 키워드: {', '.join(keywords)}")
        logger.info(f"  - 검색 주기: 10초 + 오차")
        logger.info(f"  - 지속 시간: {duration_minutes}분")
        logger.info("=" * 50)
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        search_count = 0
        
        try:
            while time.time() < end_time:
                search_count += 1
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                logger.info(f"🔍 [{search_count}회차] 검색 시작 - {current_time}")
                
                result = self.search_articles(cafe_id, menu_id, keywords)
                
                if result['success']:
                    if result['new_articles']:
                        logger.info(f"✅ 새로운 매칭 게시글 {len(result['new_articles'])}개 발견!")
                    else:
                        logger.info("ℹ️ 새로운 매칭 게시글 없음")
                else:
                    logger.error(f"❌ 검색 실패: {result['message']}")
                
                # 다음 검색까지 대기 (10초 + 오차)
                if time.time() < end_time:
                    wait_time = 10 + random.uniform(-2, 2)  # 8-12초 사이
                    logger.info(f"⏳ 다음 검색까지 {wait_time:.1f}초 대기...")
                    time.sleep(wait_time)
            
            # 최종 결과 요약
            total_found = len(self.found_articles)
            logger.info("=" * 50)
            logger.info("🏁 주기적 검색 완료")
            logger.info(f"📊 최종 결과:")
            logger.info(f"  - 총 검색 횟수: {search_count}회")
            logger.info(f"  - 총 발견된 게시글: {total_found}개")
            logger.info(f"  - 발견된 게시글 ID: {sorted(list(self.found_articles))}")
            logger.info("=" * 50)
            
        except KeyboardInterrupt:
            logger.info("\n⏹️ 사용자에 의해 중단되었습니다.")
            total_found = len(self.found_articles)
            logger.info(f"📊 중단 시점 결과: 총 {total_found}개 게시글 발견")
        except Exception as e:
            logger.error(f"❌ 주기적 검색 중 오류: {e}")


def parse_arguments():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="네이버 카페 게시글 키워드 검색 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python cafe_keyword_search.py -j login_data.json -c 12175294 -m 15 -k "맥북,지피티,노트북" -d 30
  python cafe_keyword_search.py --json-file login_data.json --cafe-id 12175294 --menu-id 15 --keywords "맥북,지피티,노트북" --duration 30
        """
    )
    
    parser.add_argument(
        '-j', '--json-file',
        required=True,
        help='로그인 세션 데이터가 담긴 JSON 파일 경로'
    )
    
    parser.add_argument(
        '-c', '--cafe-id',
        required=True,
        help='카페 ID (예: 12175294)'
    )
    
    parser.add_argument(
        '-m', '--menu-id',
        required=True,
        help='메뉴 ID (예: 15)'
    )
    
    parser.add_argument(
        '-k', '--keywords',
        required=True,
        help='검색할 키워드들 (쉼표로 구분, 예: "맥북,지피티,노트북")'
    )
    
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=60,
        help='검색 지속 시간 (분, 기본값: 60분)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='상세 로그 출력'
    )
    
    return parser.parse_args()


def main():
    """메인 함수"""
    args = parse_arguments()
    
    # 로그 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🔍 네이버 카페 게시글 키워드 검색")
    print("=" * 50)
    print(f"📁 JSON 파일: {args.json_file}")
    print(f"🏠 카페 ID: {args.cafe_id}")
    print(f"📋 메뉴 ID: {args.menu_id}")
    print(f"🔑 키워드: {args.keywords}")
    print(f"⏰ 지속 시간: {args.duration}분")
    print()
    
    # JSON 파일 존재 확인
    if not os.path.exists(args.json_file):
        print(f"❌ 오류: JSON 파일을 찾을 수 없습니다: {args.json_file}")
        print("💡 먼저 test_auto_login.py를 실행하여 로그인 세션 데이터를 생성하세요.")
        sys.exit(1)
    
    # 키워드 파싱
    keywords = [keyword.strip() for keyword in args.keywords.split(',')]
    if not keywords or not any(keywords):
        print("❌ 오류: 유효한 키워드를 입력해주세요.")
        sys.exit(1)
    
    try:
        # 키워드 검색기 생성 및 실행
        searcher = CafeKeywordSearcher(args.json_file)
        searcher.start_periodic_search(args.cafe_id, args.menu_id, keywords, args.duration)
        
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 실행 중 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
