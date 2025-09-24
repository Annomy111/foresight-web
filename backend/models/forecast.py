"""Forecast data models for Excel export"""
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ModelResponse(BaseModel):
    """Individual model response data"""
    model: str
    probability: float
    confidence: str = "medium"
    reasoning: str
    analysis_time: float


class ForecastResponse(BaseModel):
    """Complete forecast response with all model results"""
    forecast_id: str
    question: str
    definition: Optional[str] = None
    timeframe: str
    models_used: List[str]
    aggregate_probability: float
    model_responses: List[ModelResponse]
    iterations: int
    created_at: str
    total_analysis_time: float

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }