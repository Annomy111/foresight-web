/**
 * Direct OpenRouter Integration for Netlify
 * No backend needed - runs entirely on Netlify Functions!
 */

const API_KEY = process.env.OPENROUTER_API_KEY || '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';

// Models that work with the new API key
const MODELS = [
  'x-ai/grok-4-fast:free',
  'google/gemini-2.0-flash-exp:free',
  'qwen/qwen-2.5-72b-instruct:free'
];

// Rate limiting configuration
const DELAY_BETWEEN_REQUESTS = 5000; // 5 seconds
const MAX_RETRIES = 2;
const ITERATIONS_PER_MODEL = 3;

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function queryModel(model, question, definition, timeframe) {
  const prompt = `You are an expert forecaster analyzing future probabilities.

Question: ${question}
${definition ? `Definition: ${definition}` : ''}
Timeframe: By ${timeframe}

Provide your forecast as a single probability percentage (0-100) with brief reasoning.
Format your response as:
PROBABILITY: [number]%
REASONING: [brief explanation]`;

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://foresight-analyzer.netlify.app',
        'X-Title': 'Foresight Analyzer'
      },
      body: JSON.stringify({
        model: model,
        messages: [
          {
            role: 'system',
            content: 'You are an expert forecaster. Always provide probabilities between 0-100%.'
          },
          {
            role: 'user',
            content: prompt
          }
        ],
        max_tokens: 200,
        temperature: 0.7
      })
    });

    if (!response.ok) {
      const error = await response.json();
      console.error(`Model ${model} error:`, error);
      return null;
    }

    const data = await response.json();
    const content = data.choices?.[0]?.message?.content || '';

    // Parse probability from response
    const probMatch = content.match(/PROBABILITY:\s*(\d+(?:\.\d+)?)/i);
    const probability = probMatch ? parseFloat(probMatch[1]) : null;

    const reasoningMatch = content.match(/REASONING:\s*(.+)/i);
    const reasoning = reasoningMatch ? reasoningMatch[1].trim() : content.substring(0, 100);

    if (probability !== null) {
      return {
        model: model.split('/')[1].split(':')[0],
        probability,
        reasoning,
        raw_response: content
      };
    }

    return null;
  } catch (error) {
    console.error(`Error with model ${model}:`, error.message);
    return null;
  }
}

async function runEnsembleForecast(question, definition, timeframe, iterations) {
  const results = [];

  for (const model of MODELS) {
    console.log(`Querying ${model}...`);

    for (let i = 0; i < Math.min(iterations, ITERATIONS_PER_MODEL); i++) {
      const result = await queryModel(model, question, definition, timeframe);

      if (result) {
        results.push(result);
      }

      // Rate limiting delay
      if (i < iterations - 1 || model !== MODELS[MODELS.length - 1]) {
        await sleep(DELAY_BETWEEN_REQUESTS);
      }
    }
  }

  return results;
}

function calculateEnsembleResult(results) {
  if (results.length === 0) {
    return null;
  }

  const probabilities = results.map(r => r.probability);
  const mean = probabilities.reduce((a, b) => a + b, 0) / probabilities.length;
  const median = probabilities.sort((a, b) => a - b)[Math.floor(probabilities.length / 2)];

  // Calculate standard deviation
  const variance = probabilities.reduce((acc, p) => acc + Math.pow(p - mean, 2), 0) / probabilities.length;
  const stdDev = Math.sqrt(variance);

  // Determine confidence
  let confidence = 'Medium';
  if (stdDev < 10) confidence = 'High';
  else if (stdDev > 20) confidence = 'Low';

  return {
    probability: Math.round(mean * 10) / 10,
    median_probability: median,
    std_deviation: Math.round(stdDev * 10) / 10,
    confidence,
    total_models: results.length,
    model_breakdown: results.map(r => ({
      model: r.model,
      probability: r.probability
    })),
    all_results: results
  };
}

exports.handler = async (event, context) => {
  // CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
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
    const { question, definition, timeframe, iterations = 1 } = JSON.parse(event.body);

    if (!question || !timeframe) {
      return {
        statusCode: 400,
        headers,
        body: JSON.stringify({
          success: false,
          error: 'Question and timeframe are required'
        })
      };
    }

    console.log(`Starting forecast: "${question}" by ${timeframe}`);

    // Run ensemble forecast
    const results = await runEnsembleForecast(question, definition, timeframe, iterations);

    if (results.length === 0) {
      return {
        statusCode: 200,
        headers,
        body: JSON.stringify({
          success: false,
          error: 'No valid model results obtained'
        })
      };
    }

    const ensembleResult = calculateEnsembleResult(results);

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        forecast_id: `forecast_${Date.now()}`,
        result: ensembleResult
      })
    };

  } catch (error) {
    console.error('Forecast error:', error);
    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        success: false,
        error: error.message || 'Internal server error'
      })
    };
  }
};