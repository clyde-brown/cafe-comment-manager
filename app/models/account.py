#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
계정 정보 모델
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime


class LoginStatus(str, Enum):
    """로그인 상태"""

    IDLE = "idle"  # 대기 (회색)
    LOADING = "loading"  # 로그인 중 (노랑)
    SUCCESS = "success"  # 성공 (초록)
    ERROR = "error"  # 실패 (빨강)


class AccountInfo(BaseModel):
    """계정 정보 모델"""

    id: Optional[int] = Field(None, description="계정 순번")
    username: str = Field(..., description="네이버 아이디")
    password: str = Field(..., description="네이버 비밀번호")
    status: LoginStatus = Field(LoginStatus.IDLE, description="로그인 상태")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    login_time: Optional[datetime] = Field(None, description="로그인 시간")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat() if v else None}


class BatchLoginRequest(BaseModel):
    """일괄 로그인 요청"""

    accounts: List[AccountInfo] = Field(..., description="로그인할 계정 목록")


class SingleLoginRequest(BaseModel):
    """단일 로그인 요청"""

    username: str = Field(..., description="네이버 아이디")
    password: str = Field(..., description="네이버 비밀번호")
    account_id: Optional[int] = Field(None, description="계정 순번")


class LoginResponse(BaseModel):
    """로그인 응답"""

    success: bool = Field(..., description="성공 여부")
    account_id: Optional[int] = Field(None, description="계정 순번")
    username: str = Field(..., description="아이디")
    status: LoginStatus = Field(..., description="로그인 상태")
    message: str = Field(..., description="결과 메시지")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    login_time: Optional[datetime] = Field(None, description="로그인 시간")


class BatchLoginResponse(BaseModel):
    """일괄 로그인 응답"""

    task_id: str = Field(..., description="작업 ID")
    total_accounts: int = Field(..., description="전체 계정 수")
    message: str = Field(..., description="시작 메시지")


class LoginStatusResponse(BaseModel):
    """로그인 상태 조회 응답"""

    task_id: str = Field(..., description="작업 ID")
    total_accounts: int = Field(..., description="전체 계정 수")
    completed_accounts: int = Field(..., description="완료된 계정 수")
    success_count: int = Field(..., description="성공한 계정 수")
    error_count: int = Field(..., description="실패한 계정 수")
    in_progress: bool = Field(..., description="진행 중 여부")
    accounts: List[AccountInfo] = Field(..., description="계정별 상태")
    progress_percentage: float = Field(..., description="진행률 (%)")
