#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI 메인 애플리케이션 진입점
app.main의 앱을 실행합니다
"""

import uvicorn
from app.core.config import settings
from app.main import (
    app,
)  # app 변수를 import하여 uvicorn main:app 명령어로도 실행 가능하도록 함

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
