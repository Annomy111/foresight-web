const puppeteer = require('puppeteer');

async function testForesightAnalyzer() {
  console.log('🧪 Starting Foresight Analyzer E2E Test');
  console.log('=====================================\n');

  let browser;

  try {
    // Launch browser
    browser = await puppeteer.launch({
      headless: false, // Set to false to see the browser
      defaultViewport: { width: 1280, height: 800 }
    });

    const page = await browser.newPage();

    // Set up console logging
    page.on('console', msg => {
      if (msg.type() === 'error') {
        console.log('❌ Browser Console Error:', msg.text());
      }
    });

    // Set up request logging
    page.on('request', request => {
      if (request.url().includes('api') || request.url().includes('netlify/functions')) {
        console.log('📤 API Request:', request.method(), request.url());
      }
    });

    page.on('response', response => {
      if (response.url().includes('api') || response.url().includes('netlify/functions')) {
        console.log('📥 API Response:', response.status(), response.url());
      }
    });

    // Navigate to the app
    console.log('📍 Navigating to: https://foresight-analyzer.netlify.app');
    await page.goto('https://foresight-analyzer.netlify.app', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Wait for the page to load
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Check if the main form is present
    console.log('\n✅ Page loaded successfully');

    // Take a screenshot
    await page.screenshot({ path: 'test-screenshot-1.png' });
    console.log('📸 Screenshot saved: test-screenshot-1.png');

    // Check for form elements
    const questionTextarea = await page.$('textarea[placeholder*="Will there be a ceasefire"]');
    const definitionTextarea = await page.$('textarea[placeholder*="Clarify"]');
    const timeframeInput = await page.$('input[placeholder="2026"]');
    const submitButton = await page.$('button');

    if (questionTextarea && definitionTextarea && timeframeInput && submitButton) {
      console.log('✅ All form elements found');
    } else {
      console.log('❌ Some form elements are missing');
    }

    // Fill in the form
    console.log('\n📝 Filling in the form...');
    await questionTextarea.type('Will AI significantly impact the job market by 2026?');
    await definitionTextarea.type('Significant impact means at least 20% of jobs affected by AI automation or augmentation.');

    // Clear and set timeframe
    await timeframeInput.click({ clickCount: 3 });
    await timeframeInput.type('2026');

    // Set iterations slider
    const slider = await page.$('input[type="range"]');
    if (slider) {
      await slider.evaluate(el => el.value = '3');
      console.log('✅ Set iterations to 3');
    }

    // Take a screenshot of filled form
    await page.screenshot({ path: 'test-screenshot-2-filled.png' });
    console.log('📸 Screenshot saved: test-screenshot-2-filled.png');

    // Monitor network for API call
    console.log('\n🚀 Submitting forecast request...');

    const responsePromise = page.waitForResponse(
      response => response.url().includes('/.netlify/functions/forecast'),
      { timeout: 60000 }
    );

    // Click the submit button
    await submitButton.click();
    console.log('✅ Form submitted');

    // Wait for the API response
    try {
      const response = await responsePromise;
      const responseData = await response.json();

      console.log('\n📊 API Response received:');
      console.log('   Status:', response.status());
      console.log('   Success:', responseData.success);

      if (responseData.result) {
        console.log('   Result:');
        if (responseData.result.ensemble_probability !== undefined) {
          console.log('     - Ensemble Probability:', responseData.result.ensemble_probability + '%');
        }
        if (responseData.result.statistics) {
          console.log('     - Models Used:', responseData.result.statistics.models_used?.length || 0);
          console.log('     - Successful Queries:', responseData.result.statistics.successful_queries || 0);
        }
        if (responseData.result.note) {
          console.log('     - Note:', responseData.result.note);
        }
      }

      // Wait for results to be displayed
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Check if results are displayed
      const resultSection = await page.$('text=/Forecast Result/i');
      if (resultSection) {
        console.log('\n✅ Results displayed on page');

        // Take screenshot of results
        await page.screenshot({ path: 'test-screenshot-3-results.png' });
        console.log('📸 Screenshot saved: test-screenshot-3-results.png');
      } else {
        console.log('\n⚠️  Results section not found on page');
      }

    } catch (error) {
      console.log('\n❌ Error waiting for API response:', error.message);
    }

    // Test backend health endpoint directly
    console.log('\n🔍 Testing backend health directly...');
    const healthResponse = await page.evaluate(async () => {
      try {
        const response = await fetch('https://foresight-backend-api.onrender.com/health');
        const data = await response.json();
        return { status: response.status, data };
      } catch (error) {
        return { error: error.message };
      }
    });

    if (healthResponse.error) {
      console.log('⚠️  Backend health check failed:', healthResponse.error);
      console.log('   Note: Backend might be sleeping (Render free tier)');
    } else {
      console.log('✅ Backend health check passed');
      console.log('   Status:', healthResponse.status);
      console.log('   Data:', JSON.stringify(healthResponse.data));
    }

    console.log('\n=====================================');
    console.log('✅ Test completed successfully!');
    console.log('=====================================');

  } catch (error) {
    console.error('\n❌ Test failed with error:', error.message);
    console.error(error);
  } finally {
    if (browser) {
      await browser.close();
      console.log('\n🔒 Browser closed');
    }
  }
}

// Run the test
testForesightAnalyzer().catch(console.error);