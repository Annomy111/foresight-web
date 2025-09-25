// Netlify Function for Excel export - Proxy to Python FastAPI backend
const https = require('https');

// Backend URL - same as forecast function
const BACKEND_URL = process.env.BACKEND_URL || 'https://foresight-backend-api.onrender.com';

console.log('📊 Excel export function initialized with backend:', BACKEND_URL);

exports.handler = async (event, context) => {
  // CORS headers for Excel download
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
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
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Method not allowed' })
    };
  }

  try {
    const body = JSON.parse(event.body);
    const { forecast_id, forecast_data } = body;

    console.log('📤 Requesting Excel export from backend...');
    console.log('Forecast ID:', forecast_id || 'current');

    // Determine the endpoint
    const endpoint = forecast_id
      ? `${BACKEND_URL}/api/forecast/${forecast_id}/excel`
      : `${BACKEND_URL}/api/forecast/current/excel`;

    // If we have forecast data, send it as POST
    // Otherwise, use GET for existing forecast
    const options = forecast_data ? {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(forecast_data)
    } : {
      method: 'GET'
    };

    console.log('🔄 Fetching from:', endpoint);
    const response = await fetch(endpoint, options);

    console.log('📥 Backend response status:', response.status);
    console.log('📥 Content-Type:', response.headers.get('content-type'));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend error:', errorText);
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    // Check if response is Excel file
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('spreadsheet')) {
      // If not Excel, might be JSON error
      const data = await response.json();
      console.error('⚠️ Unexpected response type:', data);

      return {
        statusCode: 400,
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          success: false,
          error: data.error || 'Failed to generate Excel file'
        })
      };
    }

    // Get the binary data
    const buffer = await response.arrayBuffer();
    const base64 = Buffer.from(buffer).toString('base64');

    console.log('✅ Excel file received, size:', buffer.byteLength, 'bytes');

    // Return Excel file as base64
    return {
      statusCode: 200,
      headers: {
        ...headers,
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': `attachment; filename="foresight_analysis_${new Date().toISOString().split('T')[0]}.xlsx"`,
      },
      body: base64,
      isBase64Encoded: true
    };

  } catch (error) {
    console.error('❌ Excel export error:', error.message);
    console.error('Stack:', error.stack);

    // Generate mock Excel data for fallback
    if (process.env.USE_FALLBACK !== 'false') {
      console.log('⚠️ Using mock Excel response');

      // Create a simple CSV as fallback (not real Excel but can be opened)
      const mockCSV = `Foresight Analysis Report
Generated: ${new Date().toISOString()}

Question,Probability,Models Used,Status
"Sample forecast",45.2%,3,Mock Data

Note: This is mock data - backend service unavailable`;

      const base64CSV = Buffer.from(mockCSV).toString('base64');

      return {
        statusCode: 200,
        headers: {
          ...headers,
          'Content-Type': 'text/csv',
          'Content-Disposition': 'attachment; filename="foresight_analysis_mock.csv"',
        },
        body: base64CSV,
        isBase64Encoded: true
      };
    }

    return {
      statusCode: 500,
      headers: { ...headers, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        success: false,
        error: 'Failed to generate Excel export',
        details: error.message
      })
    };
  }
};