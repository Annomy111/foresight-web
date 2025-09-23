// TypeScript types for Foresight Analyzer

export interface ForecastRequest {
  question: string;
  definition?: string;
  timeframe?: string;
  models?: string[];
  iterations_per_model?: number;
  user_id?: string;
}

export interface ForecastResponse {
  forecast_id: string;
  status: string;
  message: string;
  forecast_url?: string;
}

export interface ForecastStatus {
  forecast_id: string;
  status: 'pending' | 'running' | 'completed' | 'error' | 'cancelled';
  progress: number;
  current_model?: string;
  completed_queries: number;
  total_queries: number;
  ensemble_probability?: number;
  excel_url?: string;
  error?: string;
}

export interface ModelResponse {
  model: string;
  iteration: number;
  ensemble_id: string;
  timestamp: string;
  response_time: number;
  status: 'success' | 'error' | 'timeout' | 'rate_limited';
  content?: string;
  probability?: number;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  error?: string;
}

export interface ModelStatistics {
  model: string;
  count: number;
  mean: number;
  median: number;
  std: number;
  min: number;
  max: number;
  success_rate: number;
}

export interface EnsembleStatistics {
  total_queries: number;
  successful_queries: number;
  failed_queries: number;
  valid_probabilities: number;
  models_used: string[];
  mean?: number;
  median?: number;
  std?: number;
  min?: number;
  max?: number;
  model_stats: Record<string, ModelStatistics>;
}

export interface ForecastResult {
  question: string;
  definition?: string;
  timeframe?: string;
  responses: ModelResponse[];
  statistics: EnsembleStatistics;
  timestamp: string;
}

export interface Model {
  id: string;
  name: string;
  provider: string;
  isFree: boolean;
  selected?: boolean;
}

export interface WebSocketUpdate {
  type: 'progress' | 'model_update' | 'completed' | 'error' | 'heartbeat';
  forecast_id?: string;
  progress?: number;
  model?: string;
  message?: string;
  ensemble_probability?: number;
  excel_url?: string;
  error?: string;
}

export interface ChartDataPoint {
  model: string;
  probability: number;
  count: number;
}

export const AVAILABLE_MODELS: Model[] = [
  // Free models
  { id: 'x-ai/grok-4-fast:free', name: 'Grok-4 Fast', provider: 'X-AI', isFree: true },
  { id: 'deepseek/deepseek-r1:free', name: 'DeepSeek R1', provider: 'DeepSeek', isFree: true },
  { id: 'qwen/qwen3-8b:free', name: 'Qwen 3 (8B)', provider: 'Alibaba', isFree: true },
  { id: 'google/gemma-2-9b-it:free', name: 'Gemma 2 (9B)', provider: 'Google', isFree: true },
  { id: 'meta-llama/llama-3.2-3b-instruct:free', name: 'Llama 3.2 (3B)', provider: 'Meta', isFree: true },
  { id: 'qwen/qwen-2.5-72b-instruct:free', name: 'Qwen 2.5 (72B)', provider: 'Alibaba', isFree: true },
  { id: 'qwen/qwen-2.5-coder-32b-instruct:free', name: 'Qwen Coder (32B)', provider: 'Alibaba', isFree: true },
  { id: 'meta-llama/llama-4-maverick:free', name: 'Llama 4 Maverick', provider: 'Meta', isFree: true },
  // Premium models
  { id: 'google/gemini-2.5-pro-preview', name: 'Gemini 2.5 Pro', provider: 'Google', isFree: false },
  { id: 'openai/gpt-5-chat', name: 'GPT-5', provider: 'OpenAI', isFree: false },
  { id: 'anthropic/claude-opus-4.1', name: 'Claude Opus 4.1', provider: 'Anthropic', isFree: false },
  { id: 'x-ai/grok-4', name: 'Grok-4', provider: 'X-AI', isFree: false },
  { id: 'deepseek/deepseek-chat-v3.1', name: 'DeepSeek Chat v3.1', provider: 'DeepSeek', isFree: false },
];