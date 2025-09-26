#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
애플리케이션 설정
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""

    app_name: str = "Cafe Comment Manager API"
    app_version: str = "1.0.0"
    app_description: str = "카페 댓글 관리를 위한 API 서버"

    # 서버 설정
    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True

    # 파일 업로드 설정
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    allowed_extensions: list = [".xlsx", ".xls"]

    class Config:
        env_file = ".env"


settings = Settings()
