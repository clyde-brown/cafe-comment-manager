#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로그인 API 라우터
"""

import asyncio
import uuid
from datetime import datetime
from typing import Dict, List
from fastapi import APIRouter, BackgroundTasks, HTTPException
import logging

from app.models.account import (
    AccountInfo,
    LoginStatus,
    SingleLoginRequest,
    BatchLoginRequest,
    LoginResponse,
    BatchLoginResponse,
    LoginStatusResponse,
)
from app.services.browser_service import BrowserService

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/login", tags=["Login"])

# 전역 상태 저장소 (실제 운영에서는 Redis 등 사용)
login_tasks: Dict[str, Dict] = {}


@router.post("/single", response_model=LoginResponse)
async def login_single_account(request: SingleLoginRequest):
    """
    단일 계정 네이버 로그인

    Args:
        request: 로그인 요청 정보

    Returns:
        LoginResponse: 로그인 결과
    """
    try:
        logger.info(f"단일 로그인 시작: {request.username}")

        # 네이버 로그인 실행 (비동기 처리로 변경)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: BrowserService.login_to_naver(
                username=request.username, password=request.password
            ),
        )

        # 결과 분석
        if result.get("success", False):
            status = LoginStatus.SUCCESS
            message = "로그인 성공"
            error_message = None
        else:
            status = LoginStatus.ERROR
            message = "로그인 실패"
            error_message = result.get("error", "알 수 없는 오류")

        return LoginResponse(
            success=result.get("success", False),
            account_id=request.account_id,
            username=request.username,
            status=status,
            message=message,
            error_message=error_message,
            login_time=datetime.now(),
        )

    except Exception as e:
        logger.error(f"단일 로그인 오류: {e}")
        return LoginResponse(
            success=False,
            account_id=request.account_id,
            username=request.username,
            status=LoginStatus.ERROR,
            message="로그인 실패",
            error_message=str(e),
            login_time=datetime.now(),
        )


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

                # 계정별 추가 지연 (캡챠 방지)
                await asyncio.sleep(1 + (i * 0.5))  # 첫 번째: 1초, 두 번째: 1.5초, ...

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

                # 계정 간 간격 (서버 부하 방지)
                await asyncio.sleep(2)

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


@router.delete("/task/{task_id}")
async def delete_login_task(task_id: str):
    """
    완료된 로그인 작업 삭제

    Args:
        task_id: 작업 ID
    """
    if task_id not in login_tasks:
        raise HTTPException(status_code=404, detail="작업을 찾을 수 없습니다.")

    del login_tasks[task_id]
    return {"message": f"작업 {task_id}가 삭제되었습니다."}


@router.get("/tasks")
async def list_login_tasks():
    """진행 중인 모든 로그인 작업 목록 조회"""
    return {
        "tasks": [
            {
                "task_id": task_id,
                "total_accounts": data["total_accounts"],
                "completed_accounts": data["completed_accounts"],
                "in_progress": data["in_progress"],
                "start_time": data["start_time"],
            }
            for task_id, data in login_tasks.items()
        ]
    }
