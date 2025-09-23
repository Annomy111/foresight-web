"""
FastAPI Backend for Foresight Analyzer Web Application
Integrates the real AI forecasting system with web interface
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid
import asyncio
import os
import sys
import json
from datetime import datetime
from pathlib import Path
import tempfile
import threading
import time

# Add current directory to path for imports
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

# Import the real forecasting components
from core.api_client import OpenRouterClient
from core.ensemble_manager import EnsembleManager
from core.statistics import calculate_ensemble_probability, calculate_model_statistics
from config.prompts import PromptTemplates
from config.settings import load_settings
from analysis.aggregator import ForecastAggregator
from export.excel_exporter import ExcelExporter
from utils.logging import setup_logger

# Initialize FastAPI app
app = FastAPI(
    title="Foresight Analyzer API",
    description="AI-powered probabilistic forecasting using ensemble methods",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
running_forecasts = {}
logger = setup_logger("foresight_api")
settings = load_settings()

# Request/Response Models
class ForecastRequest(BaseModel):
    question: str
    definition: Optional[str] = ""
    timeframe: Optional[str] = "2026"
    iterations: Optional[int] = 5
    models: Optional[List[str]] = None

class ForecastResponse(BaseModel):
    success: bool
    forecast_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ForecastStatus(BaseModel):
    forecast_id: str
    status: str  # "running", "completed", "failed"
    progress: int  # 0-100
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

# Available models endpoint
@app.get("/api/models")
async def get_available_models():
    """Get list of available AI models"""
    enabled_models = settings.get('ENABLED_MODELS', '').split(',')
    return {
        "models": [model.strip() for model in enabled_models if model.strip()],
        "default_iterations": settings.get('ITERATIONS_PER_MODEL', 5)
    }

# Root endpoint with API information
@app.get("/")
async def root():
    """Root endpoint - API information and available endpoints"""
    enabled_models = settings.get('ENABLED_MODELS', '').split(',')
    return {
        "message": "Foresight Analyzer API",
        "description": "AI-powered probabilistic forecasting using ensemble methods",
        "version": "2.0.0",
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "models": "/api/models",
            "forecast": "/api/forecast",
            "simple_forecast": "/forecast",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "capabilities": {
            "enabled_models": len([m.strip() for m in enabled_models if m.strip()]),
            "ensemble_forecasting": True,
            "excel_export": True,
            "background_processing": True
        }
    }

# Docs redirect for convenience
@app.get("/docs-redirect")
async def docs_redirect():
    """Redirect to FastAPI docs"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")

# Health check endpoint
@app.get("/health")
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Main forecast endpoint
@app.post("/api/forecast", response_model=ForecastResponse)
async def create_forecast(request: ForecastRequest, background_tasks: BackgroundTasks):
    """Create a new forecast using the real AI system"""
    try:
        forecast_id = str(uuid.uuid4())

        # Initialize forecast status
        running_forecasts[forecast_id] = {
            "status": "running",
            "progress": 0,
            "result": None,
            "error": None,
            "start_time": datetime.now()
        }

        # Start forecast in background
        background_tasks.add_task(
            run_forecast,
            forecast_id,
            request.question,
            request.definition or "",
            request.timeframe or "2026",
            request.iterations or 5,
            request.models
        )

        return ForecastResponse(
            success=True,
            forecast_id=forecast_id
        )

    except Exception as e:
        logger.error(f"Error creating forecast: {e}")
        return ForecastResponse(
            success=False,
            error=str(e)
        )

# Forecast status endpoint
@app.get("/api/forecast/{forecast_id}", response_model=ForecastStatus)
async def get_forecast_status(forecast_id: str):
    """Get the status of a running forecast"""
    if forecast_id not in running_forecasts:
        raise HTTPException(status_code=404, detail="Forecast not found")

    forecast_data = running_forecasts[forecast_id]
    return ForecastStatus(
        forecast_id=forecast_id,
        status=forecast_data["status"],
        progress=forecast_data["progress"],
        result=forecast_data["result"],
        error=forecast_data["error"]
    )

# Excel export endpoint
@app.get("/api/forecast/{forecast_id}/excel")
async def download_excel_report(forecast_id: str):
    """Download Excel report for a completed forecast"""
    if forecast_id not in running_forecasts:
        raise HTTPException(status_code=404, detail="Forecast not found")

    forecast_data = running_forecasts[forecast_id]
    if forecast_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Forecast not completed")

    try:
        # Generate Excel file
        exporter = ExcelExporter()
        excel_content = exporter.generate_report(forecast_data["result"])

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(excel_content)
            tmp_file_path = tmp_file.name

        # Return file
        return FileResponse(
            tmp_file_path,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            filename=f"forecast_{forecast_id}.xlsx"
        )

    except Exception as e:
        logger.error(f"Error generating Excel report: {e}")
        raise HTTPException(status_code=500, detail="Error generating report")

# Forecast cancellation endpoint
@app.post("/api/forecast/{forecast_id}/cancel")
async def cancel_forecast(forecast_id: str):
    """Cancel a running forecast"""
    if forecast_id not in running_forecasts:
        raise HTTPException(status_code=404, detail="Forecast not found")

    running_forecasts[forecast_id]["status"] = "cancelled"
    return {"message": "Forecast cancelled"}

# Background forecast execution
async def run_forecast(
    forecast_id: str,
    question: str,
    definition: str,
    timeframe: str,
    iterations: int,
    models: Optional[List[str]] = None
):
    """Execute the actual forecast using the real AI system"""
    try:
        # Update progress
        running_forecasts[forecast_id]["progress"] = 10

        # Initialize components
        client = OpenRouterClient()
        manager = EnsembleManager(client)

        # Get enabled models
        if models is None:
            enabled_models = settings.get('ENABLED_MODELS', '').split(',')
            models = [model.strip() for model in enabled_models if model.strip()]

        # Update progress
        running_forecasts[forecast_id]["progress"] = 20

        # Generate prompts
        prompt = PromptTemplates.get_super_forecaster_prompt(
            question=question,
            definition=definition,
            timeframe=timeframe
        )

        # Update progress
        running_forecasts[forecast_id]["progress"] = 30

        # Run forecasting for each model
        model_results = []
        total_models = len(models)

        for i, model in enumerate(models):
            if running_forecasts[forecast_id]["status"] == "cancelled":
                return

            try:
                logger.info(f"Running forecast for model: {model}")

                # Query model
                result = await client.query_model(
                    model=model,
                    prompt=prompt,
                    max_tokens=1000,
                    enable_web_search=True
                )

                if result.get('probability') is not None:
                    model_results.append({
                        'model': model,
                        'probability': result['probability'],
                        'content': result.get('content', ''),
                        'status': result.get('status', 'success')
                    })

                # Update progress
                progress = 30 + int((i + 1) / total_models * 50)
                running_forecasts[forecast_id]["progress"] = progress

            except Exception as e:
                logger.error(f"Error with model {model}: {e}")
                model_results.append({
                    'model': model,
                    'probability': None,
                    'error': str(e),
                    'status': 'error'
                })

        # Update progress
        running_forecasts[forecast_id]["progress"] = 85

        # Calculate ensemble statistics
        valid_results = [r for r in model_results if r.get('probability') is not None]

        if not valid_results:
            raise Exception("No valid model results obtained")

        # Calculate ensemble probability
        probabilities = [r['probability'] for r in valid_results]
        ensemble_prob = calculate_ensemble_probability(probabilities)

        # Calculate model statistics
        model_stats = {}
        for result in valid_results:
            model_stats[result['model']] = {
                'mean': result['probability'],
                'status': result['status']
            }

        # Create final result
        forecast_result = {
            'ensemble_probability': round(ensemble_prob, 1),
            'statistics': {
                'successful_queries': len(valid_results),
                'total_queries': len(models),
                'models_used': [r['model'] for r in valid_results],
                'model_stats': model_stats
            },
            'question': question,
            'definition': definition,
            'timeframe': timeframe,
            'iterations': iterations,
            'generated_at': datetime.now().isoformat(),
            'detailed_results': model_results
        }

        # Update final status
        running_forecasts[forecast_id].update({
            "status": "completed",
            "progress": 100,
            "result": forecast_result,
            "end_time": datetime.now()
        })

        logger.info(f"Forecast {forecast_id} completed successfully")

    except Exception as e:
        logger.error(f"Forecast {forecast_id} failed: {e}")
        running_forecasts[forecast_id].update({
            "status": "failed",
            "error": str(e),
            "end_time": datetime.now()
        })

# Simplified endpoint for direct web interface compatibility
@app.post("/forecast", response_model=ForecastResponse)
async def create_forecast_simple(request: ForecastRequest):
    """Simplified forecast endpoint for web interface"""
    try:
        # For web interface, we'll run a quick forecast synchronously
        client = OpenRouterClient()

        # Get enabled models (limit to 3 for quick response)
        enabled_models = settings.get('ENABLED_MODELS', '').split(',')
        models = [model.strip() for model in enabled_models[:3] if model.strip()]

        # Generate prompt
        prompt = PromptTemplates.get_super_forecaster_prompt(
            question=request.question,
            definition=request.definition or "",
            timeframe=request.timeframe or "2026"
        )

        # Run quick forecast
        model_results = []
        for model in models:
            try:
                result = await client.query_model(
                    model=model,
                    prompt=prompt,
                    max_tokens=800,
                    enable_web_search=True
                )

                if result.get('probability') is not None:
                    model_results.append({
                        'model': model,
                        'probability': result['probability'],
                        'status': result.get('status', 'success')
                    })
            except Exception as e:
                logger.error(f"Error with model {model}: {e}")

        # Calculate result
        if not model_results:
            return ForecastResponse(
                success=False,
                error="No valid model results obtained"
            )

        probabilities = [r['probability'] for r in model_results]
        ensemble_prob = sum(probabilities) / len(probabilities)

        # Create model stats
        model_stats = {}
        for result in model_results:
            model_stats[result['model']] = {
                'mean': result['probability']
            }

        forecast_result = {
            'ensemble_probability': round(ensemble_prob, 1),
            'statistics': {
                'successful_queries': len(model_results),
                'models_used': [r['model'] for r in model_results],
                'model_stats': model_stats
            },
            'question': request.question,
            'timeframe': request.timeframe or "2026",
            'generated_at': datetime.now().isoformat()
        }

        return ForecastResponse(
            success=True,
            result=forecast_result
        )

    except Exception as e:
        logger.error(f"Error in quick forecast: {e}")
        return ForecastResponse(
            success=False,
            error=str(e)
        )

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("🚀 Foresight Analyzer API starting up...")
    logger.info(f"📊 Enabled models: {settings.get('ENABLED_MODELS', '')}")
    logger.info(f"🔧 Iterations per model: {settings.get('ITERATIONS_PER_MODEL', 5)}")
    logger.info(f"⚡ Concurrent requests: {settings.get('CONCURRENT_REQUESTS', 3)}")
    logger.info(f"🕐 Request timeout: {settings.get('REQUEST_TIMEOUT', 120)}s")

    # Test OpenRouter API connectivity
    try:
        client = OpenRouterClient()
        logger.info("✅ OpenRouter client initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize OpenRouter client: {e}")

    logger.info("🎯 API endpoints available:")
    logger.info("   📍 Root: /")
    logger.info("   💚 Health: /health")
    logger.info("   🤖 Models: /api/models")
    logger.info("   🔮 Forecast: /api/forecast")
    logger.info("   📚 Docs: /docs")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("🛑 Foresight Analyzer API shutting down...")
    logger.info("🧹 Cleaning up running forecasts...")

    # Cancel any running forecasts
    for forecast_id in list(running_forecasts.keys()):
        if running_forecasts[forecast_id]["status"] == "running":
            running_forecasts[forecast_id]["status"] = "cancelled"
            logger.info(f"   ❌ Cancelled forecast: {forecast_id}")

    logger.info("✅ Shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)