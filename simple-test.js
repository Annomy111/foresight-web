const puppeteer = require('puppeteer');

async function testForesightAnalyzer() {
  console.log('🚀 Starting Foresight Analyzer walkthrough...');

  const browser = await puppeteer.launch({
    headless: false,
    slowMo: 1000,
    defaultViewport: { width: 1200, height: 800 }
  });

  const page = await browser.newPage();

  try {
    // Navigate to the app
    console.log('📍 Navigating to https://foresight-analyzer.netlify.app');
    await page.goto('https://foresight-analyzer.netlify.app', {
      waitUntil: 'networkidle2',
      timeout: 30000
    });

    // Wait for page to load
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Take screenshot of homepage
    await page.screenshot({ path: 'homepage.png', fullPage: true });
    console.log('📸 Homepage screenshot saved as homepage.png');

    // Check if the page loaded correctly
    const title = await page.title();
    console.log(`📄 Page title: ${title}`);

    // Look for main heading
    const heading = await page.$eval('h1', el => el.textContent).catch(() => 'Not found');
    console.log(`🏷️ Main heading: ${heading}`);

    // Look for the forecast question input
    const inputs = await page.$$('input, textarea');
    console.log(`📝 Found ${inputs.length} input fields`);

    if (inputs.length > 0) {
      // Fill the first input (question field)
      console.log('✍️ Filling forecast question...');
      await inputs[0].type('Will there be peace in Ukraine by the end of 2026?');
      await page.waitForTimeout(1000);

      // If there's a second input (definition), fill it
      if (inputs.length > 1) {
        console.log('✍️ Filling definition field...');
        await inputs[1].type('A formal ceasefire agreement signed by both parties');
        await new Promise(resolve => setTimeout(resolve, 1000));
      }

      // If there's a third input (timeframe), fill it
      if (inputs.length > 2) {
        console.log('✍️ Filling timeframe field...');
        await inputs[2].type('2026-12-31');
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }

    // Look for checkboxes (AI models)
    const checkboxes = await page.$$('input[type="checkbox"]');
    console.log(`☑️ Found ${checkboxes.length} model checkboxes`);

    if (checkboxes.length > 0) {
      // Select first few models
      console.log('✅ Selecting AI models...');
      for (let i = 0; i < Math.min(3, checkboxes.length); i++) {
        await checkboxes[i].click();
        await new Promise(resolve => setTimeout(resolve, 500));
      }
    }

    // Take screenshot after filling form
    await page.screenshot({ path: 'form-filled.png', fullPage: true });
    console.log('📸 Form filled screenshot saved as form-filled.png');

    // Look for submit button
    const submitButton = await page.$('button:has-text("Start Forecast"), button[type="submit"]');

    if (submitButton) {
      console.log('🔍 Found submit button, checking if enabled...');
      const isEnabled = await submitButton.evaluate(btn => !btn.disabled);
      console.log(`🔘 Submit button enabled: ${isEnabled}`);

      if (isEnabled) {
        console.log('🚀 Clicking submit button...');
        await submitButton.click();

        // Wait for any response/loading
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Take screenshot of result
        await page.screenshot({ path: 'after-submit.png', fullPage: true });
        console.log('📸 After submit screenshot saved as after-submit.png');

        // Check for any loading indicators or results
        const loadingElements = await page.$$('.loading, .spinner, [data-testid="loading"]');
        const resultElements = await page.$$('.result, .forecast, [data-testid="result"]');

        console.log(`⏳ Loading indicators found: ${loadingElements.length}`);
        console.log(`📊 Result elements found: ${resultElements.length}`);
      }
    } else {
      console.log('❌ No submit button found');
    }

    // Final analysis
    console.log('\n📋 Test Summary:');
    console.log(`✓ Page loaded: ${title !== ''}`);
    console.log(`✓ Main heading found: ${heading !== 'Not found'}`);
    console.log(`✓ Input fields found: ${inputs.length}`);
    console.log(`✓ Model checkboxes found: ${checkboxes.length}`);
    console.log(`✓ Submit button found: ${submitButton !== null}`);

    console.log('\n🎉 Walkthrough completed successfully!');
    console.log('📁 Screenshots saved: homepage.png, form-filled.png, after-submit.png');

    // Keep browser open for 5 seconds to see final state
    await new Promise(resolve => setTimeout(resolve, 5000));

  } catch (error) {
    console.error('❌ Error during walkthrough:', error.message);

    // Take error screenshot
    await page.screenshot({ path: 'error.png', fullPage: true });
    console.log('📸 Error screenshot saved as error.png');
  } finally {
    await browser.close();
  }
}

// Run the test
testForesightAnalyzer().catch(console.error);