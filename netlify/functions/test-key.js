exports.handler = async (event, context) => {
  const API_KEY = process.env.OPENROUTER_API_KEY || 'NO_KEY_SET';

  // Test the API key
  const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
      'HTTP-Referer': 'https://foresight-analyzer.netlify.app',
      'X-Title': 'Test'
    },
    body: JSON.stringify({
      model: 'x-ai/grok-4-fast:free',
      messages: [{ role: 'user', content: 'Say test' }],
      max_tokens: 10
    })
  });

  const data = await response.json();

  return {
    statusCode: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      api_key_first_chars: API_KEY.substring(0, 20),
      api_key_last_chars: API_KEY.substring(API_KEY.length - 10),
      response_status: response.status,
      response_data: data
    })
  };
};