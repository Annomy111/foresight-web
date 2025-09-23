"""Data models for foresight analysis responses and results"""
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, validator
import json


class ResponseStatus(str, Enum):
    """Status of an API response"""
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    RATE_LIMITED = "rate_limited"


class TokenUsage(BaseModel):
    """Token usage information"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ModelResponse(BaseModel):
    """Individual model response"""
    model: str = Field(..., description="Model identifier")
    iteration: int = Field(..., description="Iteration number (1-based)")
    ensemble_id: str = Field(..., description="Unique identifier for this response")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    response_time: float = Field(..., description="Response time in seconds")
    status: ResponseStatus = Field(..., description="Response status")

    # Content fields
    content: Optional[str] = Field(None, description="Full response content")
    probability: Optional[float] = Field(None, description="Extracted probability (0-100)")

    # Metadata
    usage: Optional[TokenUsage] = None
    error: Optional[str] = None

    # Forecast context
    question: Optional[str] = None
    definition: Optional[str] = None
    timeframe: Optional[str] = None

    @validator('probability')
    def validate_probability(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError("Probability must be between 0 and 100")
        return v

    @validator('iteration')
    def validate_iteration(cls, v):
        if v < 1:
            raise ValueError("Iteration must be >= 1")
        return v


class ModelStatistics(BaseModel):
    """Statistics for a single model"""
    model: str
    count: int = Field(..., description="Number of valid responses")
    mean: float = Field(..., description="Mean probability")
    median: float = Field(..., description="Median probability")
    std: float = Field(..., description="Standard deviation")
    min: float = Field(..., description="Minimum probability")
    max: float = Field(..., description="Maximum probability")
    success_rate: float = Field(..., description="Proportion of successful queries")

    @validator('success_rate')
    def validate_success_rate(cls, v):
        if not 0 <= v <= 1:
            raise ValueError("Success rate must be between 0 and 1")
        return v


class EnsembleStatistics(BaseModel):
    """Overall ensemble statistics"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    valid_probabilities: int
    models_used: List[str]

    # Overall probability statistics
    mean: Optional[float] = None
    median: Optional[float] = None
    std: Optional[float] = None
    min: Optional[float] = None
    max: Optional[float] = None

    # Model-specific statistics
    model_stats: Dict[str, ModelStatistics] = {}

    @property
    def success_rate(self) -> float:
        """Overall success rate"""
        return self.successful_queries / self.total_queries if self.total_queries > 0 else 0.0


class ForecastMetadata(BaseModel):
    """Metadata for a forecast run"""
    question: str
    definition: str
    timeframe: Optional[str] = None
    context: Optional[str] = None
    models: List[str]
    iterations_per_model: int
    total_queries: int
    start_time: str
    end_time: str
    duration_seconds: float


class ForecastResult(BaseModel):
    """Complete forecast result"""
    metadata: ForecastMetadata
    prompt: str
    responses: List[ModelResponse]
    statistics: EnsembleStatistics

    def get_model_responses(self, model: str) -> List[ModelResponse]:
        """Get all responses for a specific model"""
        return [r for r in self.responses if r.model == model]

    def get_successful_responses(self) -> List[ModelResponse]:
        """Get only successful responses"""
        return [r for r in self.responses if r.status == ResponseStatus.SUCCESS and r.probability is not None]

    def get_probabilities(self, model: Optional[str] = None) -> List[float]:
        """Get probability values, optionally filtered by model"""
        responses = self.get_model_responses(model) if model else self.responses
        return [r.probability for r in responses if r.probability is not None]

    def get_ensemble_probability(self) -> Optional[float]:
        """Calculate the ensemble probability (simple mean)"""
        probabilities = self.get_probabilities()
        return sum(probabilities) / len(probabilities) if probabilities else None


class ExportData(BaseModel):
    """Data structure for Excel export"""
    forecast_result: ForecastResult
    export_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    export_metadata: Dict[str, Any] = {}

    def to_summary_rows(self) -> List[Dict[str, Any]]:
        """Convert to rows for summary sheet"""
        ensemble_prob = self.forecast_result.get_ensemble_probability()

        return [{
            "Metric": "Ensemble Forecast",
            "Value": f"{ensemble_prob:.1f}%" if ensemble_prob else "N/A",
            "Description": "Aggregated probability from all models"
        }, {
            "Metric": "Total Models",
            "Value": len(self.forecast_result.metadata.models),
            "Description": "Number of AI models used"
        }, {
            "Metric": "Total Queries",
            "Value": self.forecast_result.metadata.total_queries,
            "Description": "Total API calls made"
        }, {
            "Metric": "Success Rate",
            "Value": f"{self.forecast_result.statistics.success_rate * 100:.1f}%",
            "Description": "Percentage of successful queries"
        }, {
            "Metric": "Standard Deviation",
            "Value": f"{self.forecast_result.statistics.std:.1f}%" if self.forecast_result.statistics.std else "N/A",
            "Description": "Measure of consensus between models"
        }]

    def to_detail_rows(self) -> List[Dict[str, Any]]:
        """Convert to rows for detailed responses sheet"""
        rows = []
        for response in self.forecast_result.responses:
            row = {
                "ID": response.ensemble_id,
                "Model": response.model,
                "Iteration": response.iteration,
                "Timestamp": response.timestamp,
                "Status": response.status.value,
                "Probability": response.probability,
                "Response_Time_Sec": response.response_time,
                # Truncate content to Excel cell limit (32,767 characters)
                "Content": response.content[:32000] + "..." if response.content and len(response.content) > 32000 else response.content,
                "Error": response.error,
                "Prompt_Tokens": response.usage.prompt_tokens if response.usage else None,
                "Completion_Tokens": response.usage.completion_tokens if response.usage else None,
                "Total_Tokens": response.usage.total_tokens if response.usage else None
            }
            rows.append(row)
        return rows

    def to_model_stats_rows(self) -> List[Dict[str, Any]]:
        """Convert to rows for model statistics sheet"""
        rows = []
        for model, stats in self.forecast_result.statistics.model_stats.items():
            row = {
                "Model": model,
                "Count": stats.count,
                "Mean": stats.mean,
                "Median": stats.median,
                "Std_Dev": stats.std,
                "Min": stats.min,
                "Max": stats.max,
                "Success_Rate": stats.success_rate
            }
            rows.append(row)
        return rows


class ValidationResult(BaseModel):
    """Result of response validation"""
    is_valid: bool
    issues: List[str] = []
    probability_extracted: bool = False
    reasoning_present: bool = False

    def add_issue(self, issue: str):
        """Add a validation issue"""
        self.issues.append(issue)
        self.is_valid = False


def validate_response(response: ModelResponse) -> ValidationResult:
    """
    Validate a model response for quality and completeness

    Args:
        response: The response to validate

    Returns:
        ValidationResult with details
    """
    result = ValidationResult(is_valid=True)

    # Check if response was successful
    if response.status != ResponseStatus.SUCCESS:
        result.add_issue(f"Response status is {response.status}")
        return result

    # Check if content is present
    if not response.content:
        result.add_issue("No content in response")
        return result

    # Check if probability was extracted
    if response.probability is None:
        result.add_issue("Could not extract probability from response")
    else:
        result.probability_extracted = True

        # Check probability range
        if not (0 <= response.probability <= 100):
            result.add_issue(f"Probability {response.probability} is out of range [0, 100]")

    # Check if reasoning is present (look for key indicators)
    content_lower = response.content.lower()
    reasoning_indicators = ["begründung", "base rate", "case rate", "confidence", "analyse"]

    if any(indicator in content_lower for indicator in reasoning_indicators):
        result.reasoning_present = True
    else:
        result.add_issue("Response appears to lack structured reasoning")

    # Check if PROGNOSE format is followed
    if "prognose:" not in content_lower:
        result.add_issue("Response does not follow expected PROGNOSE format")

    return result