"""
Shared models for microservices
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class BaseRequest(BaseModel):
    """기본 요청 모델"""
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: Optional[datetime] = Field(default_factory=datetime.now)


class BaseResponse(BaseModel):
    """기본 응답 모델"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    request_id: Optional[str] = None
    processing_time: Optional[float] = None


class SearchRequest(BaseRequest):
    """검색 요청 모델"""
    query: str = Field(..., min_length=1, max_length=1000)
    filters: Optional[Dict[str, Any]] = None
    limit: Optional[int] = Field(default=10, ge=1, le=100)
    offset: Optional[int] = Field(default=0, ge=0)


class SearchResult(BaseModel):
    """검색 결과 모델"""
    id: str
    title: str
    content: str
    score: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None
    source: Optional[str] = None


class SearchResponse(BaseResponse):
    """검색 응답 모델"""
    results: List[SearchResult] = []
    total_count: int = 0
    query: str = ""


class ChatRequest(BaseRequest):
    """채팅 요청 모델"""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_history: Optional[List[Dict[str, str]]] = []
    context: Optional[Dict[str, Any]] = None


class ChatResponse(BaseResponse):
    """채팅 응답 모델"""
    message: str = ""
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    sources: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = None


class AnalyticsRequest(BaseRequest):
    """분석 요청 모델"""
    data_type: str = Field(..., description="분석할 데이터 타입")
    parameters: Optional[Dict[str, Any]] = None
    date_range: Optional[Dict[str, str]] = None


class AnalyticsResponse(BaseResponse):
    """분석 응답 모델"""
    charts: Optional[List[Dict[str, Any]]] = []
    insights: Optional[List[str]] = []
    metrics: Optional[Dict[str, float]] = None


class MLRequest(BaseRequest):
    """머신러닝 요청 모델"""
    model_type: str = Field(..., description="모델 타입")
    input_data: Dict[str, Any] = Field(..., description="입력 데이터")
    parameters: Optional[Dict[str, Any]] = None


class MLResponse(BaseResponse):
    """머신러닝 응답 모델"""
    prediction: Optional[Any] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_version: Optional[str] = None
    feature_importance: Optional[Dict[str, float]] = None


class HealthCheck(BaseModel):
    """헬스체크 모델"""
    service_name: str
    status: str = "healthy"
    version: str = "1.0.0"
    uptime: Optional[float] = None
    dependencies: Optional[Dict[str, str]] = None
    timestamp: datetime = Field(default_factory=datetime.now) 