#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
엑셀 파일 처리 API 라우터
"""

from fastapi import APIRouter, File, UploadFile, HTTPException
import pandas as pd
import io
from typing import Dict, Any

from app.core.config import settings
from app.models.excel import (
    ExcelUploadResponse,
    ExcelAnalysisResponse,
    ColumnInfo,
    Statistics,
    NumericAnalysis,
    TextAnalysis,
    BasicInfo,
    DataTypes,
)

router = APIRouter(prefix="/excel", tags=["Excel"])


@router.post("/upload", response_model=ExcelUploadResponse)
async def upload_excel(file: UploadFile = File(...)):
    """
    엑셀 파일을 업로드하고 컬럼과 데이터를 읽어오는 API

    Args:
        file: 업로드할 엑셀 파일 (.xlsx, .xls)

    Returns:
        ExcelUploadResponse: 컬럼 정보, 데이터, 통계 정보
    """
    # 파일 확장자 검증
    if not file.filename.lower().endswith(tuple(settings.allowed_extensions)):
        raise HTTPException(
            status_code=400,
            detail=f"엑셀 파일만 업로드 가능합니다. {settings.allowed_extensions}",
        )

    try:
        # 파일 내용을 메모리로 읽기
        contents = await file.read()

        # 파일 크기 검증
        if len(contents) > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"파일 크기가 너무 큽니다. 최대 {settings.max_file_size // (1024*1024)}MB까지 가능합니다.",
            )

        # pandas로 엑셀 파일 읽기
        df = pd.read_excel(io.BytesIO(contents))

        # 컬럼 정보 추출
        columns_info = []
        for col in df.columns:
            col_info = ColumnInfo(
                name=str(col),
                dtype=str(df[col].dtype),
                non_null_count=int(df[col].count()),
                null_count=int(df[col].isnull().sum()),
                unique_count=int(df[col].nunique()),
            )
            columns_info.append(col_info)

        # 데이터를 JSON 직렬화 가능한 형태로 변환
        data_records = df.fillna("").to_dict("records")

        # 기본 통계 정보
        stats = Statistics(
            total_rows=len(df),
            total_columns=len(df.columns),
            memory_usage=df.memory_usage(deep=True).sum(),
            shape=df.shape,
        )

        return ExcelUploadResponse(
            status="success",
            filename=file.filename,
            file_size=len(contents),
            columns=columns_info,
            data=data_records,
            statistics=stats,
            preview=data_records[:5] if len(data_records) > 5 else data_records,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"엑셀 파일 처리 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/analyze", response_model=ExcelAnalysisResponse)
async def analyze_excel(file: UploadFile = File(...)):
    """
    엑셀 파일의 상세 분석 정보를 제공하는 API

    Args:
        file: 분석할 엑셀 파일

    Returns:
        ExcelAnalysisResponse: 상세 분석 정보 (통계, 데이터 타입 분포 등)
    """
    if not file.filename.lower().endswith(tuple(settings.allowed_extensions)):
        raise HTTPException(
            status_code=400,
            detail=f"엑셀 파일만 업로드 가능합니다. {settings.allowed_extensions}",
        )

    try:
        contents = await file.read()

        if len(contents) > settings.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"파일 크기가 너무 큽니다. 최대 {settings.max_file_size // (1024*1024)}MB까지 가능합니다.",
            )

        df = pd.read_excel(io.BytesIO(contents))

        # 수치형 컬럼 분석
        numeric_analysis = {}
        numeric_cols = df.select_dtypes(include=["number"]).columns

        for col in numeric_cols:
            numeric_analysis[col] = NumericAnalysis(
                mean=float(df[col].mean()) if not df[col].empty else None,
                median=float(df[col].median()) if not df[col].empty else None,
                std=float(df[col].std()) if not df[col].empty else None,
                min=float(df[col].min()) if not df[col].empty else None,
                max=float(df[col].max()) if not df[col].empty else None,
                quartiles={
                    "Q1": float(df[col].quantile(0.25)) if not df[col].empty else None,
                    "Q3": float(df[col].quantile(0.75)) if not df[col].empty else None,
                },
            )

        # 문자열 컬럼 분석
        text_analysis = {}
        text_cols = df.select_dtypes(include=["object"]).columns

        for col in text_cols:
            text_analysis[col] = TextAnalysis(
                unique_values=int(df[col].nunique()),
                most_common=(
                    df[col].value_counts().head(5).to_dict()
                    if not df[col].empty
                    else {}
                ),
                avg_length=(
                    float(df[col].astype(str).str.len().mean())
                    if not df[col].empty
                    else None
                ),
            )

        return ExcelAnalysisResponse(
            status="success",
            filename=file.filename,
            basic_info=BasicInfo(
                rows=len(df), columns=len(df.columns), column_names=df.columns.tolist()
            ),
            data_types=DataTypes(
                numeric_columns=len(numeric_cols),
                text_columns=len(text_cols),
                total_missing_values=int(df.isnull().sum().sum()),
            ),
            numeric_analysis=numeric_analysis,
            text_analysis=text_analysis,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"엑셀 파일 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/sample")
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
        "supported_formats": settings.allowed_extensions,
        "max_file_size_mb": settings.max_file_size // (1024 * 1024),
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
