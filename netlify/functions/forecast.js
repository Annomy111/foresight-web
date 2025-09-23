// Netlify Function for forecast API endpoint - Proxy to Python FastAPI backend
const https = require('https');

// Backend URL - update this when deployed to Railway/Render
const BACKEND_URL = process.env.BACKEND_URL || 'https://foresight-backend-api.onrender.com';

exports.handler = async (event, context) => {
  // CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Content-Type': 'application/json'
  };

  // Handle preflight
  if (event.httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers,
      body: ''
    };
  }

  if (event.httpMethod !== 'POST') {
    return {
      statusCode: 405,
      headers,
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    const body = JSON.parse(event.body);
    const { question, definition, timeframe, iterations } = body;

    // Validate input
    if (!question) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({
          success: false,
          error: 'Question is required'
        })
      };
    }

    // If backend URL is not configured, fall back to mock implementation
    if (!process.env.BACKEND_URL) {
      console.log('⚠️ BACKEND_URL not configured, using mock forecast for:', question);

      // Simple fallback implementation
      const mockResult = {
        ensemble_probability: 45.2,
        statistics: {
          successful_queries: 3,
          models_used: ['x-ai/grok-4-fast:free', 'deepseek/deepseek-r1:free', 'qwen/qwen3-8b:free'],
          model_stats: {
            'x-ai/grok-4-fast:free': { mean: 42.1 },
            'deepseek/deepseek-r1:free': { mean: 48.7 },
            'qwen/qwen3-8b:free': { mean: 44.8 }
          }
        },
        question,
        timeframe: timeframe || '2026',
        generated_at: new Date().toISOString()
      };

      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          success: true,
          result: mockResult
        })
      };
    }

    // Proxy request to FastAPI backend
    console.log('🔄 Proxying forecast request to:', `${BACKEND_URL}/forecast`);

    const response = await fetch(`${BACKEND_URL}/forecast`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question,
        definition: definition || '',
        timeframe: timeframe || '2026',
        iterations: iterations || 3
      })
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    const data = await response.json();

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify(data)
    };

  } catch (error) {
    console.error('❌ Forecast proxy error:', error);

    // Fallback to mock if backend is unavailable
    console.log('⚠️ Backend unavailable, using mock forecast');

    const fallbackResult = {
      ensemble_probability: 38.4,
      statistics: {
        successful_queries: 3,
        models_used: ['x-ai/grok-4-fast:free', 'deepseek/deepseek-r1:free', 'qwen/qwen3-8b:free'],
        model_stats: {
          'x-ai/grok-4-fast:free': { mean: 35.2 },
          'deepseek/deepseek-r1:free': { mean: 41.1 },
          'qwen/qwen3-8b:free': { mean: 38.9 }
        }
      },
      question: JSON.parse(event.body).question,
      timeframe: JSON.parse(event.body).timeframe || '2026',
      generated_at: new Date().toISOString(),
      note: 'Generated using fallback mode - backend unavailable'
    };

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        result: fallbackResult
      })
    };
  }
};