#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
엑셀 관련 데이터 모델
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ColumnInfo(BaseModel):
    """컬럼 정보 모델"""

    name: str
    dtype: str
    non_null_count: int
    null_count: int
    unique_count: int


class Statistics(BaseModel):
    """기본 통계 정보 모델"""

    total_rows: int
    total_columns: int
    memory_usage: int
    shape: tuple


class ExcelUploadResponse(BaseModel):
    """엑셀 업로드 응답 모델"""

    status: str
    filename: str
    file_size: int
    columns: List[ColumnInfo]
    data: List[Dict[str, Any]]
    statistics: Statistics
    preview: List[Dict[str, Any]]


class NumericAnalysis(BaseModel):
    """수치형 컬럼 분석 모델"""

    mean: Optional[float]
    median: Optional[float]
    std: Optional[float]
    min: Optional[float]
    max: Optional[float]
    quartiles: Dict[str, Optional[float]]


class TextAnalysis(BaseModel):
    """텍스트 컬럼 분석 모델"""

    unique_values: int
    most_common: Dict[str, int]
    avg_length: Optional[float]


class BasicInfo(BaseModel):
    """기본 정보 모델"""

    rows: int
    columns: int
    column_names: List[str]


class DataTypes(BaseModel):
    """데이터 타입 정보 모델"""

    numeric_columns: int
    text_columns: int
    total_missing_values: int


class ExcelAnalysisResponse(BaseModel):
    """엑셀 분석 응답 모델"""

    status: str
    filename: str
    basic_info: BasicInfo
    data_types: DataTypes
    numeric_analysis: Dict[str, NumericAnalysis]
    text_analysis: Dict[str, TextAnalysis]
