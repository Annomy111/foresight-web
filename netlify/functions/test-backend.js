// Netlify Function for testing backend connectivity and configuration
const https = require('https');

// Backend URL
const BACKEND_URL = process.env.BACKEND_URL || 'https://foresight-backend-api.onrender.com';

exports.handler = async (event, context) => {
  // CORS headers
  const headers = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Allow-Methods': 'GET, OPTIONS',
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

  console.log('🧪 Testing backend connectivity...');

  const diagnostics = {
    timestamp: new Date().toISOString(),
    environment: {
      BACKEND_URL: BACKEND_URL,
      hasBackendUrl: !!process.env.BACKEND_URL,
      usesFallback: process.env.USE_FALLBACK !== 'false',
      nodeVersion: process.version,
      platform: process.platform
    },
    tests: {}
  };

  try {
    // Test 1: Backend root endpoint
    console.log('📍 Test 1: Checking backend root endpoint...');
    try {
      const rootResponse = await fetch(BACKEND_URL);
      const rootData = await rootResponse.json();

      diagnostics.tests.rootEndpoint = {
        success: true,
        status: rootResponse.status,
        data: rootData
      };
      console.log('✅ Root endpoint accessible');
    } catch (error) {
      diagnostics.tests.rootEndpoint = {
        success: false,
        error: error.message
      };
      console.error('❌ Root endpoint failed:', error.message);
    }

    // Test 2: Backend health check
    console.log('📍 Test 2: Checking backend health...');
    try {
      const healthResponse = await fetch(`${BACKEND_URL}/health`);
      const healthData = await healthResponse.json();

      diagnostics.tests.healthCheck = {
        success: true,
        status: healthResponse.status,
        data: healthData
      };
      console.log('✅ Health check passed');
    } catch (error) {
      diagnostics.tests.healthCheck = {
        success: false,
        error: error.message
      };
      console.error('❌ Health check failed:', error.message);
    }

    // Test 3: Models endpoint
    console.log('📍 Test 3: Checking models endpoint...');
    try {
      const modelsResponse = await fetch(`${BACKEND_URL}/api/models`);
      const modelsData = await modelsResponse.json();

      diagnostics.tests.modelsEndpoint = {
        success: true,
        status: modelsResponse.status,
        modelsCount: modelsData.models ? modelsData.models.length : 0,
        models: modelsData.models || []
      };
      console.log('✅ Models endpoint accessible, found', modelsData.models?.length || 0, 'models');
    } catch (error) {
      diagnostics.tests.modelsEndpoint = {
        success: false,
        error: error.message
      };
      console.error('❌ Models endpoint failed:', error.message);
    }

    // Test 4: Quick forecast test
    console.log('📍 Test 4: Testing forecast endpoint...');
    try {
      const forecastResponse = await fetch(`${BACKEND_URL}/forecast`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: 'Test question from Netlify debug',
          definition: '',
          timeframe: '2026',
          iterations: 1
        })
      });

      const forecastData = await forecastResponse.json();

      diagnostics.tests.forecastEndpoint = {
        success: forecastResponse.ok,
        status: forecastResponse.status,
        hasResult: !!forecastData.result,
        probability: forecastData.result?.ensemble_probability,
        modelsUsed: forecastData.result?.statistics?.models_used?.length || 0
      };

      if (forecastResponse.ok) {
        console.log('✅ Forecast endpoint working, probability:', forecastData.result?.ensemble_probability);
      } else {
        console.log('⚠️ Forecast endpoint returned error:', forecastData);
      }
    } catch (error) {
      diagnostics.tests.forecastEndpoint = {
        success: false,
        error: error.message
      };
      console.error('❌ Forecast endpoint failed:', error.message);
    }

    // Overall status
    const allTestsPassed = Object.values(diagnostics.tests).every(test => test.success);
    diagnostics.overallStatus = allTestsPassed ? 'HEALTHY' : 'ISSUES_DETECTED';

    console.log('🔍 Diagnostics complete:', diagnostics.overallStatus);

    return {
      statusCode: 200,
      headers,
      body: JSON.stringify({
        success: true,
        diagnostics,
        recommendations: generateRecommendations(diagnostics)
      }, null, 2)
    };

  } catch (error) {
    console.error('❌ Test function error:', error);

    return {
      statusCode: 500,
      headers,
      body: JSON.stringify({
        success: false,
        error: error.message,
        diagnostics
      }, null, 2)
    };
  }
};

function generateRecommendations(diagnostics) {
  const recommendations = [];

  if (!diagnostics.environment.hasBackendUrl) {
    recommendations.push({
      priority: 'HIGH',
      issue: 'BACKEND_URL not set',
      action: 'Add BACKEND_URL environment variable in Netlify dashboard',
      value: 'https://foresight-backend-api.onrender.com'
    });
  }

  if (!diagnostics.tests.rootEndpoint?.success) {
    recommendations.push({
      priority: 'HIGH',
      issue: 'Backend not accessible',
      action: 'Check if backend is deployed and running at ' + diagnostics.environment.BACKEND_URL
    });
  }

  if (!diagnostics.tests.forecastEndpoint?.success) {
    recommendations.push({
      priority: 'HIGH',
      issue: 'Forecast endpoint not working',
      action: 'Check backend logs and OpenRouter API key configuration'
    });
  }

  if (diagnostics.tests.modelsEndpoint?.modelsCount === 0) {
    recommendations.push({
      priority: 'MEDIUM',
      issue: 'No models configured',
      action: 'Check ENABLED_MODELS environment variable in backend'
    });
  }

  if (recommendations.length === 0) {
    recommendations.push({
      priority: 'INFO',
      issue: 'None',
      action: 'All systems operational!'
    });
  }

  return recommendations;
}