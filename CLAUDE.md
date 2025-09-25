# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Development
- `npm run dev` - Start Next.js development server (default port 3000)
- `npm run build` - Build production bundle for deployment
- `npm run start` - Start production server
- `npm run lint` - Run Next.js ESLint checks

### Testing
- `npm test` - Run comprehensive test suite via test-runner.js
- `npm run test:unit` - Run Jest unit tests
- `npm run test:e2e` - Run Playwright end-to-end tests
- `npm run test:accessibility` - Run accessibility tests with Playwright
- `npm run test:api` - Run API integration tests
- `npm run test:performance` - Run Lighthouse performance audit
- `npm run test:load` - Run Artillery load testing
- `npm run test:quick` - Run quick test subset
- `npm run test:ci` - Run CI test suite (skips load tests)
- `npm run test:coverage` - Run Jest with code coverage
- `npm run test:watch` - Run Jest in watch mode
- `npm run playwright:ui` - Open Playwright test UI
- `npm run playwright:install` - Install Playwright browsers

### Python Backend (from backend/ directory)
- `pip install -r requirements.txt` - Install Python dependencies
- `uvicorn main:app --reload` - Run FastAPI development server
- `python test_openrouter_key.py` - Test OpenRouter API configuration

## Architecture

### Stack Overview
This is a **Next.js 14** web application with a **FastAPI Python backend** for AI-powered probabilistic forecasting. The app is designed for deployment on **Netlify** (frontend) with serverless functions proxying to a Python backend service.

### Key Directories

**Frontend (Next.js)**
- `src/app/` - Next.js 14 app directory with React Server Components
- `src/lib/` - Shared TypeScript utilities, API clients, and type definitions
- `.next/` - Built production output (gitignored)

**Backend (Python FastAPI)**
- `backend/main.py` - FastAPI application entry point with forecast endpoints
- `backend/core/` - Core forecasting engine (API client, ensemble manager, statistics)
- `backend/config/` - Configuration, prompts, and model settings
- `backend/services/` - Business logic services
- `backend/analysis/` - Forecast aggregation and analysis
- `backend/export/` - Excel report generation

**Serverless & Deployment**
- `netlify/functions/` - Netlify Functions (Node.js serverless endpoints)
- `netlify.toml` - Netlify deployment configuration

**Testing Infrastructure**
- `tests/runner/test-runner.js` - Orchestrates all test suites
- `tests/e2e/` - Playwright end-to-end tests
- `tests/unit/` - Jest unit tests
- `tests/performance/` - Lighthouse and Artillery performance tests
- `tests/reports/` - Test output and coverage reports

### Core Architecture Patterns

**AI Forecasting System**: The backend implements an ensemble forecasting approach using multiple LLMs via OpenRouter API. The `EnsembleManager` orchestrates parallel predictions from multiple models, which are then aggregated using statistical methods to produce probabilistic forecasts.

**API Communication Flow**:
1. Frontend (Next.js) → Netlify Function (`/.netlify/functions/forecast`)
2. Netlify Function → Python FastAPI backend (`/api/forecast/start`)
3. Backend processes forecast using ensemble of AI models
4. Results returned through same chain

**Key Components**:
- **OpenRouterClient** (`backend/core/api_client.py`): Manages LLM API interactions
- **EnsembleManager** (`backend/core/ensemble_manager.py`): Orchestrates multiple model predictions
- **ForecastAggregator** (`backend/analysis/aggregator.py`): Combines and analyzes predictions
- **ExcelExporter** (`backend/export/excel_exporter.py`): Generates detailed Excel reports

### Environment Configuration

Required environment variables:
- `OPENROUTER_API_KEY` - OpenRouter API key for LLM access
- `BACKEND_URL` - Python backend URL (for Netlify functions)
- `NEXT_PUBLIC_API_URL` - Frontend API base URL

Models are configured in backend via `ENABLED_MODELS` environment variable listing comma-separated model IDs.

### Testing Strategy

The test suite (`tests/runner/test-runner.js`) orchestrates multiple testing frameworks:
- **Unit tests**: Jest for React components and utilities
- **E2E tests**: Playwright for user workflows
- **API tests**: Integration tests for backend endpoints
- **Performance**: Lighthouse audits and Artillery load tests

Test reports are generated in `tests/reports/` with HTML output for easy review.

### Deployment Notes

The application is configured for Netlify deployment with:
- Automatic builds on git push
- Serverless functions for API proxying
- Environment variables configured in Netlify dashboard
- Static asset optimization via Next.js

Backend can be deployed separately to services like Render or Railway, with the Netlify function proxying requests.