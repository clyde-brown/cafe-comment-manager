#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Hello 페이지 애플리케이션
간단한 Hello 메시지를 출력하는 웹 API
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import pandas as pd
import io
import os
from typing import Dict, List, Any

# FastAPI 앱 인스턴스 생성
app = FastAPI(
    title="Cafe Comment Manager API",
    description="카페 댓글 관리를 위한 API 서버",
    version="1.0.0",
)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """메인 페이지 - Hello 메시지 출력"""
    html_content = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cafe Comment Manager</title>
        <style>
            body {
                font-family: 'Arial', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                color: white;
            }
            .container {
                text-align: center;
                background: rgba(255, 255, 255, 0.1);
                padding: 3rem;
                border-radius: 20px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }
            h1 {
                font-size: 3rem;
                margin-bottom: 1rem;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            }
            p {
                font-size: 1.2rem;
                margin-bottom: 2rem;
                opacity: 0.9;
            }
            .emoji {
                font-size: 4rem;
                margin-bottom: 1rem;
                display: block;
            }
            .api-link {
                display: inline-block;
                padding: 12px 24px;
                background: rgba(255, 255, 255, 0.2);
                border: none;
                border-radius: 50px;
                color: white;
                text-decoration: none;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .api-link:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <span class="emoji">☕</span>
            <h1>Hello, FastAPI!</h1>
            <p>카페 댓글 관리 시스템에 오신 것을 환영합니다!</p>
            <p>Selenium과 FastAPI가 함께 동작하는 환경이 준비되었습니다.</p>
            <a href="/docs" class="api-link">API 문서 보기</a>
        </div>
    </body>
    </html>
    """
    return html_content


@app.get("/hello")
async def hello():
    """간단한 JSON Hello 메시지"""
    return {
        "message": "Hello, World!",
        "status": "success",
        "description": "FastAPI와 Selenium이 함께 동작하는 환경입니다.",
    }


@app.get("/hello/{name}")
async def hello_name(name: str):
    """이름을 포함한 개인화된 Hello 메시지"""
    return {"message": f"Hello, {name}!", "status": "success", "name": name}


@app.get("/api/info")
async def get_info():
    """API 정보 반환"""
    return {
        "app_name": "Cafe Comment Manager",
        "version": "1.0.0",
        "description": "카페 댓글 관리를 위한 API 서버",
        "features": [
            "Selenium 브라우저 자동화",
            "FastAPI 웹 서버",
            "댓글 관리 시스템",
            "엑셀 파일 처리",
        ],
    }


@app.post("/api/excel/upload")
async def upload_excel(file: UploadFile = File(...)):
    """
    엑셀 파일을 업로드하고 컬럼과 데이터를 읽어오는 API

    Args:
        file: 업로드할 엑셀 파일 (.xlsx, .xls)

    Returns:
        JSON: 컬럼 정보, 데이터, 통계 정보
    """
    # 파일 확장자 검증
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="엑셀 파일만 업로드 가능합니다. (.xlsx, .xls)"
        )

    try:
        # 파일 내용을 메모리로 읽기
        contents = await file.read()

        # pandas로 엑셀 파일 읽기
        df = pd.read_excel(io.BytesIO(contents))

        # 컬럼 정보 추출
        columns_info = []
        for col in df.columns:
            col_info = {
                "name": str(col),
                "dtype": str(df[col].dtype),
                "non_null_count": int(df[col].count()),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
            }
            columns_info.append(col_info)

        # 데이터를 JSON 직렬화 가능한 형태로 변환
        data_records = df.fillna("").to_dict("records")

        # 기본 통계 정보
        stats = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "memory_usage": df.memory_usage(deep=True).sum(),
            "shape": df.shape,
        }

        return {
            "status": "success",
            "filename": file.filename,
            "file_size": len(contents),
            "columns": columns_info,
            "data": data_records,
            "statistics": stats,
            "preview": data_records[:5] if len(data_records) > 5 else data_records,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"엑셀 파일 처리 중 오류가 발생했습니다: {str(e)}"
        )


@app.post("/api/excel/analyze")
async def analyze_excel(file: UploadFile = File(...)):
    """
    엑셀 파일의 상세 분석 정보를 제공하는 API

    Args:
        file: 분석할 엑셀 파일

    Returns:
        JSON: 상세 분석 정보 (통계, 데이터 타입 분포 등)
    """
    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="엑셀 파일만 업로드 가능합니다. (.xlsx, .xls)"
        )

    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))

        # 수치형 컬럼 분석
        numeric_analysis = {}
        numeric_cols = df.select_dtypes(include=["number"]).columns

        for col in numeric_cols:
            numeric_analysis[col] = {
                "mean": float(df[col].mean()) if not df[col].empty else None,
                "median": float(df[col].median()) if not df[col].empty else None,
                "std": float(df[col].std()) if not df[col].empty else None,
                "min": float(df[col].min()) if not df[col].empty else None,
                "max": float(df[col].max()) if not df[col].empty else None,
                "quartiles": {
                    "Q1": float(df[col].quantile(0.25)) if not df[col].empty else None,
                    "Q3": float(df[col].quantile(0.75)) if not df[col].empty else None,
                },
            }

        # 문자열 컬럼 분석
        text_analysis = {}
        text_cols = df.select_dtypes(include=["object"]).columns

        for col in text_cols:
            text_analysis[col] = {
                "unique_values": int(df[col].nunique()),
                "most_common": (
                    df[col].value_counts().head(5).to_dict()
                    if not df[col].empty
                    else {}
                ),
                "avg_length": (
                    float(df[col].astype(str).str.len().mean())
                    if not df[col].empty
                    else None
                ),
            }

        return {
            "status": "success",
            "filename": file.filename,
            "basic_info": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
            },
            "data_types": {
                "numeric_columns": len(numeric_cols),
                "text_columns": len(text_cols),
                "total_missing_values": int(df.isnull().sum().sum()),
            },
            "numeric_analysis": numeric_analysis,
            "text_analysis": text_analysis,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"엑셀 파일 분석 중 오류가 발생했습니다: {str(e)}"
        )


@app.get("/api/excel/sample")
async def get_excel_sample():
    """
    엑셀 업로드 API 사용 예시를 제공하는 엔드포인트
    """
    return {
        "message": "엑셀 파일 업로드 API 사용 방법",
        "endpoints": {
            "/api/excel/upload": {
                "method": "POST",
                "description": "엑셀 파일 업로드 및 기본 데이터 읽기",
                "parameters": "file: UploadFile (엑셀 파일)",
            },
            "/api/excel/analyze": {
                "method": "POST",
                "description": "엑셀 파일 상세 분석",
                "parameters": "file: UploadFile (엑셀 파일)",
            },
        },
        "supported_formats": [".xlsx", ".xls"],
        "example_response": {
            "status": "success",
            "filename": "example.xlsx",
            "columns": ["이름", "나이", "이메일"],
            "data": [
                {"이름": "홍길동", "나이": 25, "이메일": "hong@example.com"},
                {"이름": "김철수", "나이": 30, "이메일": "kim@example.com"},
            ],
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
