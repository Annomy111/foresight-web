const fetch = (...args) => import('node-fetch').then(({default: fetch}) => fetch(...args));

async function diagnoseIssue() {
  console.log('🔍 Diagnostic Test Starting\n');
  console.log('=====================================\n');

  // Test 1: Backend Health Check
  console.log('1️⃣ Testing Backend Health Directly...');
  try {
    const healthResponse = await fetch('https://foresight-backend-api.onrender.com/health', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    const healthData = await healthResponse.text();
    console.log('   Status:', healthResponse.status);
    console.log('   Response:', healthData);

    if (healthResponse.ok) {
      console.log('   ✅ Backend is healthy\n');
    } else {
      console.log('   ❌ Backend health check failed\n');
    }
  } catch (error) {
    console.log('   ❌ Backend unreachable:', error.message);
    console.log('   Note: Backend might be sleeping (Render free tier)\n');
  }

  // Test 2: Direct Backend Forecast
  console.log('2️⃣ Testing Backend Forecast Directly...');
  try {
    const forecastResponse = await fetch('https://foresight-backend-api.onrender.com/forecast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: "Will AI impact jobs by 2026?",
        definition: "Test definition",
        timeframe: "2026",
        iterations: 1
      })
    });

    const forecastData = await forecastResponse.json();
    console.log('   Status:', forecastResponse.status);
    console.log('   Success:', forecastData.success);

    if (forecastData.error) {
      console.log('   Error:', forecastData.error);
    }

    if (forecastData.result) {
      console.log('   Has Result:', !!forecastData.result);
      console.log('   Ensemble Probability:', forecastData.result.ensemble_probability);
    }

    if (forecastResponse.ok && forecastData.success) {
      console.log('   ✅ Backend forecast works\n');
    } else {
      console.log('   ❌ Backend forecast failed\n');
      console.log('   Full response:', JSON.stringify(forecastData, null, 2));
    }
  } catch (error) {
    console.log('   ❌ Backend forecast error:', error.message, '\n');
  }

  // Test 3: Netlify Function
  console.log('3️⃣ Testing Netlify Function...');
  try {
    const netlifyResponse = await fetch('https://foresight-analyzer.netlify.app/.netlify/functions/forecast', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: "Will AI impact jobs by 2026?",
        definition: "Test definition",
        timeframe: "2026",
        iterations: 1
      })
    });

    const netlifyData = await netlifyResponse.json();
    console.log('   Status:', netlifyResponse.status);
    console.log('   Success:', netlifyData.success);

    if (netlifyData.result) {
      console.log('   Has Result:', !!netlifyData.result);
      console.log('   Ensemble Probability:', netlifyData.result.ensemble_probability);

      if (netlifyData.result.note) {
        console.log('   Note:', netlifyData.result.note);
      }

      // Check if it's using mock data
      if (netlifyData.result.note && netlifyData.result.note.includes('fallback')) {
        console.log('   ⚠️  Using fallback mock data!');
      }
    }

    if (netlifyResponse.ok) {
      console.log('   ✅ Netlify function responds\n');
    } else {
      console.log('   ❌ Netlify function failed\n');
    }
  } catch (error) {
    console.log('   ❌ Netlify function error:', error.message, '\n');
  }

  // Test 4: Check Backend Environment
  console.log('4️⃣ Checking Backend Configuration...');
  try {
    const configResponse = await fetch('https://foresight-backend-api.onrender.com/debug/config', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    });

    if (configResponse.ok) {
      const configData = await configResponse.json();
      console.log('   Config received:', JSON.stringify(configData, null, 2));
    } else {
      console.log('   Debug endpoint not available (status:', configResponse.status + ')');
    }
  } catch (error) {
    console.log('   Debug endpoint error:', error.message);
  }

  console.log('\n=====================================');
  console.log('📊 Diagnostic Summary:');
  console.log('=====================================\n');

  console.log('The issue appears to be that the Netlify function is falling back to mock data.');
  console.log('This typically happens when:');
  console.log('1. BACKEND_URL env var is not set in Netlify');
  console.log('2. Backend returns an error');
  console.log('3. Backend is missing OPENROUTER_API_KEY1');
  console.log('\nNext steps:');
  console.log('- Check Netlify function logs for specific errors');
  console.log('- Verify BACKEND_URL is set in Netlify environment');
  console.log('- Check if backend has OPENROUTER_API_KEY1 configured');
}

diagnoseIssue().catch(console.error);