#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 카페 댓글 자동 업로드 스크립트
순수 API 호출로 자동화 탐지 우회
"""

import logging
import time
import random
import re
import json
import sys
import os
import requests
import argparse
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlencode, quote

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 상수 정의
CAFE_COMMENT_API_URL = "https://apis.naver.com/cafe-web/cafe-mobile/CommentPost.json"


class CafeCommentUploader:
    """네이버 카페 댓글 자동 업로드 클래스 (순수 API 호출)"""
    
    def __init__(self, json_file_path: str):
        """
        초기화
        
        Args:
            json_file_path: 로그인 세션 데이터가 담긴 JSON 파일 경로
        """
        self.json_file_path = json_file_path
        self.session_data = self._load_session_data()
        self.session = requests.Session()
        
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
    
    def _simulate_human_behavior(self) -> None:
        """인간적인 행동 시뮬레이션 (대기 시간)"""
        # 랜덤한 대기 시간 (1-3초)
        wait_time = random.uniform(1.0, 3.0)
        logger.info(f"⏳ 자연스러운 대기 시간: {wait_time:.2f}초")
        time.sleep(wait_time)
    
    def _prepare_referer_url(self, cafe_id: str, article_id: str) -> str:
        """Referer URL 생성"""
        # 자연스러운 게시글 URL 생성
        referer_url = f"https://cafe.naver.com/ca-fe/cafes/{cafe_id}/articles/{article_id}?menuid=15&referrerAllArticles=false&fromNext=true"
        return referer_url
    
    def upload_comment(self, cafe_id: str, article_id: str, comment_content: str) -> Dict[str, Any]:
        """
        댓글 업로드 (순수 API 호출)
        
        Args:
            cafe_id: 카페 ID
            article_id: 게시글 ID
            comment_content: 댓글 내용
        
        Returns:
            Dict: 업로드 결과
        """
        try:
            logger.info("=" * 50)
            logger.info("🚀 네이버 카페 댓글 업로드 시작 (API 전용)")
            logger.info("=" * 50)
            
            # 1단계: requests 세션 설정
            self._setup_requests_session()
            
            # 2단계: Referer URL 설정
            referer_url = self._prepare_referer_url(cafe_id, article_id)
            self.session.headers.update({
                'Referer': referer_url
            })
            logger.info(f"📍 Referer URL 설정: {referer_url}")
            
            # 3단계: 인간적인 행동 시뮬레이션
            self._simulate_human_behavior()
            
            # 4단계: API 요청 데이터 준비
            logger.info("📤 댓글 업로드 API 호출 중...")
            
            # URL 인코딩된 데이터 준비
            data = {
                'content': comment_content,
                'stickerId': '',
                'cafeId': cafe_id,
                'articleId': article_id,
                'requestFrom': 'A'
            }
            
            # 5단계: API 호출
            response = self.session.post(CAFE_COMMENT_API_URL, data=data, timeout=30)
            
            logger.info(f"API 응답 상태: {response.status_code}")
            logger.info(f"API 응답 내용: {response.text[:200]}...")
            
            # 6단계: 결과 처리
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    logger.info("✅ 댓글 업로드 성공!")
                    return {
                        "success": True,
                        "message": "댓글 업로드 성공",
                        "response": response_json,
                        "status_code": response.status_code
                    }
                except json.JSONDecodeError:
                    logger.warning("JSON 파싱 실패, 텍스트 응답으로 처리")
                    return {
                        "success": True,
                        "message": "댓글 업로드 성공 (텍스트 응답)",
                        "response": response.text,
                        "status_code": response.status_code
                    }
            else:
                logger.error(f"API 호출 실패: {response.status_code}")
                return {
                    "success": False,
                    "message": f"댓글 업로드 실패 (상태코드: {response.status_code})",
                    "response": response.text,
                    "status_code": response.status_code
                }
                
        except requests.exceptions.Timeout:
            logger.error("❌ API 호출 타임아웃")
            return {
                "success": False,
                "message": "API 호출 타임아웃",
                "error": "Request timeout"
            }
        except requests.exceptions.ConnectionError:
            logger.error("❌ 네트워크 연결 오류")
            return {
                "success": False,
                "message": "네트워크 연결 오류",
                "error": "Connection error"
            }
        except Exception as e:
            logger.error(f"❌ 댓글 업로드 중 오류: {e}")
            return {
                "success": False,
                "message": f"댓글 업로드 중 오류가 발생했습니다: {str(e)}",
                "error": str(e)
            }


def parse_arguments():
    """명령행 인수 파싱"""
    parser = argparse.ArgumentParser(
        description="네이버 카페 댓글 자동 업로드 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python test_cafe_comment_upload.py -j login_data.json -c 12175294 -a 2750301 -m "댓글 내용"
  python test_cafe_comment_upload.py --json-file login_data.json --cafe-id 12175294 --article-id 2750301 --message "댓글 내용"
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
        '-a', '--article-id',
        required=True,
        help='게시글 ID (예: 2750301)'
    )
    
    parser.add_argument(
        '-m', '--message',
        required=True,
        help='댓글 내용'
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
    
    print("🤖 네이버 카페 댓글 자동 업로드")
    print("=" * 50)
    print(f"📁 JSON 파일: {args.json_file}")
    print(f"🏠 카페 ID: {args.cafe_id}")
    print(f"📄 게시글 ID: {args.article_id}")
    print(f"💬 댓글 내용: {args.message}")
    print()
    
    # JSON 파일 존재 확인
    if not os.path.exists(args.json_file):
        print(f"❌ 오류: JSON 파일을 찾을 수 없습니다: {args.json_file}")
        print("💡 먼저 test_auto_login.py를 실행하여 로그인 세션 데이터를 생성하세요.")
        sys.exit(1)
    
    try:
        # 댓글 업로더 생성 및 실행
        uploader = CafeCommentUploader(args.json_file)
        result = uploader.upload_comment(args.cafe_id, args.article_id, args.message)
        
        # 결과 출력
        print("\n📊 업로드 결과:")
        print("-" * 50)
        print(f"성공 여부: {result.get('success')}")
        print(f"메시지: {result.get('message')}")
        print(f"상태 코드: {result.get('status_code')}")
        
        if result.get('success'):
            print("\n🎉 댓글 업로드 성공!")
            print("🔧 자동화 탐지 우회 및 자연스러운 브라우저 행동 시뮬레이션 완료")
            sys.exit(0)
        else:
            print("\n⚠️ 댓글 업로드 실패")
            if result.get('error'):
                print(f"오류: {result.get('error')}")
            sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n⏹️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 실행 중 오류: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
