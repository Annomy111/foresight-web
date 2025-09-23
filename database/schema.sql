-- Neon PostgreSQL Schema for Foresight Analyzer
-- Created: 2025-09-22

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (optional, for user management)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    api_key_encrypted TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Forecasts table - main forecast metadata
CREATE TABLE IF NOT EXISTS forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    definition TEXT,
    timeframe VARCHAR(100),
    forecast_type VARCHAR(50) DEFAULT 'custom',
    status VARCHAR(20) DEFAULT 'pending',
    ensemble_probability FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    excel_url TEXT,
    total_queries INT DEFAULT 0,
    successful_queries INT DEFAULT 0,
    failed_queries INT DEFAULT 0,
    metadata JSONB
);

-- Model responses table - individual AI model responses
CREATE TABLE IF NOT EXISTS model_responses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    forecast_id UUID NOT NULL REFERENCES forecasts(id) ON DELETE CASCADE,
    model VARCHAR(100) NOT NULL,
    iteration INT NOT NULL,
    ensemble_id VARCHAR(100),
    status VARCHAR(20) NOT NULL,
    probability FLOAT,
    content TEXT,
    response_time FLOAT,
    token_usage JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Forecast statistics table - aggregated statistics
CREATE TABLE IF NOT EXISTS forecast_statistics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    forecast_id UUID UNIQUE NOT NULL REFERENCES forecasts(id) ON DELETE CASCADE,
    mean_probability FLOAT,
    median_probability FLOAT,
    std_deviation FLOAT,
    min_probability FLOAT,
    max_probability FLOAT,
    confidence_interval_lower FLOAT,
    confidence_interval_upper FLOAT,
    model_stats JSONB,
    consensus_strength FLOAT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API keys table - for managing user API keys
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(100),
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

-- Forecast templates table - for saving custom forecast templates
CREATE TABLE IF NOT EXISTS forecast_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    definition TEXT,
    timeframe VARCHAR(100),
    models TEXT[],
    iterations_per_model INT DEFAULT 10,
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled forecasts table - for recurring forecasts
CREATE TABLE IF NOT EXISTS scheduled_forecasts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id UUID NOT NULL REFERENCES forecast_templates(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cron_expression VARCHAR(100),
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_run_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Forecast shares table - for sharing forecasts
CREATE TABLE IF NOT EXISTS forecast_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    forecast_id UUID NOT NULL REFERENCES forecasts(id) ON DELETE CASCADE,
    share_token VARCHAR(100) UNIQUE NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE,
    access_count INT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_forecasts_user_id ON forecasts(user_id);
CREATE INDEX idx_forecasts_status ON forecasts(status);
CREATE INDEX idx_forecasts_created_at ON forecasts(created_at DESC);
CREATE INDEX idx_model_responses_forecast_id ON model_responses(forecast_id);
CREATE INDEX idx_model_responses_model ON model_responses(model);
CREATE INDEX idx_forecast_shares_token ON forecast_shares(share_token);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE
    ON users FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();

CREATE TRIGGER update_forecast_templates_updated_at BEFORE UPDATE
    ON forecast_templates FOR EACH ROW EXECUTE PROCEDURE update_updated_at_column();