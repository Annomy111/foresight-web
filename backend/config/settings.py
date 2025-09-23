"""Configuration management for Foresight Analyzer"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class APIConfig(BaseModel):
    """API configuration settings"""
    api_key: str = Field(..., description="OpenRouter API key")
    base_url: str = Field(default="https://openrouter.ai/api/v1", description="API base URL")
    timeout: int = Field(default=120, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: int = Field(default=5, description="Delay between retries in seconds")

    @validator('api_key')
    def api_key_not_empty(cls, v):
        if not v or v == "your_openrouter_api_key_here":
            raise ValueError("Valid OpenRouter API key required")
        return v

class ModelConfig(BaseModel):
    """Model configuration settings"""
    enabled_models: List[str] = Field(
        default=[
            # Verified working free models (Sept 2025) - INCLUDING GROK-4 FAST!
            "x-ai/grok-4-fast:free",  # NEW! Currently free on OpenRouter
            "google/gemma-2b-it:free",
            "mistralai/mistral-7b-instruct:free",
            "nousresearch/hermes-3-llama-3.1-8b:free",
            "qwen/qwen-2.5-72b-instruct:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "google/gemma-2-9b-it:free"
        ],
        description="List of models to use"
    )
    iterations_per_model: int = Field(default=10, description="Number of iterations per model")
    concurrent_requests: int = Field(default=3, description="Number of concurrent API requests")

    @validator('iterations_per_model')
    def validate_iterations(cls, v):
        if v < 1 or v > 100:
            raise ValueError("Iterations must be between 1 and 100")
        return v

class OutputConfig(BaseModel):
    """Output configuration settings"""
    output_dir: Path = Field(default=Path("data/results"), description="Output directory")
    excel_filename_prefix: str = Field(default="foresight_analysis", description="Excel filename prefix")
    save_raw_responses: bool = Field(default=True, description="Save raw API responses")

    @validator('output_dir')
    def create_output_dir(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v

class Settings(BaseModel):
    """Main settings container"""
    api: APIConfig
    models: ModelConfig
    output: OutputConfig

    @classmethod
    def load_from_env(cls) -> 'Settings':
        """Load settings from environment variables"""
        # API configuration - Fixed typo: should be OPENROUTER_API_KEY not OPENROUTER_API_KEY1
        api_key = os.getenv("OPENROUTER_API_KEY", "")
        if not api_key:
            # Fallback to check OPENROUTER_API_KEY1 if it was set that way
            api_key = os.getenv("OPENROUTER_API_KEY1", "")

        # Log API key status (without exposing the key)
        if api_key:
            print(f"✅ API key loaded: {api_key[:8]}...")
        else:
            print("❌ WARNING: No API key found in environment variables!")

        api_config = APIConfig(
            api_key=api_key,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            timeout=int(os.getenv("REQUEST_TIMEOUT", "120")),
            retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
            retry_delay=int(os.getenv("RETRY_DELAY", "5"))
        )

        # Model configuration
        models_str = os.getenv("ENABLED_MODELS", "")
        enabled_models = [m.strip() for m in models_str.split(",") if m.strip()]
        if not enabled_models:
            enabled_models = ModelConfig().enabled_models

        model_config = ModelConfig(
            enabled_models=enabled_models,
            iterations_per_model=int(os.getenv("ITERATIONS_PER_MODEL", "10")),
            concurrent_requests=int(os.getenv("CONCURRENT_REQUESTS", "3"))
        )

        # Output configuration
        output_config = OutputConfig(
            output_dir=Path(os.getenv("OUTPUT_DIR", "data/results")),
            excel_filename_prefix=os.getenv("EXCEL_FILENAME_PREFIX", "foresight_analysis"),
            save_raw_responses=os.getenv("SAVE_RAW_RESPONSES", "true").lower() == "true"
        )

        return cls(api=api_config, models=model_config, output=output_config)

# Singleton instance
settings = None

def get_settings() -> Settings:
    """Get or create settings instance"""
    global settings
    if settings is None:
        settings = Settings.load_from_env()
    return settings

def load_settings() -> dict:
    """Load settings as dictionary (backward compatibility)"""
    settings_obj = get_settings()
    return {
        'OPENROUTER_API_KEY': settings_obj.api.api_key,
        'OPENROUTER_BASE_URL': settings_obj.api.base_url,
        'ENABLED_MODELS': ','.join(settings_obj.models.enabled_models),
        'ITERATIONS_PER_MODEL': str(settings_obj.models.iterations_per_model),
        'CONCURRENT_REQUESTS': str(settings_obj.models.concurrent_requests),
        'REQUEST_TIMEOUT': str(settings_obj.api.timeout),
        'RETRY_ATTEMPTS': str(settings_obj.api.retry_attempts),
        'RETRY_DELAY': str(settings_obj.api.retry_delay),
        'OUTPUT_DIR': str(settings_obj.output.output_dir),
        'SAVE_RAW_RESPONSES': str(settings_obj.output.save_raw_responses).lower()
    }