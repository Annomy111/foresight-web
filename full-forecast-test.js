const puppeteer = require('puppeteer');

async function testFullForecast() {
  console.log('🚀 Testing complete forecast generation...');

  const browser = await puppeteer.launch({
    headless: false,
    slowMo: 1000,
    defaultViewport: { width: 1400, height: 900 }
  });

  const page = await browser.newPage();

  try {
    // Navigate to the app
    console.log('📍 Loading Foresight Analyzer...');
    await page.goto('https://foresight-analyzer.netlify.app', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Take initial screenshot
    await page.screenshot({ path: 'forecast-1-loaded.png', fullPage: true });
    console.log('📸 Initial page loaded');

    // Fill out the form completely
    console.log('✍️ Filling forecast question...');
    const questionInput = await page.$('input[type="text"], textarea');
    if (questionInput) {
      await questionInput.type('Will there be peace in Ukraine by the end of 2026?', { delay: 100 });
    }

    // Fill definition if available
    console.log('✍️ Filling definition...');
    const inputs = await page.$$('input, textarea');
    if (inputs.length > 1) {
      await inputs[1].type('A formal ceasefire agreement signed by both parties with international oversight', { delay: 50 });
    }

    // Fill timeframe if available
    if (inputs.length > 2) {
      await inputs[2].clear();
      await inputs[2].type('2026-12-31', { delay: 50 });
    }

    // Select some AI models
    console.log('✅ Selecting AI models...');
    const checkboxes = await page.$$('input[type="checkbox"]');
    console.log(`Found ${checkboxes.length} model checkboxes`);

    // Select first 3-4 models to speed up the test
    for (let i = 0; i < Math.min(4, checkboxes.length); i++) {
      await checkboxes[i].click();
      await new Promise(resolve => setTimeout(resolve, 300));
    }

    // Take screenshot before submitting
    await page.screenshot({ path: 'forecast-2-filled.png', fullPage: true });
    console.log('📸 Form filled out');

    // Find and click submit button
    console.log('🚀 Starting forecast...');
    const submitButton = await page.$('button:has-text("Start Forecast"), button[type="submit"]');

    if (!submitButton) {
      throw new Error('Submit button not found');
    }

    const isEnabled = await submitButton.evaluate(btn => !btn.disabled);
    console.log(`Submit button enabled: ${isEnabled}`);

    if (!isEnabled) {
      throw new Error('Submit button is disabled');
    }

    await submitButton.click();
    console.log('✅ Submit button clicked');

    // Wait for loading indicators or results
    console.log('⏳ Waiting for forecast to start...');
    await new Promise(resolve => setTimeout(resolve, 3000));

    // Take screenshot after submit
    await page.screenshot({ path: 'forecast-3-submitted.png', fullPage: true });
    console.log('📸 After submission');

    // Look for various possible result indicators
    console.log('🔍 Looking for forecast results...');

    let foundResults = false;
    let attempts = 0;
    const maxAttempts = 12; // Wait up to 2 minutes

    while (!foundResults && attempts < maxAttempts) {
      attempts++;
      console.log(`Attempt ${attempts}/${maxAttempts} - Looking for results...`);

      // Check for loading indicators
      const loadingElements = await page.$$('.loading, .spinner, [data-testid="loading"], text=Processing, text=Generating');
      if (loadingElements.length > 0) {
        console.log(`⏳ Found ${loadingElements.length} loading indicators`);
      }

      // Check for result elements
      const resultElements = await page.$$('.result, .forecast, [data-testid="result"], .probability, .percentage');
      if (resultElements.length > 0) {
        console.log(`📊 Found ${resultElements.length} result elements`);
        foundResults = true;
        break;
      }

      // Check for progress indicators
      const progressElements = await page.$$('.progress, [role="progressbar"], text=Progress');
      if (progressElements.length > 0) {
        console.log(`📈 Found ${progressElements.length} progress indicators`);
      }

      // Check for any text that might indicate results
      const pageText = await page.evaluate(() => document.body.textContent);
      if (pageText.includes('%') && (pageText.includes('probability') || pageText.includes('forecast') || pageText.includes('prediction'))) {
        console.log('📊 Found percentage results in page text');
        foundResults = true;
        break;
      }

      // Check for error messages
      if (pageText.includes('error') || pageText.includes('failed') || pageText.includes('Error')) {
        console.log('❌ Found error text on page');
        break;
      }

      // Wait before next attempt
      await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds

      // Take periodic screenshots
      if (attempts % 3 === 0) {
        await page.screenshot({ path: `forecast-progress-${attempts}.png`, fullPage: true });
        console.log(`📸 Progress screenshot ${attempts}`);
      }
    }

    // Final screenshot
    await page.screenshot({ path: 'forecast-final.png', fullPage: true });
    console.log('📸 Final state captured');

    // Analyze final results
    const finalText = await page.evaluate(() => document.body.textContent);

    console.log('\n📋 FORECAST TEST RESULTS:');
    console.log(`✓ Form filled and submitted: YES`);
    console.log(`✓ Waited for results: ${attempts * 10} seconds`);
    console.log(`✓ Found result indicators: ${foundResults ? 'YES' : 'NO'}`);

    if (foundResults) {
      console.log('🎉 SUCCESS: Forecast generation appears to be working!');
    } else {
      console.log('⚠️ No clear results found - may need longer wait time or different selectors');
    }

    // Look for specific result patterns
    const percentageMatches = finalText.match(/\d+\.?\d*%/g);
    if (percentageMatches) {
      console.log(`📊 Found percentages: ${percentageMatches.join(', ')}`);
    }

    console.log('\n📁 Screenshots saved:');
    console.log('- forecast-1-loaded.png (initial load)');
    console.log('- forecast-2-filled.png (form filled)');
    console.log('- forecast-3-submitted.png (after submit)');
    console.log('- forecast-final.png (final results)');

    // Keep browser open for manual inspection
    console.log('\n🔍 Keeping browser open for 10 seconds for manual inspection...');
    await new Promise(resolve => setTimeout(resolve, 10000));

  } catch (error) {
    console.error('❌ Error during forecast test:', error.message);
    await page.screenshot({ path: 'forecast-error.png', fullPage: true });
    console.log('📸 Error screenshot saved');
  } finally {
    await browser.close();
  }
}

testFullForecast().catch(console.error);